"""Wayfair OAuth2 authentication."""

import requests

from hotglue_singer_sdk.authenticators import OAuthAuthenticator, SingletonMeta
from hotglue_singer_sdk.helpers._util import utc_now

TOKEN_URL = "https://sso.auth.wayfair.com/oauth/token"


class WayfairAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """OAuth2 client-credentials authenticator for the Wayfair API."""

    @property
    def oauth_request_body(self) -> dict:
        return {
            "grant_type": "client_credentials",
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
        }

    def update_access_token_locally(self) -> None:
        """Fetch a token using a JSON body (Wayfair does not accept form-encoded)."""
        request_time = utc_now()
        token_response = requests.post(
            self.auth_endpoint,
            json=self.oauth_request_body,
        )
        try:
            token_response.raise_for_status()
            self.logger.info("OAuth authorization attempt was successful.")
        except Exception as ex:
            raise RuntimeError(
                f"Failed OAuth login, response was '{token_response.text}'. {ex}"
            )
        token_json = token_response.json()
        self.access_token = token_json["access_token"]
        self.expires_in = token_json.get("expires_in", self._default_expiration) + int(
            request_time.timestamp()
        )
        self.last_refreshed = request_time

    @classmethod
    def create_for_stream(cls, stream) -> "WayfairAuthenticator":
        return cls(stream=stream, auth_endpoint=TOKEN_URL)
