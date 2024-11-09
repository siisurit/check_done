import os
from pathlib import Path

import pytest
import yaml

from check_done.common import (
    ConfigurationInfo,
    ProjectOwnerType,
    YamlInfo,
    configuration_map_from_yaml_file,
    github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches,
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
    result = configuration_map_from_yaml_file(path)
    expected_result = {"name": ["Joe Doe"]}
    assert result == expected_result
    mock_open.assert_called_once_with(path)


def test_fails_to_load_configuration_file(mocker):
    mocker.patch("os.path.exists", return_value=False)
    path = Path("non_existent.yaml")
    with pytest.raises(FileNotFoundError, match="Cannot find check_done configuration: "):
        configuration_map_from_yaml_file(path)


def test_fails_on_invalid_yaml_syntax(mocker):
    invalid_yaml = """
    name: "Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=invalid_yaml))
    path = Path("invalid.yaml")
    with pytest.raises(yaml.YAMLError):
        configuration_map_from_yaml_file(path)


def test_fails_to_load_empty_yaml_config_file(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))
    mocker.patch("os.path.exists", return_value=True)
    path = Path("empty_config.yaml")
    with pytest.raises(ValueError, match="The check_done configuration is empty. Path: "):
        configuration_map_from_yaml_file(path)


def test_can_resolve_environment_variables():
    envvar_name = "TEST_CAN_RESOLVE_FROM"
    os.environ[envvar_name] = "hello"
    assert resolved_environment_variables(f"${{{envvar_name}}}") == "hello"


def test_can_pass_on_missing_environment_variable():
    envvar_name = "MISSING_ENVIRONMENT_VARIABLE"
    assert resolved_environment_variables(f"${{{envvar_name}}}", fail_on_missing_envvar=False) == ""


def test_fails_to_resolve_non_existent_environment_variable():
    with pytest.raises(ValueError):
        resolved_environment_variables("${__no_such_environment_variable__}", True)


def test_fails_to_resolve_environment_variables_with_syntax_error():
    with pytest.raises(ValueError):
        resolved_environment_variables("${")


def test_can_extract_github_project_owner_type_and_project_owner_name_and_project_number_from_url():
    assert github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(
        "https://github.com/orgs/example-org/projects/1"
    ) == (ProjectOwnerType.Organization, "example-org", 1)
    assert github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(
        "https://github.com/orgs/example-org/projects/1/some-other-stuff"
    ) == (ProjectOwnerType.Organization, "example-org", 1)
    assert github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(
        "https://github.com/users/example-username/projects/1"
    ) == (ProjectOwnerType.User, "example-username", 1)
    assert github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(
        "https://github.com/users/example-username/projects/1/some-other-stuff"
    ) == (ProjectOwnerType.User, "example-username", 1)


def test_fails_to_extract_github_project_owner_type_and_project_owner_name_and_project_number_from_url():
    urls = [
        "https://github.com/orgs/",
        "https://github.com/users/",
        "https://github.com/orgs/example-org/projects/",
        "https://github.com/users/example-username/projects/",
        "",
    ]
    for url in urls:
        expected_error_message = rf"Cannot parse GitHub organization or user name, and project number from URL: {url}."
        with pytest.raises(ValueError, match=expected_error_message):
            github_project_owner_type_and_project_owner_name_and_project_number_from_url_if_matches(url)


def test_can_validate_at_least_one_authentication_method_in_configuration():
    configuration_info_with_personal_token_authentication_only = ConfigurationInfo(
        personal_access_token="fake_personal_token",
        project_number=1,
        project_owner_name="fake_project_owner_name",
        project_owner_type=str(ProjectOwnerType.User.value),
    )
    configuration_info_with_organization_authentication_config_only = ConfigurationInfo(
        check_done_github_app_id="fake_app_id",
        check_done_github_app_private_key="fake_private_key",
        project_number=1,
        project_owner_name="another_fake_project_owner_name",
        project_owner_type=str(ProjectOwnerType.Organization.value),
    )
    assert isinstance(configuration_info_with_personal_token_authentication_only, ConfigurationInfo)
    assert isinstance(configuration_info_with_organization_authentication_config_only, ConfigurationInfo)


def test_fails_to_validate_at_least_one_authentication_method_in_configuration():
    with pytest.raises(ValueError, match="At least one authentication method must be configured."):
        ConfigurationInfo(
            project_number=1,
            project_owner_name="fake_project_owner_name",
            project_owner_type=str(ProjectOwnerType.Organization.value),
        )


def test_fails_to_validate_organization_authentication_method_with_one_missing_value_in_configuration():
    with pytest.raises(ValueError, match="At least one authentication method must be configured."):
        ConfigurationInfo(
            check_done_github_app_id="fake_check_done_github_app_id",
            project_number=1,
            project_owner_name="fake_project_owner_name",
            project_owner_type=str(ProjectOwnerType.Organization.value),
        )


def test_fails_to_validate_organization_authentication_method_with_another_missing_value_in_configuration():
    with pytest.raises(ValueError, match="At least one authentication method must be configured."):
        ConfigurationInfo(
            check_done_github_app_private_key="fake_check_done_github_app_private_key",
            project_number=1,
            project_owner_name="fake_project_owner_name",
            project_owner_type=str(ProjectOwnerType.Organization.value),
        )


def test_can_get_value_from_env():
    envvar_name = "FAKE_CHECK_DONE_GITHUB_PROJECT_URL"
    os.environ[envvar_name] = "example.com"
    yaml_info_with_env_value = YamlInfo(
        project_url="${FAKE_CHECK_DONE_GITHUB_PROJECT_URL}",
        personal_access_token="fake_personal_token",
    )
    assert yaml_info_with_env_value.project_url == "example.com"
