import re

import pytest

from check_done.command import check_done_command
from check_done.common import configuration_info
from tests._common import (
    HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)

_HAS_CHECK_DONE_DEMO_PROJECT_CONFIGURED = (
    configuration_info().project_owner_name == "siisurit" and configuration_info().project_number == 2
)

_REASON_SHOULD_HAVE_CHECK_DONE_DEMO_PROJECT_CONFIGURED = (
    "To enable for development, setup the configuration for the check done demo project."
)


def test_can_show_help():
    with pytest.raises(SystemExit) as error_info:
        check_done_command(["--help"])
    assert error_info.value.code == 0


def test_can_show_version():
    with pytest.raises(SystemExit) as error_info:
        check_done_command(["--version"])
    assert error_info.value.code == 0


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_can_execute_check_done_warnings(caplog):
    is_exit_code_ok = check_done_command([]) == 0
    has_check_done_warning_messages = len(caplog.messages) >= 1
    assert is_exit_code_ok
    assert has_check_done_warning_messages


@pytest.mark.skipif(
    not _HAS_CHECK_DONE_DEMO_PROJECT_CONFIGURED,
    reason=_REASON_SHOULD_HAVE_CHECK_DONE_DEMO_PROJECT_CONFIGURED,
)
def test_can_check_done_demo_project(caplog):
    is_exit_code_ok = check_done_command([]) == 0
    has_check_done_warning_messages = len(caplog.messages) >= 1
    expected_warning_about_missing_assignee = r"(?=.*missing assignee)(?=.*#3 Warning: Closed issue without assignee)"
    warning_about_missing_assignee = caplog.messages[0]
    expected_warning_about_open_issue_with_dene_state = r"(?=.*not closed)(?=.*#4 Warning: Open issue with Done state)"
    warning_about_open_issue_with_dene_state = caplog.messages[1]
    expected_warning_about_missing_milestone = (
        r"(?=.*missing milestone)(?=.*#11 Warning: Project item without milestone)"
    )
    warning_about_missing_milestone = caplog.messages[2]
    expected_warning_about_unfinished_goals = (
        r"(?=.*missing finished goals)(?=.*#8 Warning: project item with unfinished goals)"
    )
    warning_about_unfinished_goals = caplog.messages[3]
    expected_warning_about_pull_request_with_missing_linked_issue = (
        r"(?=.*missing linked issue)(?=.*#6 Warning: Pull request is missing linked issue)"
    )
    warning_about_pull_request_with_missing_linked_issue = caplog.messages[4]
    expected_warning_about_open_pull_request_with_done_state = (
        r"(?=.*not closed)(?=.*#7 Warning: Open pull request with Done state)"
    )
    warning_about_open_pull_request_with_done_state = caplog.messages[5]
    ok_project_item_titles = [
        "#2 Ok: Closed issue without PR",
        "#10 Ok: Properly closed issue with Done state",
        "#12 Ok: Project item with finished goals",
        "#5 Ok: Pull Request has linked issue",
    ]

    assert is_exit_code_ok
    assert has_check_done_warning_messages
    assert re.search(expected_warning_about_missing_assignee, warning_about_missing_assignee)
    assert re.search(expected_warning_about_open_issue_with_dene_state, warning_about_open_issue_with_dene_state)
    assert re.search(expected_warning_about_missing_milestone, warning_about_missing_milestone)
    assert re.search(expected_warning_about_unfinished_goals, warning_about_unfinished_goals)
    assert re.search(
        expected_warning_about_pull_request_with_missing_linked_issue,
        warning_about_pull_request_with_missing_linked_issue,
    )
    assert re.search(
        expected_warning_about_open_pull_request_with_done_state,
        warning_about_open_pull_request_with_done_state,
    )
    assert not any(
        ok_project_item_title in warning_message
        for ok_project_item_title in ok_project_item_titles
        for warning_message in caplog.messages
    )
