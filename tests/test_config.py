# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from check_done.config import (
    CONFIG_BASE_NAME,
    ConfigurationInfo,
    default_config_path,
    github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches,
    map_from_yaml_file_path,
    resolved_environment_variables,
)
from tests._common import change_current_folder

_TEST_DATA_BASE_FOLDER_FOR_MAP_FROM_YAML_FILE_TESTS = (
    Path(__file__).parent / "data" / "test_configuration_map_from_yaml"
)


def test_can_resolve_map_from_valid_yaml_file_path():
    expected_result = {"name": ["Joe Doe"]}
    valid_yaml_path = _TEST_DATA_BASE_FOLDER_FOR_MAP_FROM_YAML_FILE_TESTS / "fake_valid_yaml.yaml"
    result = map_from_yaml_file_path(valid_yaml_path)
    assert result == expected_result


def test_fails_to_resolve_map_from_missing_yaml_file_path():
    missing_yaml_path = _TEST_DATA_BASE_FOLDER_FOR_MAP_FROM_YAML_FILE_TESTS / "some_missing_yaml.yaml"
    with pytest.raises(FileNotFoundError, match="Cannot find check_done configuration yaml file: "):
        map_from_yaml_file_path(missing_yaml_path)


def test_fails_to_resolve_map_from_yaml_file_on_invalid_yaml_syntax():
    invalid_yaml_path = _TEST_DATA_BASE_FOLDER_FOR_MAP_FROM_YAML_FILE_TESTS / "fake_invalid_yaml.txt"
    with pytest.raises(yaml.YAMLError):
        map_from_yaml_file_path(invalid_yaml_path)


def test_fails_to_load_empty_yaml_config_file():
    empty_yaml_path = _TEST_DATA_BASE_FOLDER_FOR_MAP_FROM_YAML_FILE_TESTS / "fake_empty_yaml.yaml"
    with pytest.raises(ValueError, match="The check_done configuration yaml file is empty. Path: "):
        map_from_yaml_file_path(empty_yaml_path)


def test_can_resolve_environment_variables():
    envvar_name = "TEST_CAN_RESOLVE_FROM"
    os.environ[envvar_name] = "hello"
    assert resolved_environment_variables(f"${{{envvar_name}}}") == "hello"


def test_can_pass_on_missing_environment_variable():
    envvar_name = "MISSING_ENVIRONMENT_VARIABLE"
    assert resolved_environment_variables(f"${{{envvar_name}}}", fail_on_missing_envvar=False) is None


def test_fails_to_resolve_non_existent_environment_variable():
    with pytest.raises(ValueError):
        resolved_environment_variables("${__no_such_environment_variable__}", True)


def test_fails_to_resolve_environment_variables_with_syntax_error():
    with pytest.raises(ValueError):
        resolved_environment_variables("${")


def test_can_extract_github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url():
    assert github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches(
        "https://github.com/orgs/example-org/projects/1"
    ) == ("example-org", 1, True)
    assert github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches(
        "https://github.com/orgs/example-org/projects/1/some-other-stuff"
    ) == ("example-org", 1, True)
    assert github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches(
        "https://github.com/users/example-username/projects/1"
    ) == ("example-username", 1, False)
    assert github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches(
        "https://github.com/users/example-username/projects/1/some-other-stuff"
    ) == ("example-username", 1, False)


def test_fails_to_extract_github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization():
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
            github_project_owner_name_and_project_number_and_is_project_owner_of_type_organization_from_url_if_matches(
                url
            )


def test_can_validate_at_least_one_type_of_authentication_is_properly_configured():
    fake_user_project_url = "https://github.com/users/fake-username/projects/1"
    fake_configuration_info_with_user_project = ConfigurationInfo(
        project_url=fake_user_project_url,
        personal_access_token="fake_personal_token",
    )
    assert fake_configuration_info_with_user_project.project_url == fake_user_project_url
    assert fake_configuration_info_with_user_project.personal_access_token == "fake_personal_token"

    fake_organization_project_url = "https://github.com/orgs/fake-organization/projects/1"
    fake_configuration_info_with_organization_project = ConfigurationInfo(
        project_url="https://github.com/orgs/fake-organization/projects/1",
        github_app_id="fake_app_id",
        github_app_private_key="fake_private_key",
    )
    assert fake_configuration_info_with_organization_project.project_url == fake_organization_project_url
    assert fake_configuration_info_with_organization_project.github_app_id == "fake_app_id"
    assert fake_configuration_info_with_organization_project.github_app_private_key == "fake_private_key"


def test_fails_on_no_authentication_method_configured():
    with pytest.raises(ValueError, match="A user or an organization authentication method must be configured."):
        ConfigurationInfo(
            project_url="https://github.com/users/fake-username/projects/1",
        )


def test_fails_on_organization_authentication_method_missing_private_key():
    with pytest.raises(ValueError, match="A user or an organization authentication method must be configured."):
        ConfigurationInfo(
            project_url="https://github.com/orgs/fake-organization/projects/1",
            github_app_id="fake_github_app_id",
        )


def test_fails_on_organization_authentication_method_missing_app_id():
    with pytest.raises(ValueError, match="A user or an organization authentication method must be configured."):
        ConfigurationInfo(
            project_url="https://github.com/orgs/fake-organization/projects/1",
            github_app_private_key="fake_github_app_private_key",
        )


def test_can_resolve_value_from_env():
    envvar_name = "FAKE_CHECK_DONE_GITHUB_PROJECT_URL"
    envvar_value = "https://github.com/users/fake-username/projects/1"
    os.environ[envvar_name] = envvar_value
    configuration_info_with_env_value = ConfigurationInfo(
        project_url="${FAKE_CHECK_DONE_GITHUB_PROJECT_URL}",
        personal_access_token="fake_personal_token",
    )
    assert configuration_info_with_env_value.project_url == envvar_value


def test_can_resolve_project_details_from_user_project_url():
    configuration_info = ConfigurationInfo(
        project_url="https://github.com/users/fake-username/projects/1",
        personal_access_token="fake_personal_token",
    )
    assert not configuration_info.is_project_owner_of_type_organization
    assert configuration_info.project_number == 1
    assert configuration_info.project_owner_name == "fake-username"


def test_can_resolve_project_details_from_organization_project_url():
    configuration_info = ConfigurationInfo(
        project_url="https://github.com/orgs/fake-organization-name/projects/1/views/2",
        github_app_id="fake_github_app_id",
        github_app_private_key="fake_github_app_private_key",
    )
    assert configuration_info.is_project_owner_of_type_organization
    assert configuration_info.project_number == 1
    assert configuration_info.project_owner_name == "fake-organization-name"


def test_can_resolve_config_default_path():
    with tempfile.TemporaryDirectory() as temp_folder, change_current_folder(temp_folder):
        current_folder = Path(os.getcwd())
        expected_config_path = (current_folder / CONFIG_BASE_NAME).with_suffix(".yaml")
        expected_config_path.write_text("")
        actual_config_path = default_config_path()
    assert actual_config_path == expected_config_path


def test_can_resolve_default_config_path_with_yml_file_suffix():
    with tempfile.TemporaryDirectory() as temp_folder, change_current_folder(temp_folder):
        current_folder = Path(os.getcwd())
        expected_config_path = (current_folder / CONFIG_BASE_NAME).with_suffix(".yml")
        expected_config_path.write_text("")
        actual_config_path = default_config_path()
    assert actual_config_path == expected_config_path


def test_can_resolve_default_config_path_when_both_yaml_and_yml_config_files_exist():
    with tempfile.TemporaryDirectory() as temp_folder, change_current_folder(temp_folder):
        current_folder = Path(os.getcwd())
        current_folder = Path(os.getcwd())
        expected_config_path_with_prioritized_yaml_suffix = (current_folder / CONFIG_BASE_NAME).with_suffix(".yaml")
        expected_config_path_with_prioritized_yaml_suffix.write_text("")
        another_valid_config_path_with_yml_suffix = (current_folder / CONFIG_BASE_NAME).with_suffix(".yml")
        another_valid_config_path_with_yml_suffix.write_text("")
        actual_config_path = default_config_path()
    assert actual_config_path == expected_config_path_with_prioritized_yaml_suffix


def test_fails_on_missing_default_config_path():
    with (
        tempfile.TemporaryDirectory() as temp_folder,
        change_current_folder(temp_folder),
        pytest.raises(FileNotFoundError),
    ):
        default_config_path()
