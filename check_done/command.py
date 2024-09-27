import logging

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.WARNING)
    logger.warning("All checks completed! /s")


if __name__ == "__main__":
    main()
