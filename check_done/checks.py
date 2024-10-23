from check_done.done_project_items_info.done_project_items_info import done_project_items_info
from check_done.done_project_items_info.info import ProjectItemInfo


def check_done_project_items_for_warnings() -> list[str | None]:
    result = []
    done_project_items = done_project_items_info()
    for project_item in done_project_items:
        warning_reasons = [
            warning_reason for check, warning_reason in CONDITION_CHECK_AND_WARNING_REASON_LIST if check(project_item)
        ]
        if len(warning_reasons) >= 1:
            warning = _project_item_warning_string(project_item, warning_reasons)
            result.append(warning)
    return result


def _project_item_warning_string(issue: ProjectItemInfo, reasons_for_warning: list[str]) -> str:
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


def _is_not_closed(project_item: ProjectItemInfo) -> bool:
    return not project_item.closed


def _is_not_assigned(project_item: ProjectItemInfo) -> bool:
    return project_item.assignees.total_count < 1


CONDITION_CHECK_AND_WARNING_REASON_LIST = [
    (_is_not_closed, "not closed"),
    (_is_not_assigned, "missing assignee"),
]
