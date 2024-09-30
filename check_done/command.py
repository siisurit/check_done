import logging
import sys
from pathlib import Path

from check_done.common import checked_config, load_yaml

logger = logging.getLogger(__name__)
_CONFIG_PATH = Path(__file__).parent.parent / "data" / ".check_done.yaml"


def check_done_command():
    result = 1
    try:
        config_file = load_yaml(_CONFIG_PATH)
        checked_config(config_file)
        result = 0
    except KeyboardInterrupt:
        logging.exception("Interrupted as requested by user.")
    except Exception:
        logging.exception()
    return result


def main():
    logging.basicConfig(level=logging.WARNING)
    sys.exit(check_done_command())


if __name__ == "__main__":
    main()
