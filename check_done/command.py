import logging
import sys

from check_done.checks import check_done_issues_for_warnings

logger = logging.getLogger(__name__)


def check_done_command():
    result = 1
    try:
        warnings = check_done_issues_for_warnings()
        if len(warnings) == 0:
            logger.info("No warnings found.")
            result = 0
        else:
            for warning in warnings:
                logger.warning(warning)
    except KeyboardInterrupt:
        logger.exception("Interrupted as requested by user.")
    except Exception:
        logger.exception("Cannot check done issues.")
    return result


def main():
    logging.basicConfig(level=logging.INFO)
    sys.exit(check_done_command())


if __name__ == "__main__":
    main()
