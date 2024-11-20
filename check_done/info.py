# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
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


class GithubProjectItemType(StrEnum):
    issue = "Issue"
    pull_request = "PullRequest"


class _EmptyDict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PageInfo(BaseModel):
    endCursor: str
    hasNextPage: bool


class QueryInfo(BaseModel):
    """The nested content of the query and its pagination info in a paginated GraphQL query with nodes"""

    nodes: list[Any]
    page_info: PageInfo = Field(alias="pageInfo")

    @field_validator("nodes", mode="after", check_fields=True)
    def resolve_nodes(cls, nodes: list[Any]):
        validated_nodes = []
        for node in nodes:
            node_type = node.get("__typename")
            if node.get("__typename") in _NODE_TYPE_NAME_TO_INFO_CLASS_MAP:
                node_model = _NODE_TYPE_NAME_TO_INFO_CLASS_MAP.get(node_type)
                validated_nodes.append(node_model(**node))
        return validated_nodes


class ProjectV2Node(BaseModel):
    id: str
    number: NonNegativeInt
    typename: str = Field(alias="__typename")
    fields: QueryInfo | None = None
    items: QueryInfo | None = None


class ProjectV2Options(BaseModel):
    id: str
    name: str


class ProjectV2SingleSelectFieldNode(BaseModel):
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


class LinkedProjectItemNode(BaseModel):
    number: NonNegativeInt
    title: str


class LinkedProjectItemInfo(BaseModel):
    nodes: list[LinkedProjectItemNode]


# NOTE: For simplicity, both issues and pull requests are treated the same under a generic "project item" type.
#  Since all their underlying properties needed for checking, are mostly identical.
class ProjectItemInfo(BaseModel):
    """A generic type representing both issues and pull requests in a project board."""

    # Shared between Issues and Pull Requests.
    typename: GithubProjectItemType = Field(alias="__typename")
    assignees: AssigneesInfo
    body_html: str = Field(alias="bodyHTML", default=None)
    closed: bool
    number: NonNegativeInt
    repository: RepositoryInfo
    milestone: MilestoneInfo | None
    title: str

    # Only set for pull requests
    closing_issues_references: LinkedProjectItemInfo = Field(alias="closingIssuesReferences", default=None)


class ProjectV2ItemNode(BaseModel):
    content: ProjectItemInfo | _EmptyDict = None
    field_value_by_name: ProjectV2ItemProjectStatusInfo | None = Field(alias="fieldValueByName", default=None)
    typename: str = Field(alias="__typename")


class NodeByIdInfo(BaseModel):
    node: ProjectV2Node


class _ProjectsV2Info(BaseModel):
    projects_v2: QueryInfo = Field(alias="projectsV2")


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
    _NodeTypeName.ProjectV2.value: ProjectV2Node,
    _NodeTypeName.ProjectV2SingleSelectField.value: ProjectV2SingleSelectFieldNode,
    _NodeTypeName.ProjectV2SingleSelectField.ProjectV2Item: ProjectV2ItemNode,
}
