# check_done

Check done project items on a GitHub V2 project.

## How to configure

To use check_done for your project, you need to configure the fields in the `yaml` file found in the `configuration` folder.

#### project_url

The project URL as is when viewing your GitHub V2 project. E.g.: `"https://github.com/orgs/my_project_owner_name/projects/1/views/1"`

### For projects belonging to a GitHub user

#### personal_access_token

A personal access token with the permission: `read:project`.

### For projects belonging to a GitHub organization

You need to install the [Siisurit's check_done](https://github.com/apps/siisurit-s-check-done) GitHub app for authentication. Or create your own GitHub app with the following permissions: `read:issues, pull requests, projects`. Then provide the following configuration fields:

#### check_done_github_app_id

Provide the `App ID` that is found in the `General` view under the `About` section of the GitHub app installation instance. Should be a 6+ sequence of numbers.

#### check_done_github_app_private_key

The private key found in the same `General`, under the `Private keys` section. The key should be a private RSA key with PEM format.

### Optional

#### project_status_name_to_check

If you wish to specify a different status/column from the default of last, you can use this configuration field. It will try to match the name you give it, e.g.: If status is named `"✅ Done"` you can give it `"Done"` and it should find it, otherwise a list of available options will be given to you.

### Using environment variables and examples

You can use environment variables for the values in the configuration yaml by starting them with a `$` symbol and wrapping it with curly braces. E.g.: `personal_access_token: ${MY_PERSONAL_ACCESS_TOKEN_ENVVAR}`.

Example configuration for a user owned repository:

```yaml
project_url: "https://github.com/orgs/my_username/projects/1/views/1"
personal_access_token: "ghp_xxxxxxxxxxxxxxxxxxxxxx"
# Since no `project_status_name_to_check` was specified, the checks will apply to the last project status/column.
```

Example configuration for an organization owned repository:

```yaml
project_url: "https://github.com/orgs/my_username/projects/1/views/1"
check_done_github_app_id: "0123456"
check_done_github_app_private_key: "-----BEGIN RSA PRIVATE KEY-----
something_something
-----END RSA PRIVATE KEY-----
"
project_status_name_to_check: "Done" # This will match the name of a project status/column containing "Done" like "✅ Done". The checks will then be applied to this project status/column.
```
