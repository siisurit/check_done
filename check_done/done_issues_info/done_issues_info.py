import logging
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from requests import HTTPError, Response

from check_done.authentication import github_app_access_token
from check_done.common import (
    HttpBearerAuth,
    config_info,
    github_organization_name_and_project_number_from_url_if_matches,
)

_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
_BOARD_URL = config_info().board.url
_ORGANIZATION_NAME, _PROJECT_NUMBER = github_organization_name_and_project_number_from_url_if_matches(_BOARD_URL)
_ACCESS_TOKEN = github_app_access_token(_ORGANIZATION_NAME)
_PATH_TO_QUERIES = Path(__file__).parent.parent / "done_issues_info" / "queries"
_MAX_PROJECT_V2_ENTRIES_PER_PAGE = 100
logger = logging.getLogger(__name__)


# TODO#15: Add return value
def done_issues_info():
    _session = requests.Session()
    _session.headers = {"Accept": "application/vnd.github+json"}
    _session.auth = HttpBearerAuth(_ACCESS_TOKEN)
    _variables = {"login": _ORGANIZATION_NAME, "maxProjectV2EntriesPerPage": _MAX_PROJECT_V2_ENTRIES_PER_PAGE}

    def project_id() -> str:
        query_name = _GraphQlQuery.PROJECT_ID.name
        query = _GraphQlQuery.query_for(query_name)
        json_payload_map = {
            "variables": _variables,
            "query": query,
        }
        response = _session.post(_GRAPHQL_ENDPOINT, json=json_payload_map, headers=_session.headers)
        project_data = _checked_graphql_data_map(response)
        project_nodes = project_data["organization"]["projectsV2"]["nodes"]
        try:
            result_project_id = next(
                str(project_node["id"])
                for project_node in project_nodes
                if int(project_node["number"]) == _PROJECT_NUMBER
            )
        except StopIteration:
            raise ValueError(
                f"Cannot find in the GitHub organization a project with number: {_PROJECT_NUMBER}"
            ) from None
        return result_project_id

    project_id = project_id()
    logger.info(project_id)

    # TODO#15: Implement
    # def query_project_done_issues():
    #     variables = {"project_id.graphql": project_id}
    #     headers = {"Authorization": f"Bearer {_ACCESS_TOKEN}", "Accept": "application/vnd.github+json"}
    #     query_name = _GraphQlQuery.CLOSED_ISSUES_FROM_PROJECT_BOARD.name
    #     query = _GraphQlQuery.query_for(query_name)
    #     response = _session.post(_GRAPHQL_ENDPOINT, json={"query": query, "variables": variables}, headers=headers)
    #     return response.json()
    #
    # result = query_project_done_issues()
    # print(result)


@lru_cache
def _minimized_graphql(graphql_query: str) -> str:
    single_spaced_query = re.sub(r"\s+", " ", graphql_query)
    formatted_query = re.sub(r"\s*([{}()\[\]:,])\s*", r"\1", single_spaced_query)
    result = formatted_query.strip()
    return result


def _graphql_query(item_name: str) -> str:
    query_path = _PATH_TO_QUERIES / f"{item_name}.graphql"
    with query_path.open(encoding="utf-8") as query_file:
        query_text = query_file.read()
    return _minimized_graphql(query_text)


class _GraphQlQuery(Enum):
    PROJECT_ID = _graphql_query("project_id")
    CLOSED_ISSUES_FROM_PROJECT_BOARD = _graphql_query("closed_issues_from_project_board")

    @staticmethod
    def query_for(name: str):
        assert name is not None
        assert name.upper() == name
        return _GraphQlQuery[name].value


def _checked_graphql_data_map(response: Response) -> dict[str, Any | None]:
    try:
        response.raise_for_status()
    except HTTPError as error:
        raise _GraphQlError(error) from error
    response_map = response.json()
    if not isinstance(response_map, dict):
        raise _GraphQlError(f"GraphQL response must be a map but is: {response_map}.")
    errors = response_map.get("errors")
    if errors is not None:
        raise _GraphQlError(f'{errors[0]["message"]}; details: {errors}.')
    result = response_map.get("data")
    if result is None:
        raise _GraphQlError(f"GraphQL result must include data but only has: {sorted(response_map.keys())}.")
    if not isinstance(result, dict):
        raise _GraphQlError(f"GraphQL data must be a map but is: {result}.")
    return result


class _GraphQlError(Exception):
    pass
