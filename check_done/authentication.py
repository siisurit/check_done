import time

import jwt
import requests

from check_done.common import GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, AuthenticationError

_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
_SECONDS_PER_MINUTE = 60
_ISSUED_AT = int(time.time())
_EXPIRES_AT = int(time.time()) + (10 * _SECONDS_PER_MINUTE)


def github_app_access_token(organization: str) -> str:
    authentication = _Authentication(organization)
    return authentication.access_token


class _Authentication:
    def __init__(self, organization: str):
        self.organization = organization
        try:
            self.jwt_token = self._generated_jwt_token()
            self.session = requests.Session()
            self.session.headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Accept": "application/vnd.github+json",
            }
            self.installation_id = self._get_installation_id()
            self._access_token = self._get_installation_access_token()
        except Exception as error:
            raise AuthenticationError(f"Cannot authenticate with organization: {organization}") from error
        finally:
            self.session.close()

    @property
    def access_token(self):
        return self._access_token

    @staticmethod
    def _generated_jwt_token() -> str:
        """Generates a JWT token for authentication with GitHub."""
        try:
            payload = {
                "exp": _EXPIRES_AT,
                "iat": _ISSUED_AT,
                "iss": GITHUB_APP_ID,
            }
            return jwt.encode(payload, GITHUB_APP_PRIVATE_KEY, algorithm="RS256")
        except Exception as error:
            raise AuthenticationError(f"Cannot generate JWT token: {error}") from error

    def _get_installation_id(self) -> str:
        """Fetches the installation ID for the organization."""
        headers = self.session.headers
        response = self.session.get(f"https://api.github.com/orgs/{self.organization}/installation", headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        raise AuthenticationError(f"Could not retrieve installation ID: {response.status_code} - {response.text}")

    def _get_installation_access_token(self) -> str:
        """Retrieves the access token using the installation ID."""
        headers = self.session.headers
        response = self.session.post(
            f"https://api.github.com/app/installations/{self.installation_id}/access_tokens", headers=headers
        )
        if response.status_code == 201:
            return response.json().get("token")
        raise AuthenticationError(f"Could not retrieve access token: {response.status_code} - {response.text}")
