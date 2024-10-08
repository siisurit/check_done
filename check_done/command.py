import logging
import sys

from check_done.done_issues_info.done_issues_info import done_issues_info

logger = logging.getLogger(__name__)


def check_done_command():
    result = 1
    try:
        done_issues_info()
        result = 0
    except KeyboardInterrupt:
        logging.exception("Interrupted as requested by user.")
    except Exception:
        logging.exception("Cannot check done issues.")
    return result


def main():
    logging.basicConfig(level=logging.INFO)
    sys.exit(check_done_command())


if __name__ == "__main__":
    main()
