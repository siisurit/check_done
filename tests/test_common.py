import os
from pathlib import Path

import pytest
import yaml

from check_done.common import (
    config_map_from_yaml_file,
    github_organization_name_and_project_number_from_url_if_matches,
    resolved_environment_variables,
)


def test_can_load_valid_yaml(mocker):
    valid_yaml = """
    name:
      - Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mock_open = mocker.mock_open(read_data=valid_yaml)
    mocker.patch("builtins.open", mock_open)
    path = Path("valid.yaml")
    result = config_map_from_yaml_file(path)
    expected_result = {"name": ["Joe Doe"]}
    assert result == expected_result
    mock_open.assert_called_once_with(path)


def test_fails_to_load_configuration_file(mocker):
    mocker.patch("os.path.exists", return_value=False)
    path = Path("non_existent.yaml")
    with pytest.raises(FileNotFoundError, match="Cannot find check_done configuration: "):
        config_map_from_yaml_file(path)


def test_fails_on_invalid_yaml_syntax(mocker):
    invalid_yaml = """
    name: "Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=invalid_yaml))
    path = Path("invalid.yaml")
    with pytest.raises(yaml.YAMLError):
        config_map_from_yaml_file(path)


def test_fails_to_load_empty_yaml_config_file(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))
    mocker.patch("os.path.exists", return_value=True)
    path = Path("empty_config.yaml")
    with pytest.raises(ValueError, match="The check_done configuration is empty. Path: "):
        config_map_from_yaml_file(path)


def test_can_resolve_environment_variables():
    envvar_name = "TEST_CAN_RESOLVE_FROM"
    os.environ[envvar_name] = "hello"
    assert resolved_environment_variables(f"${{{envvar_name}}}") == "hello"


def test_fails_to_resolve_non_existent_environment_variable():
    with pytest.raises(ValueError):
        resolved_environment_variables("${__no_such_environment_variable__}", True)


def test_fails_to_resolve_environment_variables_with_syntax_error():
    with pytest.raises(ValueError):
        resolved_environment_variables("${")


def test_can_extract_github_organization_name_and_project_number_from_url():
    assert github_organization_name_and_project_number_from_url_if_matches(
        "https://github.com/orgs/example-org/projects/1"
    ) == ("example-org", 1)


def test_fails_to_extract_github_organization_name_and_project_number_from_url():
    urls = [
        "https://github.com/orgs/",
        "https://github.com/orgs/example-org/projects/",
        "",
    ]
    for url in urls:
        with pytest.raises(ValueError, match=r"Cannot parse GitHub organization name and project number from URL: .*"):
            github_organization_name_and_project_number_from_url_if_matches(url)
