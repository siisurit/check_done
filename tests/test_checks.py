from check_done.checks import has_unfinished_goals
from check_done.done_project_items_info.info import (
    AssigneesInfo,
    LinkedProjectItemInfo,
    MilestoneInfo,
    ProjectItemInfo,
    RepositoryInfo,
)


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
    project_item_with_unfinished_goals = ProjectItemInfo(
        assignees=AssigneesInfo(totalCount=1),
        bodyHTML=html_with_an_unfinished_goals,
        closed=True,
        number=1,
        repository=RepositoryInfo(name="test_repo"),
        milestone=MilestoneInfo(id="1"),
        title="Test",
        linked_project_item=LinkedProjectItemInfo(nodes=[]),
    )
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
    project_item_with_finished_goals = ProjectItemInfo(
        assignees=AssigneesInfo(totalCount=1),
        bodyHTML=html_with_an_finished_goals,
        closed=True,
        number=1,
        repository=RepositoryInfo(name="test_repo"),
        milestone=MilestoneInfo(id="1"),
        title="Test",
        linked_project_item=LinkedProjectItemInfo(nodes=[]),
    )
    empty_html_body = ""
    project_item_with_empty_html_body = ProjectItemInfo(
        assignees=AssigneesInfo(totalCount=1),
        bodyHTML=empty_html_body,
        closed=True,
        number=1,
        repository=RepositoryInfo(name="test_repo"),
        milestone=MilestoneInfo(id="1"),
        title="Test",
        linked_project_item=LinkedProjectItemInfo(nodes=[]),
    )

    assert has_unfinished_goals(project_item_with_unfinished_goals) is True
    assert has_unfinished_goals(project_item_with_finished_goals) is False
    assert has_unfinished_goals(project_item_with_empty_html_body) is False
