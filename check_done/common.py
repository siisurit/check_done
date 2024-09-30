import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
_ENVVAR_GITHUB_API_KEY = "GITHUB_API_KEY"
_GITHUB_API_KEY = os.environ.get(_ENVVAR_GITHUB_API_KEY)


class _BoardInfo(BaseModel):
    url: str
    api_key: str
    trackers: list[str]


class _ConfigInfo(BaseModel):
    board: _BoardInfo


def load_yaml(config_path: Path) -> dict:
    try:
        with open(config_path) as config_file:
            result = yaml.safe_load(config_file)
            if result is None:
                raise ValueError(f"The check_done configuration is empty. Path: {config_path}")
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Cannot find check_done configuration: {config_path}") from error
    return result


def checked_config(config_file: dict) -> _ConfigInfo:
    result = _ConfigInfo(**config_file)
    result.board.api_key = _GITHUB_API_KEY
    return result
