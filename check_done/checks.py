from html.parser import HTMLParser

from check_done.info import GithubProjectItemType, ProjectItemInfo


# TODO#13 Naming: CQS -> warnings_from_checked_project_items
def check_done_project_items_for_warnings(done_project_items: list[ProjectItemInfo]) -> list[str | None]:
    result = []
    for project_item in done_project_items:
        warning_reasons = [
            warning_reason
            for is_valid, warning_reason in CONDITION_CHECK_AND_WARNING_REASON_LIST
            if is_valid(project_item)
        ]
        if len(warning_reasons) >= 1:
            warning = project_item_warning_string(project_item, warning_reasons)
            result.append(warning)
    return result


def project_item_warning_string(issue: ProjectItemInfo, reasons_for_warning: list[str]) -> str:
    if len(reasons_for_warning) >= 3:
        reasons_for_warning = f"{', '.join(reasons_for_warning[:-1])}, and {reasons_for_warning[-1]}"
    elif len(reasons_for_warning) == 2:
        reasons_for_warning = f"{', '.join(reasons_for_warning[:1])} and is {reasons_for_warning[1]}"
    else:
        reasons_for_warning = reasons_for_warning[0]
    return (
        f" Done project item is {reasons_for_warning}."
        f" - repository: '{issue.repository.name}', project item: '#{issue.number} {issue.title}'."
    )


def is_not_closed(project_item: ProjectItemInfo) -> bool:
    return not project_item.closed


def possible_should_be_closed_warning(project_item: ProjectItemInfo) -> str | None:
    return "should be closed" if not project_item.closed else None


# TODO#13 Change other checks to warning functions.


def is_not_assigned(project_item: ProjectItemInfo) -> bool:
    return project_item.assignees.total_count == 0


def has_no_milestone(project_item: ProjectItemInfo) -> bool:
    return project_item.milestone is None


def has_unfinished_goals(project_item: ProjectItemInfo) -> bool:
    parser = _AllTasksCheckedHtmlParser()
    parser.feed(project_item.body_html)
    return parser.has_unfinished_goals()


class _AllTasksCheckedHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.all_tasks_are_checked = True

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            attr_dict = dict(attrs)
            is_checkbox = attr_dict.get("type") == "checkbox"
            if is_checkbox:
                is_checked = "checked" in attr_dict
                if not is_checked:
                    self.all_tasks_are_checked = False
                    # TODO Optimize: If any task is unchecked, stop parsing.

    def has_unfinished_goals(self):  # TODO#13 Possibly remove
        return not self.all_tasks_are_checked


def is_missing_linked_issue_in_pull_request(project_item: ProjectItemInfo) -> bool:
    result = False
    if project_item.typename is GithubProjectItemType.pull_request:
        result = len(project_item.linked_project_item.nodes) == 0
    return result


CONDITION_CHECK_AND_WARNING_REASON_LIST = [  # TODO#13 Clean up: Remove, rename, or change to map.
    (is_not_closed, "not closed"),
    (is_not_assigned, "missing assignee"),
    (has_no_milestone, "missing milestone"),
    (has_unfinished_goals, "missing finished goals"),
    (is_missing_linked_issue_in_pull_request, "missing linked issue"),
]

POSSIBLE_WARNINGS = [possible_should_be_closed_warning]  # TODO#13 Add other warning functions.
