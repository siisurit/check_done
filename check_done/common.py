import os
import re
import string
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator
from requests.auth import AuthBase

load_dotenv()

_CONFIGURATION_PATH = Path(__file__).parent.parent / "configuration" / ".check_done.yaml"
_GITHUB_ORGANIZATION_NAME_AND_PROJECT_NUMBER_URL_REGEX = re.compile(
    r"https://github\.com/orgs/(?P<organization_name>[a-zA-Z0-9\-]+)/projects/(?P<project_number>[0-9]+).*"
)
_GITHUB_USER_NAME_AND_PROJECT_NUMBER_URL_REGEX = re.compile(
    r"https://github\.com/users/(?P<user_name>[a-zA-Z0-9\-]+)/projects/(?P<project_number>[0-9]+).*"
)


class YamlInfo(BaseModel):
    check_done_github_app_id: str | None = None
    check_done_github_app_private_key: str | None = None
    personal_access_token: str | None = None
    project_status_name_to_check: str | None = None
    project_url: str

    # TODO#13: Add more descriptive error messages than the default pydantic for miss-configurations.

    @field_validator(
        "project_url",
        "project_status_name_to_check",
        "personal_access_token",
        "check_done_github_app_id",
        "check_done_github_app_private_key",
        mode="before",
    )
    def value_from_env(cls, value: Any | None):
        stripped_value = value.strip()
        result = (
            resolved_environment_variables(value, fail_on_missing_envvar=False)
            if stripped_value.startswith("${") and stripped_value.endswith("}")
            else stripped_value
        )
        return result


class ConfigurationInfo(BaseModel):
    check_done_github_app_id: str | None = None
    check_done_github_app_private_key: str | None = None
    personal_access_token: str | None = None
    project_number: int
    project_owner_name: str
    project_owner_type: str
    project_status_name_to_check: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one_authentication_method_in_configuration(self):
        has_user_authentication = (
            self.personal_access_token is not None and self.project_owner_type == ProjectOwnerType.User.value
        )
        has_organizational_authentication = (
            self.check_done_github_app_id is not None
            and self.check_done_github_app_private_key is not None
            and self.project_owner_type == ProjectOwnerType.Organization.value
        )
        if not (has_user_authentication or has_organizational_authentication):
            raise ValueError("At least one authentication method must be configured.")
        return self


def configuration_info() -> ConfigurationInfo:
    yaml_map = configuration_map_from_yaml_file(_CONFIGURATION_PATH)
    yaml_info = YamlInfo(**yaml_map)
    project_url = yaml_info.project_url
    project_owner_type, project_owner_name, project_number = (
        github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(project_url)
    )
    return ConfigurationInfo(
        check_done_github_app_id=yaml_info.check_done_github_app_id,
        check_done_github_app_private_key=yaml_info.check_done_github_app_private_key,
        personal_access_token=yaml_info.personal_access_token,
        project_number=project_number,
        project_owner_name=project_owner_name,
        project_owner_type=project_owner_type,
        project_status_name_to_check=yaml_info.project_status_name_to_check,
    )


class ProjectOwnerType(StrEnum):
    User = "users"
    Organization = "orgs"


def github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(
    url: str,
) -> tuple[ProjectOwnerType, str, int]:
    organization_name_and_project_number_match = _GITHUB_ORGANIZATION_NAME_AND_PROJECT_NUMBER_URL_REGEX.match(url)
    if organization_name_and_project_number_match is None:
        user_name_and_project_number_match = _GITHUB_USER_NAME_AND_PROJECT_NUMBER_URL_REGEX.match(url)
        if organization_name_and_project_number_match is None and user_name_and_project_number_match is None:
            raise ValueError(f"Cannot parse GitHub organization or user name, and project number from URL: {url}.")
        project_owner_type = ProjectOwnerType.User
        project_owner_name = user_name_and_project_number_match.group("user_name")
        project_number = int(user_name_and_project_number_match.group("project_number"))
    else:
        project_owner_type = ProjectOwnerType.Organization
        project_owner_name = organization_name_and_project_number_match.group("organization_name")
        project_number = int(organization_name_and_project_number_match.group("project_number"))
    return project_owner_type, project_owner_name, project_number


def resolved_environment_variables(value: str, fail_on_missing_envvar=True) -> str:
    try:
        result = string.Template(value).substitute(os.environ)
    except KeyError as error:
        if fail_on_missing_envvar:
            raise ValueError(f"Cannot resolve {value}: environment variable must be set: {error!s}") from error
        result = None
    except ValueError as error:
        raise ValueError(f"Cannot resolve {value!r}: {error}.") from error
    return result


def configuration_map_from_yaml_file(configuration_path: Path) -> dict:
    try:
        with open(configuration_path) as configuration_file:
            result = yaml.safe_load(configuration_file)
            if result is None:
                raise ValueError(f"The check_done configuration is empty. Path: {configuration_path}")
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Cannot find check_done configuration: {configuration_path}") from error
    return result


class AuthenticationError(Exception):
    """Error raised due to failed JWT authentication process."""


class HttpBearerAuth(AuthBase):
    # Source:
    # <https://stackoverflow.com/questions/29931671/making-an-api-call-in-python-with-an-api-that-requires-a-bearer-token>
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers["Authorization"] = "Bearer " + self.token
        return request
