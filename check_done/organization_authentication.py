# Copyright (C) 2024 by Siisurit e.U., Austria.
# All rights reserved. Distributed under the MIT License.
import time

import jwt
import requests
from requests import Session

from check_done.graphql import HttpBearerAuth

_SECONDS_PER_MINUTE = 60
_ISSUED_AT = int(time.time())
_EXPIRES_AT = int(time.time()) + (10 * _SECONDS_PER_MINUTE)


class AuthenticationError(Exception):
    """Error raised due to failed JWT authentication process."""


def resolve_organization_access_token(organization_name: str, github_app_id: str, github_app_private_key: str) -> str:
    """
    Generates the necessary access token for an organization from the installed GitHub app instance in said organization
    """
    jwt_token = generate_jwt_token(github_app_id, github_app_private_key)
    session = requests.Session()
    session.headers = {"Accept": "application/vnd.github+json"}
    session.auth = HttpBearerAuth(jwt_token)
    try:
        github_app_installation_id = resolve_github_app_installation_id(session, organization_name)
        result = resolve_access_token_from_github_app_installation_id(session, github_app_installation_id)
    except Exception as error:
        raise AuthenticationError(
            f"Cannot resolve organization access token from JWT authentication process: {error}"
        ) from error
    return result


def generate_jwt_token(github_app_id: str, github_app_private_key: str) -> str:
    """Generates a JWT token for authentication with GitHub."""
    try:
        payload = {
            "exp": _EXPIRES_AT,
            "iat": _ISSUED_AT,
            "iss": github_app_id,
        }
        return jwt.encode(payload, github_app_private_key, algorithm="RS256")
    except Exception as error:
        raise AuthenticationError(f"Cannot generate JWT token: {error}") from error


def resolve_github_app_installation_id(session: Session, organization_name: str) -> str:
    """Fetches the installation ID for the organization."""
    response = session.get(f"https://api.github.com/orgs/{organization_name}/installation")

    if response.status_code == 200 and response.json().get("id") is not None:
        return response.json().get("id")
    raise AuthenticationError(
        f"Could not retrieve installation ID: status={response.status_code} - response_text={response.text}"
    )


def resolve_access_token_from_github_app_installation_id(session: Session, installation_id: str) -> str:
    """Retrieves the access token using the installation ID."""
    response = session.post(f"https://api.github.com/app/installations/{installation_id}/access_tokens")
    if response.status_code == 201 and response.json().get("token") is not None:
        return response.json().get("token")
    raise AuthenticationError(
        f"Could not retrieve access token: status={response.status_code} - response_text={response.text}"
    )
