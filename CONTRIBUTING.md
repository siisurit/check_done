# Contributing

## Project setup

In case you want to play with the source code or contribute changes proceed as follows:

1. Check out the project from GitHub:
   ```bash
   git clone https://github.com/roskakori/check_done.git
   cd check_done
   ```
2. Install [poetry](https://python-poetry.org/).
3. Run the setup script to prepare the poetry environment and pre-commit hooks:
   ```bash
   sh scripts/set_up_project.sh
   ```

## Testing

To run the test suite:

```bash
poetry run pytest
```

To build and browse the coverage report in HTML format:

```bash
sh scripts/test_coverage.sh
open htmlcov/index.html  # macOS only
```

## Testing the GitHub app

In order to test your fork as GitHub app, you need to create your own as described in [Creating GitHub apps](https://docs.github.com/en/apps/creating-github-apps).

When asked for permissions that app requires, specify:

Repository permissions:

- Issues: read-only
- Pull requests: read-only
- Metadata: read-ony (mandatory and enabled automatically)

Organization permissions:

- Projects: read-only

## Coding guidelines

The code throughout uses a natural naming schema avoiding abbreviations, even for local variables and parameters.

Many coding guidelines are automatically enforced (and some even fixed automatically) by the pre-commit hook. If you want to check and clean up the code without performing a commit, run:

```bash
poetry run pre-commit run --all-files
```

## Release cheatsheet

This section only relevant for developers with access to the PyPI project.

To add a new release, first update the `pyproject.toml`:

.. code-block:: toml

```toml
[tool.poetry]
version = "1.x.x"
```

Next build the project and run the tests to ensure everything works:

```bash
poetry build
poetry run pytest
```

Then create a tag in the repository:

```bash
git tag --annotate --message "Tag version 1.x.x" v1.x.x
git push --tags
```

Publish the new version on PyPI:

```bash
poetry publish
```

Finally, add a release based on the tag from above to the [release page](https://github.com/siisurit/check_done/releases).
