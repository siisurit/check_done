# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
from check_done.info import GithubProjectItemType
from check_done.warning_checks import (
    sentence_from_project_item_warning_reasons,
    warning_if_missing_linked_issue_in_pull_request,
    warning_if_missing_milestone,
    warning_if_open,
    warning_if_tasks_are_uncompleted,
    warning_if_unassigned,
    warnings_for_done_project_items,
)
from tests._common import mock_project_item_info


def test_can_get_warnings_for_done_project_items():
    mock_done_project_items = [
        mock_project_item_info(closed=False),
        mock_project_item_info(assignees_count=0, linked_project_items=[]),
        mock_project_item_info(has_no_milestone=True, assignees_count=0, linked_project_items=[]),
    ]
    mocked_warnings = warnings_for_done_project_items(mock_done_project_items)
    assert "should be closed." in mocked_warnings[0]
    assert "should be assigned and have a linked issue." in mocked_warnings[1]
    assert "should be assigned, have a milestone, and have a linked issue." in mocked_warnings[2]


def test_can_get_empty_warnings_for_done_project_items():
    empty_done_project_items_list = []
    empty_mocked_warnings = warnings_for_done_project_items(empty_done_project_items_list)
    assert len(empty_mocked_warnings) == 0


def test_can_compose_sentence_from_project_item_warning_reasons():
    project_item_with_one_warnings = mock_project_item_info(linked_project_items=[])
    project_item_with_two_warnings = mock_project_item_info(assignees_count=0, linked_project_items=[])
    project_item_with_three_warnings = mock_project_item_info(
        has_no_milestone=True, assignees_count=0, milestone=None, linked_project_items=[]
    )
    single_warning_reason_string = sentence_from_project_item_warning_reasons(
        project_item_with_one_warnings, warnings_for_done_project_items([project_item_with_one_warnings])
    )
    double_warning_reason_string = sentence_from_project_item_warning_reasons(
        project_item_with_two_warnings, warnings_for_done_project_items([project_item_with_two_warnings])
    )
    triple_warning_reason_string = sentence_from_project_item_warning_reasons(
        project_item_with_three_warnings,
        warnings_for_done_project_items([project_item_with_three_warnings]),
    )
    assert "Project item should have a linked issue." in single_warning_reason_string
    assert "be assigned and have a linked issue." in double_warning_reason_string
    assert "be assigned, have a milestone, and have a linked issue." in triple_warning_reason_string


def test_can_warn_if_project_item_is_open():
    open_project_item = mock_project_item_info(closed=False)
    closed_project_item = mock_project_item_info(closed=True)
    assert warning_if_open(open_project_item) is not None
    assert warning_if_open(closed_project_item) is None


def test_can_warn_if_unassigned():
    unassigned_project_item = mock_project_item_info(assignees_count=0)
    assigned_project_item = mock_project_item_info(assignees_count=1)
    assert warning_if_unassigned(unassigned_project_item) is not None
    assert warning_if_unassigned(assigned_project_item) is None


def test_can_warn_if_missing_milestone():
    project_item_with_missing_milestone = mock_project_item_info(has_no_milestone=True)
    project_item_with_milestone = mock_project_item_info(has_no_milestone=False)
    assert warning_if_missing_milestone(project_item_with_missing_milestone) is not None
    assert warning_if_missing_milestone(project_item_with_milestone) is None


def test_can_warn_if_tasks_are_uncompleted():
    html_with_an_uncompleted_task = """
    <h2 dir="auto">Goals</h2>
    <ul class="contains-task-list">
        <li class="task-list-item">
            <input type="checkbox" id="" disabled="" class="task-list-item-checkbox"> Test 1.
        </li>
        <li class="task-list-item">
            <input type="checkbox" id="" disabled="" class="task-list-item-checkbox" checked=""> Test. 2
        </li>
    </ul>
    """
    project_item_with_uncompleted_task = mock_project_item_info(body_html=html_with_an_uncompleted_task)
    html_with_completed_tasks = """
    <h2 dir="auto">Goals</h2>
    <ul class="contains-task-list">
        <li class="task-list-item">
            <input type="checkbox" id="" disabled="" class="task-list-item-checkbox" checked=""> Test 1.
        </li>
        <li class="task-list-item">
            <input type="checkbox" id="" disabled="" class="task-list-item-checkbox" checked=""> Test. 2
        </li>
    </ul>
    """
    project_item_with_completed_tasks = mock_project_item_info(body_html=html_with_completed_tasks)
    project_item_with_empty_html_body = mock_project_item_info()
    assert warning_if_tasks_are_uncompleted(project_item_with_uncompleted_task) is not None
    assert warning_if_tasks_are_uncompleted(project_item_with_completed_tasks) is None
    assert warning_if_tasks_are_uncompleted(project_item_with_empty_html_body) is None


def test_can_warn_if_missing_linked_issue_in_pull_request():
    pull_request_is_missing_linked_issue = mock_project_item_info(linked_project_items=[])
    issue_is_missing_linked_pull_request = mock_project_item_info(
        typename=GithubProjectItemType.issue, linked_project_items=[]
    )
    pull_request_with_linked_issue = mock_project_item_info()
    assert warning_if_missing_linked_issue_in_pull_request(pull_request_is_missing_linked_issue) is not None
    assert warning_if_missing_linked_issue_in_pull_request(issue_is_missing_linked_pull_request) is None
    assert warning_if_missing_linked_issue_in_pull_request(pull_request_with_linked_issue) is None
