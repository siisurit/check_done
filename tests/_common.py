from check_done.info import (
    IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION,
    PROJECT_OWNER_NAME,
    AssigneesInfo,
    GithubProjectItemType,
    LinkedProjectItemInfo,
    LinkedProjectItemNodeInfo,
    MilestoneInfo,
    ProjectItemInfo,
    ProjectV2ItemNodeInfo,
    ProjectV2ItemProjectStatusInfo,
    RepositoryInfo,
)
from check_done.organization_authentication import CHECK_DONE_GITHUB_APP_ID, CHECK_DONE_GITHUB_APP_PRIVATE_KEY

HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION = (
    CHECK_DONE_GITHUB_APP_ID is not None
    and CHECK_DONE_GITHUB_APP_PRIVATE_KEY is not None
    and PROJECT_OWNER_NAME is not None
    and IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION
)
REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION = (
    "To enable, setup the configuration for an organization as described in the readme."
)


def mock_project_v2_item_node_info(status: str = "Done", option_id: str = "a1", closed: bool = True):
    return ProjectV2ItemNodeInfo(
        __typename="ProjectV2Item",
        content=mock_project_item_info(closed=closed),
        fieldValueByName=ProjectV2ItemProjectStatusInfo(status=status, optionId=option_id),
    )


def mock_project_item_info(
    has_no_milestone: bool = False,
    assignees_count: int = 1,
    body_html: str = "",
    closed: bool = True,
    linked_project_items: [] = None,
    milestone: MilestoneInfo = None,
    number: int = 1,
    repository: RepositoryInfo = None,
    title: str = "mock_title",
    typename: GithubProjectItemType = GithubProjectItemType.pull_request,
):
    if linked_project_items is None:
        linked_project_items = [LinkedProjectItemNodeInfo(number=1, title="mock_linked_project_item_title")]
    if milestone is None and not has_no_milestone:
        milestone = MilestoneInfo(id="mock_milestone_id")
    if repository is None:
        repository = RepositoryInfo(name="mock_repository")
    return ProjectItemInfo(
        __typename=typename,
        assignees=AssigneesInfo(totalCount=assignees_count),
        bodyHTML=body_html,
        closed=closed,
        closingIssuesReferences=LinkedProjectItemInfo(nodes=linked_project_items),
        milestone=milestone,
        number=number,
        repository=repository,
        title=title,
    )
