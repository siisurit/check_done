[![PyPI](https://img.shields.io/pypi/v/check_done)](https://pypi.org/project/pygount/)
[![Python Versions](https://img.shields.io/pypi/pyversions/check_done.svg)](https://www.python.org/downloads/)
[![Build Status](https://github.com/siisurit/check_done/actions/workflows/build.yml/badge.svg)](https://github.com/roskakori/pygount/actions/workflows/build.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/siisurit/check_done)](https://opensource.org/licenses/BSD-3-Clause)

# check_done

Check_done is a command line tool to check that GitHub issues and pull requests in a project board with a status of "Done" are really done.

For each issue or pull request in the "Done" column of the project board, it checks that:

- It is closed.
- It has an assignee.
- It is assigned to a milestone.
- All tasks are completed (list with checkboxes in the description).

For pull requests, it additionally checks if they reference an issue.

This ensures a consistent quality on done issues and pull requests, and helps to notice if they were accidentally deemed to be done too early.

## Installation

In order to gain access to your project board, issues, and pull requests, check_done needs to be authorized. The exact way to do that depends on whether your project belongs to a single user or a GitHub organization.

For user projects, [create a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) with the permission: `read:project`.

For organization projects, follow the instructions to [Installing a GitHub App from a third party](https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-a-third-party) using the [Check_done app](https://github.com/apps/check-done-app).

Remember the **app ID** and **private key** of the installed app.

## Configuration

Check_done can be configured by having a `.check_done.yaml` in your current directory, or any of the directories above.

Alternatively, you can specify a specific location, for example:

```bash
check_done --config some/path/.check_done.yaml
```

### Project and authentication

A minimum configuration requires the URL of the project board and the authentication information from the installation.

The project URL can be seen in the web browser's URL bar when visiting the project board, for example: `https://github.com/users/my-username/projects/1/views/1` (for a user) or `https://github.com/my-organization/projects/1/` (for an organization).

An example of a user project could look like this:

```yaml
project_url: "https://github.com/users/my-username/projects/1/views/1"
personal_access_token: "ghp_xxxxxxxxxxxxxxxxxxxxxx"
```

For an organization project:

```yaml
project_url: "https://github.com/orgs/my_username/projects/1/views/1"
check_done_github_app_id: "1234567"
check_done_github_app_private_key: "-----BEGIN RSA PRIVATE KEY-----
something_something
-----END RSA PRIVATE KEY-----
"
```

In order to avoid having to commit tokens and keys into your repository, you can use environment variables for the values in the configuration YAML by starting them with a `$` symbol and wrapping them with curly braces. For example:

```yaml
personal_access_token: ${MY_PERSONAL_ACCESS_TOKEN_ENVVAR}
```

### Changing the board status column to check

By default, check_done checks all issues and pull requests in the column rightmost/last column of the project board. If you left the default names when creating the GitHub project board, this would be the `"✅ Done"` column.

If you want to check a different column, you can specify its name with this option. For example:

```yaml
project_status_name_to_check = "Done"
```

The name takes the first column that partially matches the case sensitivity. For example, `"Done"` will also match `"✅ Done"`, but not `"done"`.

If no column matches, the resulting error messages will tell you the exact names of all available columns.
