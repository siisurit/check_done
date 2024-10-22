import logging
import sys

from check_done.done_project_items_info.done_project_items_info import (
    done_project_items_info,
)
from check_done.done_project_items_info.info import IssueInfo, IssueState

logger = logging.getLogger(__name__)


def _issue_warning_string(issue: IssueInfo, reason_for_warning: str) -> str:
    # TODO: Ponder better wording.
    return (
        f" Issue '#{issue.number} {issue.title}' in repository '{issue.repository.name}' "
        f"should be {reason_for_warning}."
    )


def _check_done_issues_are_closed(issue: IssueInfo) -> str | None:
    result = None
    if issue.state == IssueState.OPEN:
        result = _issue_warning_string(
            issue,
            f"of state {IssueState.CLOSED.value} but is of state {IssueState.OPEN.value}",
        )
    return result


def _check_done_issues_for_warnings() -> list[str | None]:
    result = []
    done_issues = done_project_items_info()
    criteria_checks = [
        _check_done_issues_are_closed,
    ]
    for issue in done_issues:
        warnings = [check(issue) for check in criteria_checks if check(issue)]
        result.extend(warnings)
    return result


def check_done_command():
    result = 1
    try:
        warnings = _check_done_issues_for_warnings()
        if len(warnings) == 0:
            logging.info("No warnings found.")
            result = 0
        else:
            for warning in warnings:
                logging.warning(warning)
    except KeyboardInterrupt:
        logging.exception("Interrupted as requested by user.")
    except Exception:
        logging.exception("Cannot check done issues.")
    return result


def main():
    logging.basicConfig(level=logging.INFO)
    sys.exit(check_done_command())


if __name__ == "__main__":
    main()
