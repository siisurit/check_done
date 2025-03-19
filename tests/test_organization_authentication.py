# Copyright (C) 2024-2025 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import pytest
import requests
import requests_mock
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from check_done.graphql import HttpBearerAuth
from check_done.organization_authentication import (
    AuthenticationError,
    generate_jwt_token,
    resolve_github_app_installation_id,
    resolve_organization_access_token,
)
from tests._common import (
    DEMO_CHECK_DONE_GITHUB_APP_ID,
    DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY,
    DEMO_CHECK_DONE_PROJECT_OWNER_NAME,
    HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)

_DUMMY_GITHUB_APP_ID = "dummy_github_app_id"
_DUMMY_ORGANIZATION_NAME = "dummy_organization_name"
_DUMMY_ACCESS_TOKEN = "dummy_access_token"
_FAKE_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=1024)
_FAKE_PEM_PRIVATE_KEY = _FAKE_PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode("utf-8")


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_resolve_organization_access_token():
    resolve_organization_access_token(
        DEMO_CHECK_DONE_PROJECT_OWNER_NAME, DEMO_CHECK_DONE_GITHUB_APP_ID, DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY
    )


def test_can_resolve_organization_access_token_from_bad_requests():
    with requests_mock.Mocker() as mock:
        mock.get(
            f"https://api.github.com/orgs/{_DUMMY_ORGANIZATION_NAME}/installation",
            json={"id": _DUMMY_GITHUB_APP_ID},
            status_code=200,
        )
        mock.post(
            f"https://api.github.com/app/installations/{_DUMMY_GITHUB_APP_ID}/access_tokens",
            json={"token": _DUMMY_ACCESS_TOKEN},
            status_code=201,
        )
        token = resolve_organization_access_token(_DUMMY_ORGANIZATION_NAME, _DUMMY_GITHUB_APP_ID, _FAKE_PEM_PRIVATE_KEY)
    assert token == _DUMMY_ACCESS_TOKEN


def test_fails_to_generate_jwt_token():
    invalid_private_key_value = ""
    with pytest.raises(Exception, match="Cannot generate JWT token: Could not parse the provided public key."):
        generate_jwt_token(_DUMMY_GITHUB_APP_ID, invalid_private_key_value)


def test_can_generate_jwt_token():
    fake_jwt_token = generate_jwt_token(_DUMMY_GITHUB_APP_ID, _FAKE_PEM_PRIVATE_KEY)
    assert isinstance(fake_jwt_token, str)


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_can_resolve_github_app_installation_id():
    session = _session()
    fake_installation_id = resolve_github_app_installation_id(session, DEMO_CHECK_DONE_PROJECT_OWNER_NAME)
    assert isinstance(fake_installation_id, int)


@pytest.mark.skipif(
    not HAS_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
    reason=REASON_SHOULD_HAVE_DEMO_CHECK_DONE_ORGANIZATION_PROJECT_CONFIGURED,
)
def test_fails_to_resolve_github_app_installation_id():
    session = _session()
    with pytest.raises(AuthenticationError, match="Could not retrieve installation ID: status=404 "):
        resolve_github_app_installation_id(session, _DUMMY_ORGANIZATION_NAME)


def test_fails_to_resolve_github_app_installation_id_from_bad_request():
    with requests_mock.Mocker() as mock:
        mock.get(f"https://api.github.com/orgs/{_DUMMY_ORGANIZATION_NAME}/installation", status_code=400)
        with pytest.raises(AuthenticationError, match="Could not retrieve installation ID: status=400 "):
            resolve_organization_access_token(_DUMMY_ORGANIZATION_NAME, _DUMMY_GITHUB_APP_ID, _FAKE_PEM_PRIVATE_KEY)


def test_fails_to_resolve_access_token_from_github_app_installation_id():
    with requests_mock.Mocker() as mock:
        mock.get(
            f"https://api.github.com/orgs/{_DUMMY_ORGANIZATION_NAME}/installation",
            json={"id": _DUMMY_GITHUB_APP_ID},
            status_code=200,
        )
        mock.post(f"https://api.github.com/app/installations/{_DUMMY_GITHUB_APP_ID}/access_tokens", status_code=400)
        with pytest.raises(AuthenticationError, match="Could not retrieve access token: status=400 "):
            resolve_organization_access_token(_DUMMY_ORGANIZATION_NAME, _DUMMY_GITHUB_APP_ID, _FAKE_PEM_PRIVATE_KEY)


def _session():
    assert DEMO_CHECK_DONE_GITHUB_APP_ID is not None
    assert DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY is not None
    jwt_token = generate_jwt_token(DEMO_CHECK_DONE_GITHUB_APP_ID, DEMO_CHECK_DONE_GITHUB_APP_PRIVATE_KEY)
    session = requests.Session()
    session.headers = {"Accept": "application/vnd.github+json"}
    session.auth = HttpBearerAuth(jwt_token)
    return session
