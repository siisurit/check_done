#!/bin/sh
set -ex
git config --local core.commentChar ";"  # Allow commit messages to start with hash (#).
uv sync
uv run pre-commit install --install-hooks
curl --silent --output schema.graphql https://docs.github.com/public/fpt/schema.docs.graphql
