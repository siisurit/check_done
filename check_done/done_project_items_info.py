# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import logging

import requests

from check_done.config import ConfigurationInfo
from check_done.graphql import GraphQlQuery, HttpBearerAuth, query_infos
from check_done.info import (
    NodeByIdInfo,
    ProjectItemInfo,
    ProjectOwnerInfo,
    ProjectV2ItemNode,
    ProjectV2Node,
    ProjectV2SingleSelectFieldNode,
)
from check_done.organization_authentication import resolve_organization_access_token

_GITHUB_PROJECT_STATUS_FIELD_NAME = "Status"
logger = logging.getLogger(__name__)


def done_project_items_info(configuration_info: ConfigurationInfo) -> list[ProjectItemInfo]:
    project_owner_name = configuration_info.project_owner_name

    is_project_owner_of_type_organization = configuration_info.is_project_owner_of_type_organization
    if is_project_owner_of_type_organization:
        github_app_id = configuration_info.github_app_id
        github_app_private_key = configuration_info.github_app_private_key
        access_token = resolve_organization_access_token(project_owner_name, github_app_id, github_app_private_key)
    else:
        access_token = configuration_info.personal_access_token

    with requests.Session() as session:
        session.headers = {"Accept": "application/vnd.github+json"}
        session.auth = HttpBearerAuth(access_token)

        project_query_name = (
            GraphQlQuery.ORGANIZATION_PROJECTS.name
            if is_project_owner_of_type_organization
            else GraphQlQuery.USER_PROJECTS.name
        )
        project_infos = query_infos(ProjectOwnerInfo, project_query_name, session, project_owner_name)

        project_number = configuration_info.project_number
        project_id = matching_project_id(project_infos, project_number, project_owner_name)
        project_single_select_field_infos = query_infos(
            NodeByIdInfo, GraphQlQuery.PROJECT_SINGLE_SELECT_FIELDS.name, session, project_owner_name, project_id
        )

        project_item_infos = query_infos(
            NodeByIdInfo, GraphQlQuery.PROJECT_V2_ITEMS.name, session, project_owner_name, project_id
        )

    project_status_name_to_check = configuration_info.project_status_name_to_check
    project_status_option_id = matching_project_status_option_id(
        project_single_select_field_infos,
        project_status_name_to_check,
        project_number,
        project_owner_name,
    )
    result = filtered_project_item_infos_by_done_status(project_item_infos, project_status_option_id)
    return result


def matching_project_id(project_infos: list[ProjectV2Node], project_number: int, project_owner_name: str) -> str:
    try:
        return next(str(project_info.id) for project_info in project_infos if project_info.number == project_number)
    except StopIteration:
        raise ValueError(
            f"Cannot find a project with number '{project_number}', owned by '{project_owner_name}'."
        ) from None


def matching_project_status_option_id(
    project_single_select_field_infos: list[ProjectV2SingleSelectFieldNode],
    project_status_name_to_check: str | None,
    project_number: int,
    project_owner_name: str,
) -> str:
    try:
        status_options = next(
            field_info.options
            for field_info in project_single_select_field_infos
            if field_info.name == _GITHUB_PROJECT_STATUS_FIELD_NAME
        )
    except StopIteration:
        raise ValueError(
            f"Cannot find a project status selection field in the GitHub project with number `{project_number}` "
            f"owned by `{project_owner_name}`."
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
                f"Cannot find the project status matching name {project_status_name_to_check!r} "
                f"in the GitHub project with number '{project_number}' owned by {project_owner_name!r}. "
                f"Available options are: {project_status_options_names!r}"
            ) from None
    else:
        last_status_option = status_options[-1]
        logger.info(f"Checking project items with the last project status selected: {last_status_option.name!r}.")
        result = last_status_option.id
    return result


def filtered_project_item_infos_by_done_status(
    project_item_infos: list[ProjectV2ItemNode],
    project_status_option_id: str,
) -> list[ProjectItemInfo]:
    result = []
    for project_item_info in project_item_infos:
        has_project_status_option = (
            project_item_info.field_value_by_name is not None
            and project_item_info.field_value_by_name.option_id == project_status_option_id
        )
        if has_project_status_option:
            result.append(project_item_info.content)
    return result
