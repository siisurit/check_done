import logging

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.WARNING)
    logger.warning("Hello world!")


if __name__ == "__main__":
    main()
