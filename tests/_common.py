# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import os
from contextlib import contextmanager

from check_done.config import (
    github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches,
)
from check_done.info import (
    AssigneesInfo,
    GithubProjectItemType,
    LinkedProjectItemInfo,
    LinkedProjectItemNode,
    MilestoneInfo,
    ProjectItemInfo,
    ProjectV2ItemNode,
    ProjectV2ItemProjectStatusInfo,
    RepositoryInfo,
)

_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_ID = "CHECK_DONE_GITHUB_APP_ID"
_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY = "CHECK_DONE_GITHUB_APP_PRIVATE_KEY"
ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK = "CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK"
_ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_URL = "CHECK_DONE_GITHUB_PROJECT_URL"

DEMO_CHECK_DONE_GITHUB_APP_ID = os.environ.get(_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_ID)
DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY = os.environ.get(_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY)
DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK = os.environ.get(
    ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_STATUS_NAME_TO_CHECK
)
DEMO_CHECK_DONE_GITHUB_PROJECT_URL = os.environ.get(_ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_URL)

(
    DEMO_CHECK_DONE_PROJECT_OWNER_NAME,
    DEMO_CHECK_DONE_PROJECT_NUMBER,
    DEMO_CHECK_DONE_IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION,
) = (
    github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches(
        DEMO_CHECK_DONE_GITHUB_PROJECT_URL
    )
    if DEMO_CHECK_DONE_GITHUB_PROJECT_URL
    else (None, None, None)
)

HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED = (
    DEMO_CHECK_DONE_GITHUB_PROJECT_URL is not None
    and DEMO_CHECK_DONE_GITHUB_APP_ID is not None
    and DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY is not None
    and DEMO_CHECK_DONE_IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION
)
REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED = (
    f"To enable, setup the configuration file for an organization as described in the readme, "
    f"and set the following environment variables:"
    f"{_ENVVAR_DEMO_CHECK_DONE_GITHUB_PROJECT_URL}"
    f"{_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_ID}"
    f"{_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY}"
    f"{_ENVVAR_DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY}"
)


def new_fake_project_v2_item_node(status: str = "Done", option_id: str = "a1", closed: bool = True):
    return ProjectV2ItemNode(
        __typename="ProjectV2Item",
        content=new_fake_project_item_info(closed=closed),
        fieldValueByName=ProjectV2ItemProjectStatusInfo(status=status, optionId=option_id),
    )


def new_fake_project_item_info(
    has_no_milestone: bool = False,
    assignees_count: int = 1,
    body_html: str = "",
    closed: bool = True,
    closing_issues_references: [] = None,
    milestone: MilestoneInfo = None,
    number: int = 1,
    repository: RepositoryInfo = None,
    title: str = "fake_title",
    typename: GithubProjectItemType = GithubProjectItemType.pull_request,
):
    if closing_issues_references is None:
        closing_issues_references = [LinkedProjectItemNode(number=1, title="fake_closing_issues_references")]
    if milestone is None and not has_no_milestone:
        milestone = MilestoneInfo(id="fake_milestone_id")
    if repository is None:
        repository = RepositoryInfo(name="fake_repository")
    return ProjectItemInfo(
        __typename=typename,
        assignees=AssigneesInfo(totalCount=assignees_count),
        bodyHTML=body_html,
        closed=closed,
        closingIssuesReferences=LinkedProjectItemInfo(nodes=closing_issues_references),
        milestone=milestone,
        number=number,
        repository=repository,
        title=title,
    )


@contextmanager
def change_current_folder(path):
    old_folder = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_folder)
