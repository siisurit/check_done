#!/bin/sh
set -e
poetry run pytest --cov-reset --cov=check_done tests/ --cov-report html
echo "To view results on linux/MacOS run: firefox htmlcov/index.html &"
