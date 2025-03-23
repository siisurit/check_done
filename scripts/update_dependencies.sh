#!/bin/sh
# Update requirements files and pre-commit hooks to current versions.
set -e
echo "🧱 Updating project"
poetry update
echo "🛠️ Updating pre-commit"
poetry run pre-commit autoupdate
echo "🕸️ Updating GitHub GraphQL schema"
curl --silent --output schema.graphql https://docs.github.com/public/fpt/schema.docs.graphql
echo "🎉 Successfully updated dependencies"
