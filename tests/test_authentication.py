import pytest
import requests_mock

from check_done.authentication import AuthenticationError, github_app_access_token

_DEMO_INSTALLATION_ID = "installation_id"
_DEMO_ACCESS_TOKEN = "access_token"


def test_github_app_access_token():
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.github.com/orgs/my_organization/installation",
            json={"id": _DEMO_INSTALLATION_ID},
            status_code=200,
        )
        mock.post(
            f"https://api.github.com/app/installations/{_DEMO_INSTALLATION_ID}/access_tokens",
            json={"token": _DEMO_ACCESS_TOKEN},
            status_code=201,
        )
        token = github_app_access_token("my_organization")
    assert token == _DEMO_ACCESS_TOKEN


# TODO: Once the authentication.py module is finalized, implement proper test for function _generated_jwt_token()
# def test_fails_to_generate_jwt_token():
# original_value_private_key = check_done.authentication.GITHUB_APP_PRIVATE_KEY
# try:
#     invalid_private_key_value = "ë"
#     check_done.authentication.GITHUB_APP_PRIVATE_KEY = invalid_private_key_value
#     with pytest.raises(Exception):
#         github_app_access_token("my_organization")
# finally:
#     check_done.authentication.GITHUB_APP_PRIVATE_KEY = original_value_private_key


def test_fails_to_get_installation_id():
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.github.com/orgs/my_organization/installation",
            json={"id": _DEMO_INSTALLATION_ID},
            status_code=400,
        )
        with pytest.raises(AuthenticationError) as exception_info:
            github_app_access_token("my_organization")
    cause_exception = str(exception_info.value.__cause__)
    assert cause_exception.startswith("Could not retrieve installation ID: ")


def test_fails_to_get_access_token():
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.github.com/orgs/my_organization/installation",
            json={"id": _DEMO_INSTALLATION_ID},
            status_code=200,
        )
        mock.post(
            f"https://api.github.com/app/installations/{_DEMO_INSTALLATION_ID}/access_tokens",
            json={"token": _DEMO_ACCESS_TOKEN},
            status_code=400,
        )
        with pytest.raises(AuthenticationError) as exception_info:
            github_app_access_token("my_organization")
    cause_exception = str(exception_info.value.__cause__)
    assert cause_exception.startswith("Could not retrieve access token: ")
