from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, NonNegativeInt, field_validator


class NodesTypeName(StrEnum):
    CustomField = "CustomField"
    MultiUserIssueCustomField = "MultiUserIssueCustomField"
    PeriodProjectCustomField = "PeriodProjectCustomField"
    PeriodIssueCustomField = "PeriodIssueCustomField"
    ProjectTimeTrackingSettings = "ProjectTimeTrackingSettings"
    SingleUserIssueCustomField = "SingleUserIssueCustomField"


class ProjectItemState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"


class GithubContentType(StrEnum):
    ISSUE = "ISSUE"
    DRAFT_ISSUE = "DRAFT_ISSUE"
    PULL_REQUEST = "PULL_REQUEST"


class _EmptyDict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PageInfo(BaseModel):
    endCursor: str
    hasNextPage: bool


class PaginatedQueryInfo(BaseModel):
    nodes: list[Any]
    page_info: PageInfo = Field(alias="pageInfo")

    @field_validator("nodes", mode="after", check_fields=True)
    def validate_each_node(cls, nodes: list[Any]):
        validated_nodes = []
        for node in nodes:
            node_type = node.get("__typename")
            if node.get("__typename") in _NODE_TYPE_NAME_TO_INFO_CLASS_MAP:
                node_model = _NODE_TYPE_NAME_TO_INFO_CLASS_MAP.get(node_type)
                validated_nodes.append(node_model(**node))
        return validated_nodes


class ProjectV2NodeInfo(BaseModel):
    id: str
    number: NonNegativeInt
    typename: str = Field(alias="__typename")
    fields: PaginatedQueryInfo | None = None
    items: PaginatedQueryInfo | None = None


class ProjectV2Options(BaseModel):
    id: str
    name: str


class ProjectV2SingleSelectFieldNodeInfo(BaseModel):
    id: str
    name: str
    typename: str = Field(alias="__typename")
    options: list[ProjectV2Options]


class ProjectV2ItemProjectStatusInfo(BaseModel):
    status: str
    option_id: str = Field(alias="optionId")


class RepositoryInfo(BaseModel):
    name: str


class AssigneesInfo(BaseModel):
    total_count: NonNegativeInt = Field(alias="totalCount")


class MilestoneInfo(BaseModel):
    id: str


class LinkedProjectItemNodeInfo(BaseModel):
    number: NonNegativeInt
    title: str


class LinkedProjectItemInfo(BaseModel):
    nodes: list[LinkedProjectItemNodeInfo]


# NOTE: For simplicity, both issues and pull requests are treated the same under a generic "project item" type.
#  Since all their underlying properties needed for checking are essentially identical,
#  there is no value in differentiating between them as long as the above continues to be the case.
class ProjectItemInfo(BaseModel):
    """A generic type representing both issues and pull requests in a project board."""

    assignees: AssigneesInfo
    body_html: str = Field(alias="bodyHTML", default=None)
    closed: bool
    number: NonNegativeInt
    repository: RepositoryInfo
    milestone: MilestoneInfo | None
    title: str
    linked_project_item: LinkedProjectItemInfo = Field(
        validation_alias=AliasChoices(
            "closedByPullRequestsReferences", "closingIssuesReferences", "linked_project_item"
        )
    )


class ProjectV2ItemNodeInfo(BaseModel):
    type: GithubContentType
    # TODO#4: When including pull requests, implement their info model
    #  See: https://docs.github.com/en/graphql/reference/unions#projectv2itemcontent
    content: ProjectItemInfo | _EmptyDict = None
    field_value_by_name: ProjectV2ItemProjectStatusInfo | None = Field(alias="fieldValueByName", default=None)


class NodeByIdInfo(BaseModel):
    node: ProjectV2NodeInfo


class _ProjectsV2Info(BaseModel):
    projects_v2: PaginatedQueryInfo = Field(alias="projectsV2")


class ProjectOwnerInfo(BaseModel):
    """
    A generic type representing the project owner whether they are an organization or user.
    The difference between organization and user is irrelevant in check_done's case,
    as we are only using the project owner to retrieve the projects ID's.
    """

    project_owner: _ProjectsV2Info = Field(validation_alias=AliasChoices("organization", "user"))


class _NodeTypeName(StrEnum):
    ProjectV2 = "ProjectV2"
    ProjectV2SingleSelectField = "ProjectV2SingleSelectField"
    ProjectV2Item = "ProjectV2Item"


_NODE_TYPE_NAME_TO_INFO_CLASS_MAP = {
    _NodeTypeName.ProjectV2.value: ProjectV2NodeInfo,
    _NodeTypeName.ProjectV2SingleSelectField.value: ProjectV2SingleSelectFieldNodeInfo,
    _NodeTypeName.ProjectV2SingleSelectField.ProjectV2Item: ProjectV2ItemNodeInfo,
}
