from pathlib import Path

import pytest
import yaml

from check_done.command import load_yaml


def test_can_load_valid_yaml(mocker):
    valid_yaml = """
    name:
      - Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mock_open = mocker.mock_open(read_data=valid_yaml)
    mocker.patch("builtins.open", mock_open)
    path = Path("valid.yaml")
    result = load_yaml(path)
    expected_result = {"name": ["Joe Doe"]}
    assert result == expected_result
    mock_open.assert_called_once_with(path)


def test_fails_to_load_configuration_file(mocker):
    mocker.patch("os.path.exists", return_value=False)
    path = Path("non_existent.yaml")
    with pytest.raises(FileNotFoundError, match="Cannot find check_done configuration: "):
        load_yaml(path)


def test_fails_on_invalid_yaml_syntax(mocker):
    invalid_yaml = """
    name: "Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=invalid_yaml))
    path = Path("invalid.yaml")
    with pytest.raises(yaml.YAMLError):
        load_yaml(path)


def test_fails_to_load_empty_yaml_config_file(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))
    mocker.patch("os.path.exists", return_value=True)
    path = Path("empty_config.yaml")
    with pytest.raises(ValueError, match="The check_done configuration is empty. Path: "):
        load_yaml(path)
