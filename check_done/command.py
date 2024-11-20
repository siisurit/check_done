# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import argparse
import logging
import sys
from pathlib import Path

import check_done
from check_done.config import (
    map_from_yaml_file_path,
    resolve_configuration_yaml_file_path_from_root_path,
    resolve_root_repository_path,
    validate_configuration_info_from_yaml_map,
)
from check_done.done_project_items_info import done_project_items_info
from check_done.warning_checks import warnings_for_done_project_items

logger = logging.getLogger(__name__)

_HELP_DESCRIPTION = "Checks that finished issues and pull requests in a GitHub project board column are really done."


class Command:
    """Command interface for check_done"""

    def __init__(self):
        self.args = None

    @staticmethod
    def argument_parser():
        parser = argparse.ArgumentParser(prog="check_done", description=_HELP_DESCRIPTION)
        parser.add_argument("--version", "-v", action="version", version="%(prog)s " + check_done.__version__)
        # TODO#13: Is this implementation of the --root-dir argument proper? If not how to improve it?
        parser.add_argument(
            "--root-dir",
            "-r",
            type=Path,
            default=resolve_root_repository_path(),
            help="Specify a different root directory to check for the YAML config file.",
        )
        return parser

    def apply_arguments(self, arguments=None):
        parser = self.argument_parser()
        self.args = parser.parse_args(arguments)

    def execute(self):
        configuration_yaml_path = resolve_configuration_yaml_file_path_from_root_path(self.args.root_dir)
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


def check_done_command(arguments=None):
    result = 1
    command = Command()
    try:
        command.apply_arguments(arguments)
        command.execute()
        result = 0
    except KeyboardInterrupt:
        logger.error("Interrupted as requested by user.")  # noqa: TRY400
    except Exception:
        logger.exception("Cannot check done project items.")
    return result


def main():
    logging.basicConfig(level=logging.INFO)
    sys.exit(check_done_command())


if __name__ == "__main__":
    main()
