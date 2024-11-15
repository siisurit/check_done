# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import argparse
import logging
import sys

import check_done
from check_done.done_project_items_info import done_project_items_info
from check_done.warning_checks import warnings_for_done_project_items

logger = logging.getLogger(__name__)

_HELP_DESCRIPTION = (
    'Analyzes for consistency a GitHub project state/column that is meant to represent "done" project items.'
)


class Command:
    """Command interface for check_done"""

    @staticmethod
    def argument_parser():
        parser = argparse.ArgumentParser(prog="check_done", description=_HELP_DESCRIPTION)
        parser.add_argument("--version", action="version", version="%(prog)s " + check_done.__version__)
        return parser

    def apply_arguments(self, arguments=None):
        parser = self.argument_parser()
        parser.parse_args(arguments)

    @staticmethod
    def execute():
        done_project_items = done_project_items_info()
        warnings = warnings_for_done_project_items(done_project_items)
        if len(warnings) == 0:
            logger.info("check_done found no problems with the items in the specified project state/column.")
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
