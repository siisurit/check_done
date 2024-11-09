import logging
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel
from requests import HTTPError, Response, Session

from check_done.common import (
    HttpBearerAuth,
    configuration_info,
)
from check_done.info import (
    IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION,
    PROJECT_NUMBER,
    PROJECT_OWNER_NAME,
    NodeByIdInfo,
    PaginatedQueryInfo,
    ProjectItemInfo,
    ProjectOwnerInfo,
    ProjectV2ItemNodeInfo,
    ProjectV2NodeInfo,
    ProjectV2SingleSelectFieldNodeInfo,
)
from check_done.organization_authentication import access_token_from_organization

_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
_PROJECT_STATUS_NAME_TO_CHECK = configuration_info().project_status_name_to_check
_PERSONAL_ACCESS_TOKEN = configuration_info().personal_access_token
_ORGANIZATION_ACCESS_TOKEN = (
    access_token_from_organization(PROJECT_OWNER_NAME) if IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION else None
)
_ACCESS_TOKEN = _ORGANIZATION_ACCESS_TOKEN or _PERSONAL_ACCESS_TOKEN
_PATH_TO_QUERIES = Path(__file__).parent / "queries"
_MAX_ENTRIES_PER_PAGE = 100
_GITHUB_PROJECT_STATUS_FIELD_NAME = "Status"
logger = logging.getLogger(__name__)


def done_project_items_info() -> list[ProjectItemInfo]:
    session = requests.Session()
    session.headers = {"Accept": "application/vnd.github+json"}
    session.auth = HttpBearerAuth(_ACCESS_TOKEN)

    projects_ids_query_name = (
        _GraphQlQuery.ORGANIZATION_PROJECTS_IDS.name
        if IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION
        else _GraphQlQuery.USER_PROJECTS_IDS.name
    )
    projects_ids_nodes_info = _query_nodes_info(ProjectOwnerInfo, projects_ids_query_name, session)
    project_id = matching_project_id(projects_ids_nodes_info)

    last_project_state_option_ids_nodes_info = _query_nodes_info(
        NodeByIdInfo, _GraphQlQuery.PROJECT_STATE_OPTIONS_IDS.name, session, project_id
    )
    last_project_state_option_id = matching_project_state_option_id(
        last_project_state_option_ids_nodes_info, _PROJECT_STATUS_NAME_TO_CHECK
    )

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
            f"Cannot find a project with number '{PROJECT_NUMBER}', owned by '{PROJECT_OWNER_NAME}'."
        ) from error


def matching_project_state_option_id(
    node_infos: list[ProjectV2SingleSelectFieldNodeInfo], project_status_name_to_check: str | None
) -> str:
    if project_status_name_to_check is not None:
        try:
            result = next(
                option.id
                for project_state_node in node_infos
                for option in project_state_node.options
                if project_status_name_to_check in option.name
            )
        except StopIteration as error:
            status_options_names = [
                option.name for project_state_node in node_infos for option in project_state_node.options
            ]
            raise ValueError(
                f"Cannot find the project status matching name '{_PROJECT_STATUS_NAME_TO_CHECK}' "
                f"in the GitHub project with number `{PROJECT_NUMBER}` owned by `{PROJECT_OWNER_NAME}`. "
                f"Available options are: {status_options_names}"
            ) from error
    else:
        try:
            result = next(
                project_state_node.options[-1].id
                for project_state_node in node_infos
                if project_state_node.name is not None and project_state_node.name == _GITHUB_PROJECT_STATUS_FIELD_NAME
            )
        except StopIteration as error:
            raise ValueError(
                f"Cannot find a project status selection field in the GitHub project with number `{PROJECT_NUMBER}` "
                f"owned by `{PROJECT_OWNER_NAME}`."
            ) from error
    return result


def filtered_project_item_infos_by_done_status(
    node_infos: list[ProjectV2ItemNodeInfo], last_project_state_option_id: str
) -> list[ProjectItemInfo]:
    result = []
    for node in node_infos:
        has_last_project_state_option = (
            node.field_value_by_name is not None and node.field_value_by_name.option_id == last_project_state_option_id
        )
        if has_last_project_state_option:
            result.append(node.content)
    if len(result) < 1:
        logger.warning(
            f"No project items found with the last project status option selected in the GitHub project with number "
            f"`{PROJECT_NUMBER}` owned by '{PROJECT_OWNER_NAME}'"
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
    ORGANIZATION_PROJECTS_IDS = _graphql_query("organization_projects_ids")
    USER_PROJECTS_IDS = _graphql_query("user_projects_ids")
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
    variables = {"login": PROJECT_OWNER_NAME, "maxEntriesPerPage": _MAX_ENTRIES_PER_PAGE}
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
