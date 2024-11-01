import os
import re
import string
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
from requests.auth import AuthBase

load_dotenv()

_GITHUB_ORGANIZATION_NAME_AND_PROJECT_NUMBER_URL_REGEX = re.compile(
    r"https://github\.com/orgs/(?P<organization_name>[a-zA-Z0-9\-]+)/projects/(?P<project_number>[0-9]+).*"
)
_CONFIG_PATH = Path(__file__).parent.parent / "data" / ".check_done.yaml"


class _ConfigInfo(BaseModel):
    project_board_url: str
    check_done_github_app_id: str
    check_done_github_app_private_key: str

    @field_validator("check_done_github_app_id", "check_done_github_app_private_key", mode="before")
    def value_from_env(cls, value: Any | None):
        if isinstance(value, str):
            stripped_value = value.strip()
            result = (
                resolved_environment_variables(value)
                if stripped_value.startswith("${") and stripped_value.endswith("}")
                else stripped_value
            )
        else:
            result = value
        return result


def config_info() -> _ConfigInfo:
    config_map = config_map_from_yaml_file(_CONFIG_PATH)
    return _ConfigInfo(**config_map)


def github_organization_name_and_project_number_from_url_if_matches(url: str) -> tuple[str, int]:
    organization_name_and_project_number_match = _GITHUB_ORGANIZATION_NAME_AND_PROJECT_NUMBER_URL_REGEX.match(url)
    if organization_name_and_project_number_match is None:
        raise ValueError(f"Cannot parse GitHub organization name and project number from URL: {url}.")
    organization_name = organization_name_and_project_number_match.group("organization_name")
    project_number = int(organization_name_and_project_number_match.group("project_number"))
    return organization_name, project_number


def resolved_environment_variables(value: str, fail_on_missing_envvar=True) -> str:
    try:
        result = string.Template(value).substitute(os.environ)
    except KeyError as error:
        if fail_on_missing_envvar:
            raise ValueError(f"Cannot resolve {value}: environment variable must be set: {error!s}") from error
        result = ""
    except ValueError as error:
        raise ValueError(f"Cannot resolve {value!r}: {error}.") from error
    return result


def config_map_from_yaml_file(config_path: Path) -> dict:
    try:
        with open(config_path) as config_file:
            result = yaml.safe_load(config_file)
            if result is None:
                raise ValueError(f"The check_done configuration is empty. Path: {config_path}")
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Cannot find check_done configuration: {config_path}") from error
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
