from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from requests import HTTPError, Response

from check_done.done_project_items_info.done_project_items_info import (
    PROJECT_NUMBER,
    GraphQlError,
    checked_graphql_data_map,
    done_project_items_info,
    filtered_project_item_infos_by_done_status,
    get_paginated_query_info_from_response_info,
    matching_last_project_state_option_id,
    matching_project_id,
    minimized_graphql,
)
from check_done.done_project_items_info.info import (
    GithubContentType,
    PageInfo,
    PaginatedQueryInfo,
    ProjectItemInfo,
    ProjectV2ItemNodeInfo,
    ProjectV2ItemProjectStatusInfo,
    ProjectV2NodeInfo,
    ProjectV2Options,
    ProjectV2SingleSelectFieldNodeInfo,
    RepositoryInfo,
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
    mocked_node_info = PaginatedQueryInfo(nodes=[], pageInfo=PageInfo(endCursor="a", hasNextPage=True))
    result = get_paginated_query_info_from_response_info(mocked_node_info)
    assert isinstance(result, PaginatedQueryInfo)


def test_fails_to_get_nodes_info_from_node_with_no_matching_node_info_type():
    mocked_model = _MockedInfo(id=1)
    with pytest.raises(ValueError, match="Could not find nodes info in id=1."):
        get_paginated_query_info_from_response_info(mocked_model)


def test_can_get_done_project_items_info():
    assert len(done_project_items_info()) >= 1


def test_can_find_matching_project_id_from_node_infos():
    _matching_project_id = "b2"
    _mock_project_id_node_infos = [
        ProjectV2NodeInfo(id="a1", number=1, __typename="ProjectV2"),
        ProjectV2NodeInfo(id=_matching_project_id, number=PROJECT_NUMBER, __typename="ProjectV2"),
    ]

    _project_id = matching_project_id(_mock_project_id_node_infos)
    assert _project_id == _matching_project_id


def test_fails_to_find_matching_project_id_from_node_infos():
    _mock_project_id_node_infos = [
        ProjectV2NodeInfo(id="a1", number=1, __typename="ProjectV2"),
    ]
    with pytest.raises(ValueError, match=f"Cannot find a project with number '{PROJECT_NUMBER}'"):
        matching_project_id(_mock_project_id_node_infos)


def test_can_find_matching_last_project_state_option_id():
    _mock_matching_last_project_state_option_id = "2b"
    _mock_last_project_state_option_id_node_infos = [
        ProjectV2SingleSelectFieldNodeInfo(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(id=_mock_matching_last_project_state_option_id, name="Finished"),
            ],
        )
    ]
    _matching_last_project_state_option_id = matching_last_project_state_option_id(
        _mock_last_project_state_option_id_node_infos
    )
    assert _matching_last_project_state_option_id == _mock_matching_last_project_state_option_id


def test_fails_to_find_matching_last_project_state_option_id():
    _mock_last_project_state_option_id_node_infos = [
        ProjectV2SingleSelectFieldNodeInfo(
            id="a1", name="Milestone", __typename="ProjectV2SingleSelectField", options=[]
        )
    ]
    with pytest.raises(ValueError, match="Cannot find the project status selection field "):
        _matching_last_project_state_option_id = matching_last_project_state_option_id(
            _mock_last_project_state_option_id_node_infos
        )


def test_can_get_filtered_project_item_infos_by_done_status():
    _in_progress_project_status_id = "a1"
    _done_project_status_id = "b2"
    _mocked_done_issues_node_infos = [
        ProjectV2ItemNodeInfo(
            type=GithubContentType.ISSUE,
            content=ProjectItemInfo(
                number=1,
                closed=False,
                title="Do something",
                repository=RepositoryInfo(name="my_repo"),
            ),
            fieldValueByName=ProjectV2ItemProjectStatusInfo(
                status="In Progress", optionId=_in_progress_project_status_id
            ),
        ),
        ProjectV2ItemNodeInfo(
            type=GithubContentType.ISSUE,
            content=ProjectItemInfo(
                number=2,
                closed=True,
                title="Do something else",
                repository=RepositoryInfo(name="my_repo"),
            ),
            fieldValueByName=ProjectV2ItemProjectStatusInfo(status="Done", optionId=_done_project_status_id),
        ),
        ProjectV2ItemNodeInfo(
            type=GithubContentType.PULL_REQUEST,
            content=ProjectItemInfo(
                number=3,
                closed=False,
                title="#1 Do something",
                repository=RepositoryInfo(name="my_repo"),
            ),
            fieldValueByName=ProjectV2ItemProjectStatusInfo(
                status="In Progress", optionId=_in_progress_project_status_id
            ),
        ),
        ProjectV2ItemNodeInfo(
            type=GithubContentType.PULL_REQUEST,
            content=ProjectItemInfo(
                number=4,
                closed=True,
                title="#2 Do something else",
                repository=RepositoryInfo(name="my_repo"),
            ),
            fieldValueByName=ProjectV2ItemProjectStatusInfo(status="Done", optionId=_done_project_status_id),
        ),
    ]
    _done_issue_infos = filtered_project_item_infos_by_done_status(
        _mocked_done_issues_node_infos, _done_project_status_id
    )
    assert len(_done_issue_infos) == 2


def test_fails_to_find_any_filtered_project_item_infos_by_done_status(caplog):
    _matching_project_id = "a1"
    _other_project_id = "b2"
    _mocked_done_issues_node_infos = [
        ProjectV2ItemNodeInfo(
            type=GithubContentType.ISSUE,
            content=ProjectItemInfo(
                number=1,
                closed=False,
                title="Do something",
                repository=RepositoryInfo(name="my_repo"),
            ),
            fieldValueByName=ProjectV2ItemProjectStatusInfo(status="In Progress", optionId=_other_project_id),
        )
    ]

    _done_issue_infos = filtered_project_item_infos_by_done_status(_mocked_done_issues_node_infos, _matching_project_id)
    assert len(_done_issue_infos) < 1

    expected_log_warning = "No project items found with the last project status option selected "
    assert expected_log_warning in caplog.text
