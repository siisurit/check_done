# Copyright (C) 2024-2025 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import os

import pytest

from check_done.config import ConfigurationInfo
from check_done.done_project_items_info import (
    done_project_items_info,
    filtered_project_item_infos_by_done_status,
    matching_project_id,
    matching_project_status_option_id,
)
from check_done.info import (
    ProjectV2Node,
    ProjectV2Options,
    ProjectV2SingleSelectFieldNode,
)
from tests._common import (
    DEMO_CHECK_DONE_GITHUB_APP_ID,
    DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY,
    DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK,
    DEMO_CHECK_DONE_GITHUB_PROJECT_URL,
    ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK,
    HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    new_fake_project_v2_item_node,
)

_HAS_PROJECT_STATUS_NAME_TO_CHECK = DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK is not None
_REASON_SHOULD_HAVE_SET_ENV_PROJECT_STATUS_NAME_TO_CHECK = (
    f"To enable, set {ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK}."
)
_ENVVAR_DEMO_CHECK_DONE_PERSONAL_ACCESS_TOKEN = "CHECK_DONE_PERSONAL_ACCESS_TOKEN"
_DEMO_CHECK_DONE_PERSONAL_ACCESS_TOKEN = os.environ.get(_ENVVAR_DEMO_CHECK_DONE_PERSONAL_ACCESS_TOKEN)
_ENVVAR_DEMO_CHECK_DONE_USER_GITHUB_PROJECT_URL = "CHECK_DONE_USER_GITHUB_PROJECT_URL"
_DEMO_CHECK_DONE_USER_GITHUB_PROJECT_URL = os.environ.get(_ENVVAR_DEMO_CHECK_DONE_USER_GITHUB_PROJECT_URL)
_REASON_SHOULD_HAVE_USER_PROJECT_CONFIGURED = (
    f"To enable, set the environment variable {_ENVVAR_DEMO_CHECK_DONE_PERSONAL_ACCESS_TOKEN}, "
    f"and {_ENVVAR_DEMO_CHECK_DONE_USER_GITHUB_PROJECT_URL} to a user owned project URL."
)


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_resolve_done_project_items_info():
    fake_configuration_info = ConfigurationInfo(
        project_url=DEMO_CHECK_DONE_GITHUB_PROJECT_URL,
        github_app_id=DEMO_CHECK_DONE_GITHUB_APP_ID,
        github_app_private_key=DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY,
    )
    assert len(done_project_items_info(fake_configuration_info)) >= 1


@pytest.mark.skipif(
    not _DEMO_CHECK_DONE_USER_GITHUB_PROJECT_URL and not _DEMO_CHECK_DONE_PERSONAL_ACCESS_TOKEN,
    reason=_REASON_SHOULD_HAVE_USER_PROJECT_CONFIGURED,
)
def test_can_resolve_done_project_items_info_for_user_project():
    fake_configuration_info = ConfigurationInfo(
        project_url=_DEMO_CHECK_DONE_USER_GITHUB_PROJECT_URL,
        personal_access_token=_DEMO_CHECK_DONE_PERSONAL_ACCESS_TOKEN,
    )
    assert len(done_project_items_info(fake_configuration_info)) >= 1


def test_can_find_matching_project_id():
    expected_to_match_project_id = "b2"
    project_number = 1
    another_project_number = 256
    fake_project_id_node_infos = [
        ProjectV2Node(id="a1", number=another_project_number, __typename="ProjectV2"),
        ProjectV2Node(id=expected_to_match_project_id, number=project_number, __typename="ProjectV2"),
    ]

    matched_project_id = matching_project_id(
        fake_project_id_node_infos, project_number=project_number, project_owner_name="dummy_project_owner_name"
    )
    assert matched_project_id == expected_to_match_project_id


def test_fails_to_find_matching_project_id():
    project_number = 1
    another_project_number = 256
    fake_project_id_node_infos = [
        ProjectV2Node(id="a1", number=another_project_number, __typename="ProjectV2"),
    ]
    with pytest.raises(ValueError, match="Cannot find a project with number "):
        matching_project_id(fake_project_id_node_infos, project_number, "dummy_project_owner_name")


def test_can_find_matching_project_status_option_id():
    expected_to_math_project_status_option_id = "2b"
    fake_matching_project_status_option_name = "Finished"
    fake_last_project_status_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(
                    id=expected_to_math_project_status_option_id, name=fake_matching_project_status_option_name
                ),
            ],
        )
    ]
    matched_project_status_option_id = matching_project_status_option_id(
        fake_last_project_status_option_id_node_infos,
        fake_matching_project_status_option_name,
        1,
        "dummy_project_owner_name",
    )
    assert matched_project_status_option_id == expected_to_math_project_status_option_id


@pytest.mark.skipif(
    not _HAS_PROJECT_STATUS_NAME_TO_CHECK,
    reason=_REASON_SHOULD_HAVE_SET_ENV_PROJECT_STATUS_NAME_TO_CHECK,
)
def test_fails_to_find_matching_project_status_option_id():
    wrongly_assumed_matching_project_status_option_name = "Backlog"
    fake_last_project_status_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(id="2b", name=DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK),
            ],
        )
    ]
    with pytest.raises(
        ValueError,
        match=f"Cannot find the project status matching name '{wrongly_assumed_matching_project_status_option_name}' ",
    ):
        matching_project_status_option_id(
            fake_last_project_status_option_id_node_infos,
            wrongly_assumed_matching_project_status_option_name,
            1,
            "dummy_project_owner_name",
        )


def test_can_find_matching_last_project_status_option_id():
    expected_to_match_project_status_option_id = "2b"
    fake_last_project_status_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(
            id="a1",
            name="Status",
            __typename="ProjectV2SingleSelectField",
            options=[
                ProjectV2Options(id="1a", name="In Progress"),
                ProjectV2Options(id=expected_to_match_project_status_option_id, name="Finished"),
            ],
        )
    ]
    matching_last_project_status_option_id = matching_project_status_option_id(
        fake_last_project_status_option_id_node_infos,
        None,
        1,
        "dummy_project_owner_name",
    )
    assert matching_last_project_status_option_id == expected_to_match_project_status_option_id


def test_fails_to_find_matching_last_project_status_option_id():
    fake_last_project_status_option_id_node_infos = [
        ProjectV2SingleSelectFieldNode(id="a1", name="Milestone", __typename="ProjectV2SingleSelectField", options=[])
    ]
    with pytest.raises(ValueError, match="Cannot find a project status selection field "):
        matching_project_status_option_id(
            fake_last_project_status_option_id_node_infos,
            None,
            1,
            "dummy_project_owner_name",
        )


def test_can_resolve_filtered_project_item_infos_by_done_status():
    in_progress_project_status_id = "a1"
    done_project_status_id = "b2"
    fake_done_issues_node_infos = [
        new_fake_project_v2_item_node(option_id=in_progress_project_status_id, closed=True),
        new_fake_project_v2_item_node(option_id=in_progress_project_status_id, closed=False),
        new_fake_project_v2_item_node(option_id=done_project_status_id, closed=True),
        new_fake_project_v2_item_node(option_id=done_project_status_id, closed=False),
    ]
    done_issue_infos = filtered_project_item_infos_by_done_status(fake_done_issues_node_infos, done_project_status_id)
    assert len(done_issue_infos) == 2
