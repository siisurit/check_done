# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import argparse
import logging
import sys
from pathlib import Path

import check_done
from check_done.config import (
    CONFIG_BASE_NAME,
    default_config_path,
    map_from_yaml_file_path,
    validate_configuration_info_from_yaml_map,
)
from check_done.done_project_items_info import done_project_items_info
from check_done.warning_checks import warnings_for_done_project_items

logger = logging.getLogger(__name__)

_HELP_DESCRIPTION = (
    'Check that GitHub issues and pull requests in a project board with a status of "Done" are really done.'
)


def check_done_command(arguments=None) -> int:
    result = 1
    try:
        execute(arguments)
        result = 0
    except KeyboardInterrupt:
        logger.error("Interrupted as requested by user.")  # noqa: TRY400
    except Exception:
        logger.exception("Cannot check done project items.")
    return result


def execute(arguments=None):
    parser = _argument_parser()
    args = parser.parse_args(arguments)
    configuration_yaml_path = args.config or default_config_path()
    yaml_map = map_from_yaml_file_path(configuration_yaml_path)
    configuration_info = validate_configuration_info_from_yaml_map(yaml_map)
    done_project_items = done_project_items_info(configuration_info)
    done_project_items_count = len(done_project_items)
    if done_project_items_count == 0:
        logger.info("Nothing to check. Project has no items in the selected project status.")
    else:
        warnings = warnings_for_done_project_items(done_project_items)
        if len(warnings) == 0:
            logger.info(
                f"All project items are correct, "
                f"{done_project_items_count!s} checked in the selected project status. "
            )
        else:
            for warning in warnings:
                logger.warning(warning)


def _argument_parser():
    parser = argparse.ArgumentParser(prog="check_done", description=_HELP_DESCRIPTION)
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help=(
            f"Path to configuration file with project URL, authentication details, and possibly other options; "
            f"default: {CONFIG_BASE_NAME}.yaml in the current working directory or any of the above."
        ),
    )
    parser.add_argument("--version", "-v", action="version", version="%(prog)s " + check_done.__version__)
    return parser


def main():  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    sys.exit(check_done_command())


if __name__ == "__main__":  # pragma: no cover
    main()
