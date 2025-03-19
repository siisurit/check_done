# Copyright (C) 2024-2025 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
from check_done.info import GithubProjectItemType
from check_done.warning_checks import (
    sentence_from_project_item_warning_reasons,
    warning_reason_if_missing_closing_issue_reference_in_pull_request,
    warning_reason_if_missing_milestone,
    warning_reason_if_open,
    warning_reason_if_tasks_are_uncompleted,
    warning_reason_if_unassigned,
    warnings_for_done_project_items,
)
from tests._common import new_fake_project_item_info


def test_can_resolve_warnings_for_done_project_items():
    fake_done_project_items = [
        new_fake_project_item_info(closed=False),
        new_fake_project_item_info(assignees_count=0, closing_issues_references=[]),
        new_fake_project_item_info(has_no_milestone=True, assignees_count=0, closing_issues_references=[]),
    ]
    fake_warnings = warnings_for_done_project_items(fake_done_project_items)

    not_closed_warning = fake_warnings[0]
    assert "should be closed." in not_closed_warning

    not_assigned_and_pull_request_is_missing_closing_issue_reference_warning = fake_warnings[1]
    assert (
        "should be assigned and have a closing issue reference."
        in not_assigned_and_pull_request_is_missing_closing_issue_reference_warning
    )

    not_assigned_and_missing_milestone_and_pull_request_is_missing_closing_issue_reference_warning = fake_warnings[2]
    assert (
        "should be assigned, have a milestone, and have a closing issue reference."
        in not_assigned_and_missing_milestone_and_pull_request_is_missing_closing_issue_reference_warning
    )


def test_warnings_for_done_project_items_with_empty_list_of_done_project_items():
    empty_fake_warnings = warnings_for_done_project_items([])
    assert len(empty_fake_warnings) == 0


def test_can_compose_sentence_from_project_item_warning_reasons():
    project_item_with_one_warning_reason = new_fake_project_item_info(closing_issues_references=[])
    single_warning_reason_string = sentence_from_project_item_warning_reasons(
        project_item_with_one_warning_reason, ["have a closing issue reference"]
    )
    assert "Project item should have a closing issue reference." in single_warning_reason_string

    project_item_with_two_warning_reasons = new_fake_project_item_info(assignees_count=0, closing_issues_references=[])
    double_warning_reason_string = sentence_from_project_item_warning_reasons(
        project_item_with_two_warning_reasons, ["be assigned", "have a closing issue reference"]
    )
    assert "be assigned and have a closing issue reference." in double_warning_reason_string

    project_item_with_three_warning_reasons = new_fake_project_item_info(
        has_no_milestone=True, assignees_count=0, milestone=None, closing_issues_references=[]
    )
    triple_warning_reason_string = sentence_from_project_item_warning_reasons(
        project_item_with_three_warning_reasons,
        ["be assigned", "have a milestone", "have a closing issue reference"],
    )
    assert "be assigned, have a milestone, and have a closing issue reference." in triple_warning_reason_string


def test_can_return_warning_reason_if_project_item_is_open():
    open_project_item = new_fake_project_item_info(closed=False)
    assert warning_reason_if_open(open_project_item) is not None

    closed_project_item = new_fake_project_item_info(closed=True)
    assert warning_reason_if_open(closed_project_item) is None


def test_can_return_warning_reason_if_project_item_is_unassigned():
    unassigned_project_item = new_fake_project_item_info(assignees_count=0)
    assert warning_reason_if_unassigned(unassigned_project_item) is not None

    assigned_project_item = new_fake_project_item_info(assignees_count=1)
    assert warning_reason_if_unassigned(assigned_project_item) is None


def test_can_return_warning_reason_if_project_item_is_missing_milestone():
    project_item_with_missing_milestone = new_fake_project_item_info(has_no_milestone=True)
    assert warning_reason_if_missing_milestone(project_item_with_missing_milestone) is not None

    project_item_with_milestone = new_fake_project_item_info(has_no_milestone=False)
    assert warning_reason_if_missing_milestone(project_item_with_milestone) is None


def test_can_return_warning_reason_if_project_item_has_uncompleted_tasks():
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

    project_item_with_uncompleted_task = new_fake_project_item_info(body_html=html_with_an_uncompleted_task)
    assert warning_reason_if_tasks_are_uncompleted(project_item_with_uncompleted_task) is not None

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
    project_item_with_completed_tasks = new_fake_project_item_info(body_html=html_with_completed_tasks)
    assert warning_reason_if_tasks_are_uncompleted(project_item_with_completed_tasks) is None

    project_item_with_empty_html_body = new_fake_project_item_info()
    assert warning_reason_if_tasks_are_uncompleted(project_item_with_empty_html_body) is None


def test_can_return_warning_reason_if_project_item_is_missing_closing_issue_reference_in_pul_request():
    pull_request_with_missing_closing_issue_reference = new_fake_project_item_info(closing_issues_references=[])
    assert (
        warning_reason_if_missing_closing_issue_reference_in_pull_request(
            pull_request_with_missing_closing_issue_reference
        )
        is not None
    )

    issue_is_missing_closed_by_pull_request_reference = new_fake_project_item_info(
        typename=GithubProjectItemType.issue, closing_issues_references=[]
    )
    assert (
        warning_reason_if_missing_closing_issue_reference_in_pull_request(
            issue_is_missing_closed_by_pull_request_reference
        )
        is None
    )

    pull_request_with_closing_issue_reference = new_fake_project_item_info()
    assert (
        warning_reason_if_missing_closing_issue_reference_in_pull_request(pull_request_with_closing_issue_reference)
        is None
    )
