# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from requests import HTTPError, Response

from check_done.graphql import (
    GraphQlError,
    checked_graphql_data_map,
    get_query_info_from_response_info,
    minimized_graphql,
)
from check_done.info import (
    PageInfo,
    QueryInfo,
)


@pytest.mark.parametrize(
    "input_query, expected_output",
    [
        # Basic whitespace removal
        ("{ user(id: 1) { name age } }", "{user(id:1){name age}}"),
        # Test 2: Multiple spaces and around symbols
        ("{    user   (  id:    1   )   {   name,   age   }   }", "{user(id:1){name,age}}"),
        # Empty string
        ("", ""),
        # Already minimized string
        ("{user(id:1){name,age}}", "{user(id:1){name,age}}"),
        # Test 5: Newlines and tabs
        ("{\n  user (id: 1) {\n\tname\n\tage\n  }\n}", "{user(id:1){name age}}"),
        # Complex query with variables and fragments
        (
            """
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
                    """,
            "query getUser($id:ID!){user(id:$id){...userFields}}fragment userFields on User{name age email}",
        ),
    ],
    ids=[
        "basic_whitespace_removal",
        "whitespace_around_symbols",
        "empty_string",
        "already_minimized",
        "newlines_and_tabs",
        "complex_query_with_fragments",
    ],
)
def test_minimized_graphql(input_query, expected_output):
    assert minimized_graphql(input_query) == expected_output


def _mock_response(json_data=None, status_code=200, raise_for_status=None):
    mock_resp = Mock(spec=Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    else:
        mock_resp.raise_for_status = Mock()
    return mock_resp


def test_can_check_graphql_data_map():
    mock_resp = _mock_response(json_data={"data": {"key": "value"}})
    result = checked_graphql_data_map(mock_resp)
    assert result == {"key": "value"}


def test_fails_to_check_graphql_data_map_on_http_error():
    mock_resp = _mock_response(raise_for_status=HTTPError("HTTP error"))
    with pytest.raises(GraphQlError, match="HTTP error"):
        checked_graphql_data_map(mock_resp)


def test_fails_to_check_graphql_data_map_on_invalid_json_format():
    mock_resp = _mock_response(json_data=["not", "a", "dict"])
    with pytest.raises(GraphQlError, match="GraphQL response must be a map"):
        checked_graphql_data_map(mock_resp)


def test_fails_to_check_graphql_data_map_on_graphql_errors():
    mock_resp = _mock_response(json_data={"errors": [{"message": "Some GraphQL error"}]})
    with pytest.raises(GraphQlError, match="Some GraphQL error"):
        checked_graphql_data_map(mock_resp)


def test_fails_to_check_graphql_data_map_on_missing_data():
    mock_resp = _mock_response(json_data={"something_else": "value"})
    with pytest.raises(GraphQlError, match="GraphQL result must include data"):
        checked_graphql_data_map(mock_resp)


def test_fails_to_check_graphql_data_map_on_invalid_data_format():
    mock_resp = _mock_response(json_data={"data": ["not", "a", "dict"]})
    with pytest.raises(GraphQlError, match="GraphQL data must be a map"):
        checked_graphql_data_map(mock_resp)


class _MockedInfo(BaseModel):
    id: int


def test_can_get_nodes_info_from_response_info():
    mocked_node_info = QueryInfo(nodes=[], pageInfo=PageInfo(endCursor="a", hasNextPage=True))
    result = get_query_info_from_response_info(mocked_node_info)
    assert isinstance(result, QueryInfo)


def test_fails_to_get_nodes_info_from_node_with_no_matching_node_info_type():
    mocked_model = _MockedInfo(id=1)
    with pytest.raises(ValueError, match="Could not find fields matching the "):
        get_query_info_from_response_info(mocked_model)
