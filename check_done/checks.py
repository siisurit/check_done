from html.parser import HTMLParser

from check_done.info import GithubProjectItemType, ProjectItemInfo


def check_done_project_items_for_warnings(done_project_items: list[ProjectItemInfo]) -> list[str | None]:
    result = []
    for project_item in done_project_items:
        warning_reasons = [
            warning_reason for check, warning_reason in CONDITION_CHECK_AND_WARNING_REASON_LIST if check(project_item)
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


def is_not_assigned(project_item: ProjectItemInfo) -> bool:
    return project_item.assignees.total_count == 0


def has_no_milestone(project_item: ProjectItemInfo) -> bool:
    return project_item.milestone is None


def has_unfinished_goals(project_item: ProjectItemInfo) -> bool:
    class _GoalsHTMLParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.is_any_goal_unchecked = False

        def handle_starttag(self, tag, attrs):
            if tag == "input":
                attr_dict = dict(attrs)
                is_checkbox = attr_dict.get("type") == "checkbox"
                is_unchecked = "checked" not in attr_dict
                if is_checkbox and is_unchecked:
                    self.is_any_goal_unchecked = True

        def has_unfinished_goals(self):
            return self.is_any_goal_unchecked

    parser = _GoalsHTMLParser()
    parser.feed(project_item.body_html)
    return parser.has_unfinished_goals()


def is_missing_linked_issue_in_pull_request(project_item: ProjectItemInfo) -> bool:
    result = False
    if project_item.typename is GithubProjectItemType.pull_request:
        result = len(project_item.linked_project_item.nodes) == 0
    return result


CONDITION_CHECK_AND_WARNING_REASON_LIST = [
    (is_not_closed, "not closed"),
    (is_not_assigned, "missing assignee"),
    (has_no_milestone, "missing milestone"),
    (has_unfinished_goals, "missing finished goals"),
    (is_missing_linked_issue_in_pull_request, "missing linked issue"),
]
