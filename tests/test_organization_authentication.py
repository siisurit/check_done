import pytest
import requests
import requests_mock
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from check_done.common import HttpBearerAuth
from check_done.info import (
    PROJECT_OWNER_NAME,
)
from check_done.organization_authentication import (
    CHECK_DONE_GITHUB_APP_PRIVATE_KEY,
    AuthenticationError,
    access_token_from_organization,
    generate_jwt_token,
    get_check_done_github_app_installation_id,
)
from tests._common import (
    HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)

_MOCK_INSTALLATION_ID = "mock_installation_id"
_MOCK_ORGANIZATION_NAME = "mock_organization_name"
_MOCK_ACCESS_TOKEN = "mock_access_token"


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_access_token_from_organization():
    access_token_from_organization(PROJECT_OWNER_NAME)


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_mock_access_token_from_organization():
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.github.com/orgs/my_organization/installation",
            json={"id": _MOCK_INSTALLATION_ID},
            status_code=200,
        )
        mock.post(
            f"https://api.github.com/app/installations/{_MOCK_INSTALLATION_ID}/access_tokens",
            json={"token": _MOCK_ACCESS_TOKEN},
            status_code=201,
        )
        token = access_token_from_organization("my_organization")
    assert token == _MOCK_ACCESS_TOKEN


def test_fails_to_generate_jwt_token():
    invalid_private_key_value = ""
    expected_error = "Cannot generate JWT token: Could not parse the provided public key."
    with pytest.raises(Exception, match=expected_error):
        generate_jwt_token(invalid_private_key_value)


def test_can_generate_jwt_token():
    _mock_private_key_for_testing = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _mock_pem_private_key_string_for_testing = _mock_private_key_for_testing.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    generate_jwt_token(_mock_pem_private_key_string_for_testing)


def _session():
    jtw_token = generate_jwt_token(CHECK_DONE_GITHUB_APP_PRIVATE_KEY)
    session = requests.Session()
    session.headers = {"Accept": "application/vnd.github+json"}
    session.auth = HttpBearerAuth(jtw_token)
    return session


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_can_get_check_done_github_app_installation_id():
    session = _session()
    installation_id = get_check_done_github_app_installation_id(session, PROJECT_OWNER_NAME)
    assert isinstance(installation_id, int)


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_fails_to_get_check_done_github_app_installation_id():
    session = _session()
    with pytest.raises(AuthenticationError, match="Could not retrieve installation ID: status=404 "):
        get_check_done_github_app_installation_id(session, "wrong_organization_name")


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_mock_fails_to_get_check_done_github_app_installation_id():
    with requests_mock.Mocker() as mock:
        mock.get(f"https://api.github.com/orgs/{_MOCK_ORGANIZATION_NAME}/installation", status_code=400)
        with pytest.raises(AuthenticationError, match="Could not retrieve installation ID: status=400 "):
            access_token_from_organization(_MOCK_ORGANIZATION_NAME)


@pytest.mark.skipif(
    not HAS_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
    reason=REASON_SHOULD_HAVE_ORGANIZATION_AUTHENTICATION_CONFIGURATION,
)
def test_mock_fails_to_get_access_token_from_check_done_github_app_installation_id():
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.github.com/orgs/my_organization/installation",
            json={"id": _MOCK_INSTALLATION_ID},
            status_code=200,
        )
        mock.post(f"https://api.github.com/app/installations/{_MOCK_INSTALLATION_ID}/access_tokens", status_code=400)
        with pytest.raises(AuthenticationError, match="Could not retrieve access token: status=400 "):
            access_token_from_organization("my_organization")
