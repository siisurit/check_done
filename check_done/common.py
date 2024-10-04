import os
import re
import string
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

load_dotenv()
_ENVVAR_GITHUB_APP_ID = "GITHUB_APP_ID"
_ENVVAR_GITHUB_APP_PRIVATE_KEY = "GITHUB_APP_PRIVATE_KEY"
GITHUB_APP_ID = os.environ.get(_ENVVAR_GITHUB_APP_ID)
GITHUB_APP_PRIVATE_KEY = os.environ.get(_ENVVAR_GITHUB_APP_PRIVATE_KEY)

_GITHUB_ORGANIZATION_NAME_AND_PROJECT_NUMBER_URL_REGEX = re.compile(
    r"https://github\.com/orgs/(?P<organization_name>[a-zA-Z0-9\-]+)/projects/(?P<project_number>[0-9]+).*"
)
_CONFIG_PATH = Path(__file__).parent.parent / "data" / ".check_done.yaml"


class _BoardInfo(BaseModel):
    url: str
    api_key: str
    trackers: list[str]

    @field_validator("api_key", mode="before")
    def api_key_from_env(cls, api_key: Any | None):
        if isinstance(api_key, str):
            stripped_api_key = api_key.strip()
            result = (
                resolved_environment_variables(api_key)
                if stripped_api_key.startswith("${") and stripped_api_key.endswith("}")
                else stripped_api_key
            )
        else:
            result = api_key
        return result


class _ConfigInfo(BaseModel):
    board: _BoardInfo


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
    """Error raised due to failed authentication in the JWT process."""
