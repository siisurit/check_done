import logging
import sys

from check_done.authentication import github_app_access_token
from check_done.common import config_info, github_organization_name_and_project_number_from_url_if_matches

logger = logging.getLogger(__name__)


def check_done_command():
    result = 1
    try:
        board_url = config_info().board.url
        organization_name, _ = github_organization_name_and_project_number_from_url_if_matches(board_url)
        github_app_access_token(organization_name)
        result = 0
    except KeyboardInterrupt:
        logging.exception("Interrupted as requested by user.")
    except Exception:
        logging.exception("Cannot check done issues.")
    return result


def main():
    logging.basicConfig(level=logging.WARNING)
    sys.exit(check_done_command())


if __name__ == "__main__":
    main()
