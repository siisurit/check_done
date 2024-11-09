import time

import jwt
import requests
from requests import Session

from check_done.common import (
    AuthenticationError,
    HttpBearerAuth,
    configuration_info,
)

CHECK_DONE_GITHUB_APP_ID = configuration_info().check_done_github_app_id
CHECK_DONE_GITHUB_APP_PRIVATE_KEY = configuration_info().check_done_github_app_private_key
_SECONDS_PER_MINUTE = 60
_ISSUED_AT = int(time.time())
_EXPIRES_AT = int(time.time()) + (10 * _SECONDS_PER_MINUTE)


def access_token_from_organization(organization_name: str) -> str:
    """
    Generates the necessary access token for an organization from the installed GitHub app instance in said organization
    """
    jtw_token = generate_jwt_token(CHECK_DONE_GITHUB_APP_PRIVATE_KEY)
    session = requests.Session()
    session.headers = {"Accept": "application/vnd.github+json"}
    session.auth = HttpBearerAuth(jtw_token)
    try:
        check_done_github_app_installation_id = get_check_done_github_app_installation_id(session, organization_name)
        result = get_access_token_from_check_done_github_app_installation_id(
            session, check_done_github_app_installation_id
        )
    except Exception as error:
        raise AuthenticationError(f"Cannot generate JWT token: {error}") from error
    return result


def generate_jwt_token(private_key: str) -> str:
    """Generates a JWT token for authentication with GitHub."""
    try:
        payload = {
            "exp": _EXPIRES_AT,
            "iat": _ISSUED_AT,
            "iss": CHECK_DONE_GITHUB_APP_ID,
        }
        return jwt.encode(payload, private_key, algorithm="RS256")
    except Exception as error:
        raise AuthenticationError(f"Cannot generate JWT token: {error}") from error


def get_check_done_github_app_installation_id(session: Session, organization_name: str) -> str:
    """Fetches the installation ID for the organization."""
    response = session.get(f"https://api.github.com/orgs/{organization_name}/installation")

    if response.status_code == 200 and response.json().get("id") is not None:
        return response.json().get("id")
    raise AuthenticationError(
        f"Could not retrieve installation ID: status={response.status_code} - response_text={response.text}"
    )


def get_access_token_from_check_done_github_app_installation_id(session: Session, installation_id: str) -> str:
    """Retrieves the access token using the installation ID."""
    response = session.post(f"https://api.github.com/app/installations/{installation_id}/access_tokens")
    if response.status_code == 201 and response.json().get("token") is not None:
        return response.json().get("token")
    raise AuthenticationError(
        f"Could not retrieve access token: status={response.status_code} - response_text={response.text}"
    )
