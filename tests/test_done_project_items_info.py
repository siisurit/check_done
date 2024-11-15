# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.

import pytest

from check_done.config import configuration_info
from check_done.done_project_items_info import (
    PROJECT_NUMBER,
    done_project_items_info,
    filtered_project_item_infos_by_done_status,
    matching_project_id,
    matching_project_state_option_id,
)
from check_done.info import (
    ProjectV2Node,
    ProjectV2Options,
    ProjectV2SingleSelectFieldNode,
)
from tests._common import mock_project_v2_item_node

_HAS_PROJECT_STATUS_NAME_TO_CHECK = configuration_info().project_status_name_to_check is not None
_REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION = (
    "To enable, configure the `project_status_name_to_check` field as described in the readme."
)


def test_can_get_done_project_items_info():
    assert len(done_project_items_info()) >= 1


def test_can_find_matching_project_id_from_node_infos():
    _matching_project_id = "b2"
    _another_project_number = 256
    _mock_project_id_node_infos = [
        ProjectV2Node(id="a1", number=_another_project_number, __typename="ProjectV2"),
        ProjectV2Node(id=_matching_project_id, number=PROJECT_NUMBER, __typename="ProjectV2"),
    ]

    _project_id = matching_project_id(_mock_project_id_node_infos)
    assert _project_id == _matching_project_id


def test_fails_to_find_matching_project_id_from_node_infos():
    _another_project_number = 256
    _mock_project_id_node_infos = [
        ProjectV2Node(id="a1", number=_another_project_number, __typename="ProjectV2"),
    ]
    with pytest.raises(ValueError, match=f"Cannot find a project with number '{PROJECT_NUMBER}'"):
        matching_project_id(_mock_project_id_node_infos)


def test_can_find_matching_project_state_option_id_from_name():
    _mock_matching_project_state_option_id = "2b"
    _mock_matching_project_state_option_name = "Finished"
    _mock_last_project_state_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(
                    id=_mock_matching_project_state_option_id, name=_mock_matching_project_state_option_name
                ),
            ],
        )
    ]
    _matching_project_state_option_id = matching_project_state_option_id(
        _mock_last_project_state_option_id_node_infos, _mock_matching_project_state_option_name
    )
    assert _matching_project_state_option_id == _mock_matching_project_state_option_id


@pytest.mark.skipif(
    not _HAS_PROJECT_STATUS_NAME_TO_CHECK,
    reason=_REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_fails_to_find_matching_project_state_option_id_from_name():
    _wrongly_assumed_matching_project_state_option_name = "Fake"
    _actual_matching_project_state_option_name = configuration_info().project_status_name_to_check
    _mock_last_project_state_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(id="2b", name=_actual_matching_project_state_option_name),
            ],
        )
    ]
    with pytest.raises(
        ValueError,
        match=f"Cannot find the project status matching name '{_actual_matching_project_state_option_name}' ",
    ):
        _matching_project_state_option_id = matching_project_state_option_id(
            _mock_last_project_state_option_id_node_infos, _wrongly_assumed_matching_project_state_option_name
        )


def test_can_find_matching_last_project_state_option_id():
    _mock_matching_last_project_state_option_id = "2b"
    _mock_last_project_state_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(id=_mock_matching_last_project_state_option_id, name="Finished"),
            ],
        )
    ]
    _matching_last_project_state_option_id = matching_project_state_option_id(
        _mock_last_project_state_option_id_node_infos, None
    )
    assert _matching_last_project_state_option_id == _mock_matching_last_project_state_option_id


def test_fails_to_find_matching_last_project_state_option_id():
    _mock_last_project_state_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(id="a1", name="Milestone", __typename="ProjectV2SingleSelectField", options=[])
    ]
    with pytest.raises(ValueError, match="Cannot find a project status selection field "):
        _matching_last_project_state_option_id = matching_project_state_option_id(
            _mock_last_project_state_option_id_node_infos, None
        )


def test_can_get_filtered_project_item_infos_with_done_status():
    _in_progress_project_status_id = "a1"
    _done_project_status_id = "b2"
    _mocked_done_issues_node_infos = [
        mock_project_v2_item_node(option_id=_in_progress_project_status_id, closed=True),
        mock_project_v2_item_node(option_id=_in_progress_project_status_id, closed=False),
        mock_project_v2_item_node(option_id=_done_project_status_id, closed=True),
        mock_project_v2_item_node(option_id=_done_project_status_id, closed=False),
    ]
    _done_issue_infos = filtered_project_item_infos_by_done_status(
        _mocked_done_issues_node_infos, _done_project_status_id
    )
    assert len(_done_issue_infos) == 2


def test_fails_to_find_any_filtered_project_item_infos_by_done_status(caplog):
    _matching_project_id = "a1"
    _other_project_id = "b2"
    _mocked_done_issues_node_infos = [mock_project_v2_item_node(option_id=_other_project_id)]

    _done_issue_infos = filtered_project_item_infos_by_done_status(_mocked_done_issues_node_infos, _matching_project_id)
    assert len(_done_issue_infos) < 1

    expected_log_warning = "No project items found for the specified project status in the GitHub project "
    assert expected_log_warning in caplog.text
