import logging
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel
from requests import HTTPError, Response, Session

from check_done.authentication import github_app_access_token
from check_done.common import (
    HttpBearerAuth,
    config_info,
    github_organization_name_and_project_number_from_url_if_matches,
)
from check_done.done_project_items_info.info import (
    GithubContentType,
    NodeByIdInfo,
    OrganizationInfo,
    PaginatedQueryInfo,
    ProjectItemInfo,
    ProjectV2ItemNodeInfo,
    ProjectV2NodeInfo,
    ProjectV2SingleSelectFieldNodeInfo,
)

_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
_PROJECT_BOARD_URL = config_info().project_board_url
ORGANIZATION_NAME, PROJECT_NUMBER = github_organization_name_and_project_number_from_url_if_matches(_PROJECT_BOARD_URL)
_ACCESS_TOKEN = github_app_access_token(ORGANIZATION_NAME)
_PATH_TO_QUERIES = Path(__file__).parent.parent / "done_project_items_info" / "queries"
_MAX_ENTRIES_PER_PAGE = 100
_GITHUB_PROJECT_STATUS_FIELD_NAME = "Status"
logger = logging.getLogger(__name__)


def done_project_items_info() -> list[ProjectItemInfo]:
    session = requests.Session()
    session.headers = {"Accept": "application/vnd.github+json"}
    session.auth = HttpBearerAuth(_ACCESS_TOKEN)

    projects_ids_nodes_info = _query_nodes_info(OrganizationInfo, _GraphQlQuery.PROJECTS_IDS.name, session)
    project_id = matching_project_id(projects_ids_nodes_info)

    last_project_state_option_ids_nodes_info = _query_nodes_info(
        NodeByIdInfo, _GraphQlQuery.PROJECT_STATE_OPTIONS_IDS.name, session, project_id
    )
    last_project_state_option_id = matching_last_project_state_option_id(last_project_state_option_ids_nodes_info)

    project_items_nodes_info = _query_nodes_info(
        NodeByIdInfo, _GraphQlQuery.PROJECT_V_2_ITEMS.name, session, project_id
    )
    result = filtered_project_item_infos_by_done_status(project_items_nodes_info, last_project_state_option_id)
    return result


def matching_project_id(node_infos: list[ProjectV2NodeInfo]) -> str:
    try:
        return next(str(project_node.id) for project_node in node_infos if project_node.number == PROJECT_NUMBER)
    except StopIteration as error:
        raise ValueError(
            f"Cannot find a project with number '{PROJECT_NUMBER}', in the GitHub organization '{ORGANIZATION_NAME}'."
        ) from error


def matching_last_project_state_option_id(node_infos: list[ProjectV2SingleSelectFieldNodeInfo]) -> str:
    try:
        return next(
            # TODO: Ponder giving the user the option to pick which project state option instead of picking
            #  the last one.
            #  Take into consideration that the GraphQL query allows for filtering the status options by name,
            #  which is interesting when there are emoji's in the name like in the case of Siisurit...
            #  To help with that, if the script can't find the name the user gave, a list of the options can be
            #  shown to them.
            project_state_node.options[-1].id
            for project_state_node in node_infos
            if project_state_node.name is not None and project_state_node.name == _GITHUB_PROJECT_STATUS_FIELD_NAME
        )
    except StopIteration as error:
        raise ValueError(
            f"Cannot find the project status selection field in the GitHub project with number `{PROJECT_NUMBER}` "
            f"on the `{ORGANIZATION_NAME}` organization."
        ) from error


def filtered_project_item_infos_by_done_status(
    node_infos: list[ProjectV2ItemNodeInfo], last_project_state_option_id: str
) -> list[ProjectItemInfo]:
    result = []
    for node in node_infos:
        has_last_project_state_option = node.field_value_by_name.option_id == last_project_state_option_id
        assert node.type == GithubContentType.ISSUE or GithubContentType.PULL_REQUEST
        if has_last_project_state_option:
            result.append(node.content)
    if len(result) < 1:
        logger.warning(
            f"No project items found with the last project status option selected in the GitHub project with number "
            f"`{PROJECT_NUMBER}` in organization '{ORGANIZATION_NAME}'"
        )
    return result


@lru_cache
def minimized_graphql(graphql_query: str) -> str:
    single_spaced_query = re.sub(r"\s+", " ", graphql_query)
    formatted_query = re.sub(r"\s*([{}()\[\]:,])\s*", r"\1", single_spaced_query)
    result = formatted_query.strip()
    return result


def _graphql_query(item_name: str) -> str:
    query_path = _PATH_TO_QUERIES / f"{item_name}.graphql"
    with query_path.open(encoding="utf-8") as query_file:
        query_text = query_file.read()
    return minimized_graphql(query_text)


class _GraphQlQuery(Enum):
    PROJECTS_IDS = _graphql_query("projects_ids")
    PROJECT_STATE_OPTIONS_IDS = _graphql_query("project_state_options_ids")
    PROJECT_V_2_ITEMS = _graphql_query("project_v2_items")

    @staticmethod
    def query_for(name: str):
        assert name is not None
        assert name.upper() == name
        return _GraphQlQuery[name].value


def _query_nodes_info(
    base_model: type[BaseModel], query_name: str, session: Session, project_id: str | None = None
) -> list:
    result = []
    variables = {"login": ORGANIZATION_NAME, "maxEntriesPerPage": _MAX_ENTRIES_PER_PAGE}
    if project_id is not None:
        variables["projectId"] = project_id
    after = None
    has_more_pages = True
    while has_more_pages:
        query = _GraphQlQuery.query_for(query_name)
        if after is not None:
            variables["after"] = after
        json_payload_map = {
            "variables": variables,
            "query": query,
        }
        response = session.post(_GRAPHQL_ENDPOINT, json=json_payload_map)
        response_map = checked_graphql_data_map(response)
        response_info = base_model(**response_map)
        paginated_query_info = get_paginated_query_info_from_response_info(response_info)
        nodes_info = paginated_query_info.nodes
        page_info = paginated_query_info.page_info
        after = page_info.endCursor
        has_more_pages = page_info.hasNextPage
        result.extend(nodes_info)
    return result


def get_paginated_query_info_from_response_info(base_model: BaseModel) -> PaginatedQueryInfo:
    if isinstance(base_model, PaginatedQueryInfo):
        return base_model
    for model in base_model.__fields_set__:
        field_value = getattr(base_model, model)
        if isinstance(field_value, BaseModel):
            page_info = get_paginated_query_info_from_response_info(field_value)
            if page_info is not None:
                return page_info
    raise ValueError(f"Could not find nodes info in {base_model}.")


def checked_graphql_data_map(response: Response) -> dict[str, Any | None]:
    try:
        response.raise_for_status()
    except HTTPError as error:
        raise GraphQlError(error) from error
    response_map = response.json()
    if not isinstance(response_map, dict):
        raise GraphQlError(f"GraphQL response must be a map but is: {response_map}.")
    errors = response_map.get("errors")
    if errors is not None:
        raise GraphQlError(f'{errors[0]["message"]}; details: {errors}.')
    result = response_map.get("data")
    if result is None:
        raise GraphQlError(f"GraphQL result must include data but only has: {sorted(response_map.keys())}.")
    if not isinstance(result, dict):
        raise GraphQlError(f"GraphQL data must be a map but is: {result}.")
    return result


class GraphQlError(Exception):
    pass
