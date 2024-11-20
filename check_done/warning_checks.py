# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
from html.parser import HTMLParser

from check_done.info import GithubProjectItemType, ProjectItemInfo


class _StopParsingHtml(Exception):
    """Custom exception to stop HTML parsing."""


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
                    raise _StopParsingHtml


def warnings_for_done_project_items(done_project_items: list[ProjectItemInfo]) -> list[str | None]:
    result = []
    for project_item in done_project_items:
        warning_reasons = [
            warning_reason(project_item)
            for warning_reason in POSSIBLE_WARNINGS
            if warning_reason(project_item) is not None
        ]
        if len(warning_reasons) >= 1:
            warning = sentence_from_project_item_warning_reasons(project_item, warning_reasons)
            result.append(warning)
    return result


def sentence_from_project_item_warning_reasons(project_item: ProjectItemInfo, warning_reasons: list[str]) -> str:
    if len(warning_reasons) >= 3:
        warning_reasons = f"{', '.join(warning_reasons[:-1])}, and {warning_reasons[-1]}"
    elif len(warning_reasons) == 2:
        warning_reasons = f"{', '.join(warning_reasons[:1])} and {warning_reasons[1]}"
    else:
        warning_reasons = warning_reasons[0]
    return (
        f" Project item should {warning_reasons}."
        f" - repository: {project_item.repository.name!r} - item name: '#{project_item.number} {project_item.title}'."
    )


def warning_reason_if_open(project_item: ProjectItemInfo) -> str | None:
    return "be closed" if not project_item.closed else None


def warning_reason_if_unassigned(project_item: ProjectItemInfo) -> str | None:
    return "be assigned" if project_item.assignees.total_count == 0 else None


def warning_reason_if_missing_milestone(project_item: ProjectItemInfo) -> str | None:
    return "have a milestone" if project_item.milestone is None else None


def warning_reason_if_tasks_are_uncompleted(project_item: ProjectItemInfo) -> str | None:
    # TODO#29 Change parsing of tasks to markdown description.
    #  Background: This is less fragile than HTML because even if GitHub changes the names of HTML
    #  types it will still work.
    parser = _AllTasksCheckedHtmlParser()
    try:
        parser.feed(project_item.body_html)
        parser.close()
    except _StopParsingHtml:
        pass  # Stop parsing HTML after first unchecked task.
    return "have all tasks completed" if not parser.all_tasks_are_checked else None


def warning_reason_if_missing_closing_issue_reference_in_pull_request(project_item: ProjectItemInfo) -> str | None:
    is_missing_closing_issue_reference_in_pull_request = (
        len(project_item.closing_issues_references.nodes) == 0
        if project_item.typename is GithubProjectItemType.pull_request
        else False
    )
    return "have a closing issue reference" if is_missing_closing_issue_reference_in_pull_request else None


POSSIBLE_WARNINGS = [
    warning_reason_if_open,
    warning_reason_if_unassigned,
    warning_reason_if_missing_milestone,
    warning_reason_if_tasks_are_uncompleted,
    warning_reason_if_missing_closing_issue_reference_in_pull_request,
]
