# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from requests import HTTPError, Response, Session
from requests.auth import AuthBase

from check_done.info import (
    QueryInfo,
)

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
_MAX_ENTRIES_PER_PAGE = 100
_PATH_TO_QUERIES = Path(__file__).parent / "queries"


class GraphQlError(Exception):
    pass


class HttpBearerAuth(AuthBase):
    # Source:
    # <https://stackoverflow.com/questions/29931671/making-an-api-call-in-python-with-an-api-that-requires-a-bearer-token>
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers["Authorization"] = "Bearer " + self.token
        return request


@lru_cache
def minimized_graphql(graphql_query: str) -> str:
    single_spaced_query = re.sub(r"\s+", " ", graphql_query)
    formatted_query = re.sub(r"\s*([{}()\[\]:,])\s*", r"\1", single_spaced_query)
    result = formatted_query.strip()
    if result == "":
        raise GraphQlError("GraphQL query is empty.")
    return result


def _graphql_query(item_name: str) -> str:
    query_path = _PATH_TO_QUERIES / f"{item_name}.graphql"
    with query_path.open(encoding="utf-8") as query_file:
        query_text = query_file.read()
    return minimized_graphql(query_text)


class GraphQlQuery(Enum):
    ORGANIZATION_PROJECTS = _graphql_query("organization_projects")
    USER_PROJECTS = _graphql_query("user_projects")
    PROJECT_SINGLE_SELECT_FIELDS = _graphql_query("project_single_select_fields")
    PROJECT_V2_ITEMS = _graphql_query("project_v2_items")

    @staticmethod
    def query_for(name: str):
        assert name is not None
        assert name.upper() == name
        return GraphQlQuery[name].value


def query_infos(
    base_model: type[BaseModel],
    query_name: str,
    session: Session,
    project_owner_name: str,
    project_id: str | None = None,
) -> list:
    result = []
    variables = {"login": project_owner_name, "maxEntriesPerPage": _MAX_ENTRIES_PER_PAGE}
    if project_id is not None:
        variables["projectId"] = project_id
    after = None
    has_more_pages = True
    while has_more_pages:
        query = GraphQlQuery.query_for(query_name)
        if after is not None:
            variables["after"] = after
        json_payload_map = {
            "variables": variables,
            "query": query,
        }
        response = session.post(GRAPHQL_ENDPOINT, json=json_payload_map)
        response_map = checked_graphql_data_map(response)
        response_info = base_model(**response_map)
        query_info = query_info_from_response_info(response_info)
        nodes_info = query_info.nodes
        page_info = query_info.page_info
        after = page_info.endCursor
        has_more_pages = page_info.hasNextPage
        result.extend(nodes_info)
    return result


def query_info_from_response_info(base_model: BaseModel) -> QueryInfo:
    if isinstance(base_model, QueryInfo):
        return base_model
    for model_field_name in base_model.model_fields_set:
        field_model = getattr(base_model, model_field_name)
        if isinstance(field_model, BaseModel):
            result = query_info_from_response_info(field_model)
            if result is not None:
                return result
    raise ValueError(
        f"Could not find fields matching the {QueryInfo.__name__} model with fields "
        f"`{QueryInfo.model_fields.keys()}` in: {base_model}"
    )


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
