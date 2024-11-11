from check_done.checks import (
    CONDITION_CHECK_AND_WARNING_REASON_LIST,
    check_done_project_items_for_warnings,
    has_no_milestone,
    has_unfinished_goals,
    is_missing_linked_issue_in_pull_request,
    is_not_assigned,
    is_not_closed,
    project_item_warning_string,
)
from tests._common import mock_project_item_info

# TODO#13 Clean up "is False/True".


def test_can_check_done_project_items_for_warnings():
    mock_done_project_items = [
        mock_project_item_info(assignees_count=0, linked_project_items=[]),
        mock_project_item_info(linked_project_items=[]),
    ]
    mocked_warnings = check_done_project_items_for_warnings(mock_done_project_items)
    assert "missing assignee and is missing linked issue." in mocked_warnings[0]
    assert "missing linked issue." in mocked_warnings[1]


def test_can_check_empty_done_project_items_list_for_warnings():
    empty_done_project_items_list = []
    empty_mocked_warnings = check_done_project_items_for_warnings(empty_done_project_items_list)
    assert len(empty_mocked_warnings) == 0


def test_can_compose_project_item_warning_string():
    project_item_with_one_warnings = mock_project_item_info(linked_project_items=[])
    project_item_with_two_warnings = mock_project_item_info(assignees_count=0, linked_project_items=[])
    project_item_with_three_warnings = mock_project_item_info(
        assignees_count=0, milestone=None, linked_project_items=[]
    )
    _, warning_for_missing_linked_project = CONDITION_CHECK_AND_WARNING_REASON_LIST[4]
    _, warning_for_missing_assignee = CONDITION_CHECK_AND_WARNING_REASON_LIST[1]
    _, warning_for_missing_milestone = CONDITION_CHECK_AND_WARNING_REASON_LIST[2]
    single_warning_reason_string = project_item_warning_string(
        project_item_with_one_warnings, [warning_for_missing_linked_project]
    )
    double_warning_reason_string = project_item_warning_string(
        project_item_with_two_warnings, [warning_for_missing_linked_project, warning_for_missing_assignee]
    )
    triple_warning_reason_string = project_item_warning_string(
        project_item_with_three_warnings,
        [warning_for_missing_linked_project, warning_for_missing_assignee, warning_for_missing_milestone],
    )
    assert "is missing linked issue." in single_warning_reason_string
    assert "is missing linked issue and is missing assignee." in double_warning_reason_string
    assert "is missing linked issue, missing assignee, and missing milestone" in triple_warning_reason_string


def test_can_check_if_project_item_is_not_closed():
    not_closed_project_item = mock_project_item_info(closed=False)
    closed_project_item = mock_project_item_info(closed=True)
    assert is_not_closed(not_closed_project_item) is True
    assert is_not_closed(closed_project_item) is False


def test_can_check_if_project_item_is_is_not_assigned():
    not_assigned_project_item = mock_project_item_info(assignees_count=0)
    assigned_project_item = mock_project_item_info(assignees_count=1)
    assert is_not_assigned(not_assigned_project_item) is True
    assert is_not_assigned(assigned_project_item) is False


def test_can_check_if_project_item_has_no_milestone():
    project_item_without_milestone = mock_project_item_info(has_no_milestone=True)
    project_item_with_milestone = mock_project_item_info(has_no_milestone=False)
    assert has_no_milestone(project_item_without_milestone) is True
    assert has_no_milestone(project_item_with_milestone) is False


def test_can_check_for_unfinished_goals():
    html_with_an_unfinished_goals = """
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
    project_item_with_unfinished_goals = mock_project_item_info(body_html=html_with_an_unfinished_goals)
    html_with_an_finished_goals = """
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
    project_item_with_finished_goals = mock_project_item_info(body_html=html_with_an_finished_goals)
    project_item_with_empty_html_body = mock_project_item_info()
    assert has_unfinished_goals(project_item_with_unfinished_goals)
    assert not has_unfinished_goals(project_item_with_finished_goals)
    assert has_unfinished_goals(project_item_with_empty_html_body) is False


def test_can_check_if_project_item_is_missing_linked_project_item():
    project_item_is_missing_linked_project_items = mock_project_item_info(linked_project_items=[])
    has_linked_project_items = mock_project_item_info()
    assert is_missing_linked_issue_in_pull_request(project_item_is_missing_linked_project_items) is True
    assert is_missing_linked_issue_in_pull_request(has_linked_project_items) is False
