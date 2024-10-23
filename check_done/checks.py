from check_done.done_project_items_info.done_project_items_info import done_project_items_info
from check_done.done_project_items_info.info import ProjectItemInfo


def check_done_issues_for_warnings() -> list[str | None]:
    result = []
    done_issues = done_project_items_info()
    criteria_checks = [
        _check_done_issues_are_closed,
    ]
    for issue in done_issues:
        warnings = [check(issue) for check in criteria_checks if check(issue)]
        result.extend(warnings)
    return result


def _check_done_issues_are_closed(issue: ProjectItemInfo) -> str | None:
    result = None
    if not issue.closed:
        result = _issue_warning_string(
            issue,
            "closed",
        )
    return result


def _issue_warning_string(issue: ProjectItemInfo, reason_for_warning: str) -> str:
    # TODO: Ponder better wording.
    return (
        f" Done project item should be {reason_for_warning}."
        f" - repository: '{issue.repository.name}', project item: '#{issue.number} {issue.title}'."
    )
