# Copyright (C) 2024-2025 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
import requests_mock
from pydantic import BaseModel
from requests import HTTPError, Response

from check_done.graphql import (
    GRAPHQL_ENDPOINT,
    GraphQlError,
    GraphQlQuery,
    checked_graphql_data_map,
    minimized_graphql,
    query_info_from_response_info,
    query_infos,
)
from check_done.info import (
    PageInfo,
    ProjectOwnerInfo,
    ProjectV2Node,
    QueryInfo,
)


class _FakeModelWithQueryInfoField(BaseModel):
    query_info: QueryInfo


class _FakeModelContainingQueryInfoModel(BaseModel):
    another_dummy_mode: _FakeModelWithQueryInfoField


class _FakeModelInfo(BaseModel):
    id: int


def test_can_minimize_graphql_with_simple_white_space():
    input_query = "{ user(id: 1) { name age } }"
    expected_output = "{user(id:1){name age}}"
    assert minimized_graphql(input_query) == expected_output


def test_can_minimize_graphql_with_multiple_spaces_around_symbols():
    input_query = "{    user   (  id:    1   )   {   name,   age   }   }"
    expected_output = "{user(id:1){name,age}}"
    assert minimized_graphql(input_query) == expected_output


def test_can_minimize_graphql_with_already_minimal_string():
    input_query = "{user(id:1){name,age}}"
    expected_output = "{user(id:1){name,age}}"
    assert minimized_graphql(input_query) == expected_output


def test_can_minimize_graphql_with_newlines_and_tabs():
    input_query = "{\n  user (id: 1) {\n\tname\n\tage\n  }\n}"
    expected_output = "{user(id:1){name age}}"
    assert minimized_graphql(input_query) == expected_output


def test_can_minimize_complex_graphql_query_with_fragments_and_variables():
    input_query = """
                query getUser($id: ID!) {
                  user(id: $id) {
                    ...userFields
                  }
                }
                fragment userFields on User {
                  name
                  age
                  email
                }
                """
    expected_output = "query getUser($id:ID!){user(id:$id){...userFields}}fragment userFields on User{name age email}"
    assert minimized_graphql(input_query) == expected_output


def test_fails_to_minimize_empty_graphql_query():
    with pytest.raises(GraphQlError, match="GraphQL query is empty."):
        minimized_graphql("")


def test_can_check_graphql_data_map():
    mock_response = _mock_response(json_data={"data": {"key": "value"}})
    result = checked_graphql_data_map(mock_response)
    assert result == {"key": "value"}


def test_fails_to_check_graphql_data_map_on_http_error():
    mock_response = _mock_response(raise_for_status=HTTPError("HTTP error"))
    with pytest.raises(GraphQlError, match="HTTP error"):
        checked_graphql_data_map(mock_response)


def test_fails_to_check_graphql_data_map_on_invalid_json_format():
    mock_response = _mock_response(json_data=["not", "a", "dict"])
    with pytest.raises(GraphQlError, match="GraphQL response must be a map"):
        checked_graphql_data_map(mock_response)


def test_fails_to_check_graphql_data_map_on_graphql_errors():
    mock_response = _mock_response(json_data={"errors": [{"message": "Some GraphQL error"}]})
    with pytest.raises(GraphQlError, match="Some GraphQL error"):
        checked_graphql_data_map(mock_response)


def test_fails_to_check_graphql_data_map_on_missing_data():
    mock_response = _mock_response(json_data={"something_else": "value"})
    with pytest.raises(GraphQlError, match="GraphQL result must include data"):
        checked_graphql_data_map(mock_response)


def test_fails_to_check_graphql_data_map_on_invalid_data_format():
    mock_response = _mock_response(json_data={"data": ["not", "a", "dict"]})
    with pytest.raises(GraphQlError, match="GraphQL data must be a map"):
        checked_graphql_data_map(mock_response)


def test_can_resolve_query_info_from_response_info():
    fake_query_info = QueryInfo(nodes=[], pageInfo=PageInfo(endCursor="a", hasNextPage=True))
    query_info = query_info_from_response_info(fake_query_info)
    assert query_info.nodes == fake_query_info.nodes
    assert query_info.page_info.endCursor == fake_query_info.page_info.endCursor
    assert query_info.page_info.hasNextPage
    assert isinstance(query_info, QueryInfo)


def test_can_resolve_nested_query_info_from_response_info():
    fake_query_info = QueryInfo(nodes=[], pageInfo=PageInfo(endCursor="a", hasNextPage=True))
    fake_nested_query_info = _FakeModelContainingQueryInfoModel(
        another_dummy_mode=_FakeModelWithQueryInfoField(query_info=fake_query_info)
    )
    query_info = query_info_from_response_info(fake_nested_query_info)
    assert query_info.nodes == fake_query_info.nodes
    assert query_info.page_info.endCursor == fake_query_info.page_info.endCursor
    assert query_info.page_info.hasNextPage
    assert isinstance(query_info, QueryInfo)


def test_fails_to_resolve_query_info_from_response_info_with_no_query_info():
    fake_model = _FakeModelInfo(id=1)
    with pytest.raises(ValueError, match="Could not find fields matching the "):
        query_info_from_response_info(fake_model)


def test_can_resolve_mocked_single_page_query_infos():
    mocked_result = _mocked_query_infos_from_json_files(["test_can_resolve_single_page_query_infos"])
    assert len(mocked_result) == 1
    assert isinstance(mocked_result[0], ProjectV2Node)


def test_can_resolve_multi_page_query_infos():
    mocked_result = _mocked_query_infos_from_json_files(
        ["test_can_resolve_multi_page_query_infos_page_1", "test_can_resolve_multi_page_query_infos_page_2"]
    )
    assert len(mocked_result) > 1
    assert isinstance(mocked_result[0], ProjectV2Node)
    assert isinstance(mocked_result[1], ProjectV2Node)


def _mocked_query_infos_from_json_files(json_files_base_name: list[str]) -> list:
    test_data_base_folder = Path(__file__).parent / "data" / "test_can_query_mocked_query_infos"
    with requests_mock.Mocker() as mock:
        response_list = []
        for json_file_base_name in json_files_base_name:
            json_mock_path = test_data_base_folder / (json_file_base_name + ".json")
            with json_mock_path.open() as json_mock_info_file:
                json_mock_data = json.load(json_mock_info_file)
                response_list.append({"json": json_mock_data})
        mock.post(GRAPHQL_ENDPOINT, response_list=response_list)
        dummy_session = requests.Session()
        result = query_infos(
            ProjectOwnerInfo, GraphQlQuery.USER_PROJECTS.name, dummy_session, "dummy_project_owner_name"
        )
    return result


def _mock_response(json_data=None, status_code=200, raise_for_status=None):
    mock_response = Mock(spec=Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    if raise_for_status:
        mock_response.raise_for_status.side_effect = raise_for_status
    else:
        mock_response.raise_for_status = Mock()
    return mock_response
