"""Wayfair OAuth for the tap (portal refresh and client credentials)."""

import base64
import json
import time
from typing import Optional

import requests
from hotglue_etl_exceptions import InvalidCredentialsError
from hotglue_singer_sdk.authenticators import OAuthAuthenticator, SingletonMeta
from hotglue_singer_sdk.helpers._util import utc_now

CLIENT_CREDENTIALS_TOKEN_URL = "https://sso.auth.wayfair.com/oauth/token"

PORTAL_TOKEN_URL = (
    "https://partners.wayfair.com/auth/realms/Developer_Portal/"
    "protocol/openid-connect/token"
)

# Hotglue connect often stores OAuth ``expires_in`` as TTL seconds; after refresh we store Unix time.
EXPIRES_IN_ABSOLUTE_THRESHOLD = 1_000_000_000

TOKEN_REFRESH_BUFFER_SECONDS = 120


def uses_portal_oauth(config: dict) -> bool:
    """True when hotglue linked the connection via Developer Portal (has refresh_token)."""
    return bool(config.get("refresh_token"))


def token_url_for_config(config: dict) -> str:
    """Token endpoint for this config: portal OpenID URL vs supplier client-credentials URL."""
    if uses_portal_oauth(config):
        return PORTAL_TOKEN_URL
    return CLIENT_CREDENTIALS_TOKEN_URL


def _utc_now_ts() -> int:
    """Current time as Unix seconds (UTC)."""
    return round(time.time())


class WayfairAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """Obtain and refresh Bearer tokens for Wayfair API calls."""

    def _tap_config(self) -> dict:
        """Live tap config (authoritative for tokens)."""
        return self._tap._config

    @property
    def oauth_request_body(self) -> dict:
        """Body for local token refresh (grant type depends on portal vs M2M config)."""
        config = self._tap_config()
        if uses_portal_oauth(config):
            return {
                "grant_type": "refresh_token",
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "refresh_token": config["refresh_token"],
            }
        return {
            "grant_type": "client_credentials",
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
        }

    def is_token_valid(self) -> bool:
        """True if the current access token can be sent without calling refresh."""
        if uses_portal_oauth(self._tap_config()):
            access_token = self._tap_config().get("access_token")
            if not access_token:
                return False

            expires_at = self._access_token_expires_at()
            if expires_at is None:
                return False

            valid = (expires_at - _utc_now_ts()) >= TOKEN_REFRESH_BUFFER_SECONDS
            if valid:
                self.access_token = access_token
                self.expires_in = expires_at
            return valid

        return super().is_token_valid()

    def _access_token_expires_at(self) -> Optional[int]:
        """Resolve access token expiry as Unix seconds for portal-linked config."""
        config = self._tap_config()
        token = config.get("access_token")
        if isinstance(token, str) and token.count(".") == 2:
            try:
                segment = token.split(".")[1]
                segment += "=" * (-len(segment) % 4)
                payload = json.loads(base64.urlsafe_b64decode(segment))
                exp = payload.get("exp")
                if exp is not None:
                    return int(exp)
            except (ValueError, json.JSONDecodeError, TypeError):
                pass

        expires_in = config.get("expires_in")
        if expires_in is None:
            return None

        expires_in = int(expires_in)
        now = _utc_now_ts()
        if expires_in >= EXPIRES_IN_ABSOLUTE_THRESHOLD:
            return expires_in

        absolute = now + expires_in
        config["expires_in"] = absolute
        return absolute

    def update_access_token(self) -> None:
        """Refresh via Hotglue accesstoken API when configured, else local OAuth."""
        try:
            super().update_access_token()
        except RuntimeError as ex:
            if "Missing required env vars for Hotglue access token" not in str(ex):
                raise
            self.logger.warning(
                "Hotglue accesstoken API not configured; falling back to local "
                "Wayfair OAuth refresh."
            )
            self.update_access_token_locally()

    def update_access_token_locally(self) -> None:
        """POST to Wayfair token URL; portal uses form body, M2M uses JSON."""
        request_time = utc_now()
        body = self.oauth_request_body
        if uses_portal_oauth(self._tap_config()):
            token_response = requests.post(
                self.auth_endpoint,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=300,
            )
        else:
            token_response = requests.post(
                self.auth_endpoint,
                json=body,
                timeout=300,
            )
        try:
            token_response.raise_for_status()
            self.logger.info("OAuth authorization attempt was successful.")
        except requests.HTTPError as ex:
            raise InvalidCredentialsError(
                f"Wayfair OAuth failed ({token_response.status_code}): "
                f"{token_response.text}. {ex}"
            )

        token_json = token_response.json()
        self.access_token = token_json["access_token"]
        self.expires_in = int(token_json.get("expires_in", 3600)) + int(
            request_time.timestamp()
        )
        self.last_refreshed = request_time

        config = self._tap_config()
        config["access_token"] = token_json["access_token"]
        config["expires_in"] = self.expires_in
        new_refresh = token_json.get("refresh_token")
        if new_refresh:
            config["refresh_token"] = new_refresh

        if self._tap.config_file is not None:
            with open(self._tap.config_file, "w") as outfile:
                json.dump(config, outfile, indent=4)

    @classmethod
    def create_for_stream(cls, stream) -> "WayfairAuthenticator":
        """Create a stream-bound authenticator with the correct token URL for config."""
        return cls(
            stream=stream,
            auth_endpoint=token_url_for_config(stream._tap._config),
        )
