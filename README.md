# check_done

Check_done is a command line tool to check that finished issues and pull requests in a GitHub project board are really done.

## Configuration

To use check_done for your project, you need to configure the fields in the `yaml` file found in the `configuration` folder.

### General settings

#### project_url (required)

The project URL as is when viewing your GitHub V2 project. E.g.: `"https://github.com/orgs/my_project_owner_name/projects/1/views/1"`

#### project_status_name_to_check (optional)

By default, check_done checks all issues and pull requests in the column rightmost / last column of the project board. If you left the default names when creating the GitHub project board, this will be the `"✅ Done"` column.

If you want to check a different column, you can specify its name with this option. For example:

```yaml
project_status_name_to_check = "Done"
```

The name takes the first column that partially matches case sensitively. For example, `"Done"` will also match `"✅ Done"`, but not `"done"`.

If no column matches, the resulting error messages will tell you the exact names of all available columns.

### Authorization settings for a project belonging to a GitHub user

#### personal_access_token

A personal access token with the permission: `read:project`.

Example:

```yaml
project_url: "https://github.com/orgs/my_username/projects/1/views/1"
personal_access_token: "ghp_xxxxxxxxxxxxxxxxxxxxxx"
# Since no `project_status_name_to_check` was specified, the checks will apply to the last project status/column.
```

### Authorization settings for a project belonging to a GitHub organization

Follow the instructions to [Installing a GitHub App from a third party](https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-a-third-party) using the [Siisurit's check_done app](https://github.com/apps/siisurit-s-check-done).

You can also derive your own GitHub app from it with the following permissions:

- `pull requests`
- `projects`
- `read:issues`

Remember the App ID and the app private key. Then add the following settings to the configuration file:

```yaml
check_done_github_app_id = ...  # Typically a decimal number with at least 6 digits
check_done_github_app_private_key = ""-----BEGIN RSA PRIVATE KEY..."
```

Example:

```yaml
project_url: "https://github.com/orgs/my_username/projects/1/views/1"
check_done_github_app_id: "0123456"
check_done_github_app_private_key: "-----BEGIN RSA PRIVATE KEY-----
something_something
-----END RSA PRIVATE KEY-----
"
project_status_name_to_check: "Done" # This will match the name of a project status/column containing "Done" like "✅ Done". The checks will then be applied to this project status/column.
```

### Using environment variables and examples

You can use environment variables for the values in the configuration yaml by starting them with a `$` symbol and wrapping it with curly braces. For example:

```yaml
personal_access_token: ${MY_PERSONAL_ACCESS_TOKEN_ENVVAR}
```
