# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import logging

import requests

from check_done.config import configuration_info
from check_done.graphql import GraphQlQuery, HttpBearerAuth, query_infos
from check_done.info import (
    IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION,
    PROJECT_NUMBER,
    PROJECT_OWNER_NAME,
    NodeByIdInfo,
    ProjectItemInfo,
    ProjectOwnerInfo,
    ProjectV2ItemNode,
    ProjectV2Node,
    ProjectV2SingleSelectFieldNode,
)
from check_done.organization_authentication import access_token_from_organization

_PROJECT_STATUS_NAME_TO_CHECK = configuration_info().project_status_name_to_check
_PERSONAL_ACCESS_TOKEN = configuration_info().personal_access_token
_ORGANIZATION_ACCESS_TOKEN = (
    access_token_from_organization(PROJECT_OWNER_NAME) if IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION else None
)
_ACCESS_TOKEN = _ORGANIZATION_ACCESS_TOKEN or _PERSONAL_ACCESS_TOKEN
_GITHUB_PROJECT_STATUS_FIELD_NAME = "Status"
logger = logging.getLogger(__name__)


def done_project_items_info() -> list[ProjectItemInfo]:
    with requests.Session() as session:
        session.headers = {"Accept": "application/vnd.github+json"}
        session.auth = HttpBearerAuth(_ACCESS_TOKEN)

        project_query_name = (
            GraphQlQuery.ORGANIZATION_PROJECTS.name
            if IS_PROJECT_OWNER_OF_TYPE_ORGANIZATION
            else GraphQlQuery.USER_PROJECTS.name
        )
        project_infos = query_infos(ProjectOwnerInfo, project_query_name, session)
        project_id = matching_project_id(project_infos)
        project_single_select_field_infos = query_infos(
            NodeByIdInfo, GraphQlQuery.PROJECT_SINGLE_SELECT_FIELDS.name, session, project_id
        )
        project_item_infos = query_infos(NodeByIdInfo, GraphQlQuery.PROJECT_V2_ITEMS.name, session, project_id)

    project_status_option_id = matching_project_state_option_id(
        project_single_select_field_infos, _PROJECT_STATUS_NAME_TO_CHECK
    )
    result = filtered_project_item_infos_by_done_status(project_item_infos, project_status_option_id)
    return result


def matching_project_id(project_infos: list[ProjectV2Node]) -> str:
    try:
        return next(str(project_info.id) for project_info in project_infos if project_info.number == PROJECT_NUMBER)
    except StopIteration:
        raise ValueError(
            f"Cannot find a project with number '{PROJECT_NUMBER}', owned by '{PROJECT_OWNER_NAME}'."
        ) from None


def matching_project_state_option_id(
    project_single_select_field_infos: list[ProjectV2SingleSelectFieldNode],
    project_status_name_to_check: str | None,
) -> str:
    try:
        status_options = next(
            field_info.options
            for field_info in project_single_select_field_infos
            if field_info.name == _GITHUB_PROJECT_STATUS_FIELD_NAME
        )
    except StopIteration:
        raise ValueError(
            f"Cannot find a project status selection field in the GitHub project with number `{PROJECT_NUMBER}` "
            f"owned by `{PROJECT_OWNER_NAME}`."
        ) from None
    if project_status_name_to_check:
        logger.info(f"Checking project items with status matching: '{project_status_name_to_check}'")
        try:
            result = next(
                status_option.id
                for status_option in status_options
                if project_status_name_to_check in status_option.name
            )
        except StopIteration:
            project_status_options_names = [
                option.name for field_info in project_single_select_field_infos for option in field_info.options
            ]
            raise ValueError(
                f"Cannot find the project status matching name '{_PROJECT_STATUS_NAME_TO_CHECK}' "
                f"in the GitHub project with number `{PROJECT_NUMBER}` owned by `{PROJECT_OWNER_NAME}`. "
                f"Available options are: {project_status_options_names}"
            ) from None
    else:
        logger.info("Checking project items in the last status/board column.")
        result = status_options[-1].id
    return result


def filtered_project_item_infos_by_done_status(
    project_item_infos: list[ProjectV2ItemNode],
    project_state_option_id: str,
) -> list[ProjectItemInfo]:
    result = []
    for project_item_info in project_item_infos:
        has_project_state_option = (
            project_item_info.field_value_by_name is not None
            and project_item_info.field_value_by_name.option_id == project_state_option_id
        )
        if has_project_state_option:
            result.append(project_item_info.content)
    if len(result) < 1:
        logger.warning(
            f"No project items found for the specified project status in the GitHub project "
            f"with number '{PROJECT_NUMBER}' owned by '{PROJECT_OWNER_NAME}'."
        )
    return result
