import pytest
import yaml

from check_done.command import load_yaml_config


def test_can_load_valid_yaml(mocker):
    valid_yaml = """
    name:
      - Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mock_open = mocker.mock_open(read_data=valid_yaml)
    mocker.patch("builtins.open", mock_open)
    result = load_yaml_config("valid.yaml")
    expected_result = {"name": ["Joe Doe"]}
    assert result == expected_result
    mock_open.assert_called_once_with("valid.yaml", "r")


def test_fails_to_load_configuration_file(mocker):
    mocker.patch("os.path.exists", return_value=False)
    with pytest.raises(FileNotFoundError, match="Cannot find check_done configuration: "):
        load_yaml_config("non_existent.yaml")


def test_fails_on_invalid_yaml_syntax(mocker):
    invalid_yaml = """
    name: "Joe Doe
    """
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open(read_data=invalid_yaml))
    with pytest.raises(yaml.YAMLError):
        load_yaml_config("invalid.yaml")


def test_fails_to_load_empty_yaml_config_file(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))
    mocker.patch("os.path.exists", return_value=True)
    with pytest.raises(ValueError, match="The check_done configuration is empty. Path: "):
        load_yaml_config("empty_config.yaml")
