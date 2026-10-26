"""Tests for Wayfair OAuth."""

import base64
import json
import time
from unittest.mock import MagicMock

from tap_wayfair.auth import (
    CLIENT_CREDENTIALS_TOKEN_URL,
    EXPIRES_IN_ABSOLUTE_THRESHOLD,
    PORTAL_TOKEN_URL,
    WayfairAuthenticator,
    token_url_for_config,
    uses_portal_oauth,
)


def _stream_with_config(config: dict) -> MagicMock:
    tap = MagicMock()
    tap._config = dict(config)
    stream = MagicMock()
    stream.config = config
    stream._tap = tap
    stream.logger = MagicMock()
    return stream


def _authenticator(stream: MagicMock, auth_endpoint: str) -> WayfairAuthenticator:
    """Construct an authenticator without the SingletonMeta constructor cache."""
    auth = object.__new__(WayfairAuthenticator)
    auth.__init__(stream=stream, auth_endpoint=auth_endpoint)
    return auth


def test_portal_oauth_config_detection_and_token_url():
    assert uses_portal_oauth({"refresh_token": "rt"})
    assert not uses_portal_oauth({"client_id": "a", "client_secret": "b"})
    assert token_url_for_config({"refresh_token": "x"}) == PORTAL_TOKEN_URL
    assert (
        token_url_for_config({"client_id": "a", "client_secret": "b"})
        == CLIENT_CREDENTIALS_TOKEN_URL
    )


def test_oauth_request_body_portal_vs_client_credentials():
    stream = _stream_with_config(
        {
            "client_id": "cid",
            "client_secret": "sec",
            "refresh_token": "rt",
        }
    )
    auth = _authenticator(stream, PORTAL_TOKEN_URL)
    assert auth.oauth_request_body["grant_type"] == "refresh_token"
    assert auth.oauth_request_body["refresh_token"] == "rt"

    stream = _stream_with_config({"client_id": "cid", "client_secret": "sec"})
    auth = _authenticator(stream, CLIENT_CREDENTIALS_TOKEN_URL)
    assert auth.oauth_request_body["grant_type"] == "client_credentials"


def test_is_token_valid_uses_jwt_exp():
    now = int(time.time())
    payload = json.dumps({"exp": now + 3600}).encode()
    segment = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    token = f"hdr.{segment}.sig"
    stream = _stream_with_config(
        {
            "client_id": "cid",
            "client_secret": "sec",
            "refresh_token": "rt",
            "access_token": token,
            "expires_in": 3600,
        }
    )
    auth = _authenticator(stream, PORTAL_TOKEN_URL)
    assert auth.is_token_valid()


def test_ttl_expires_in_normalized_to_absolute():
    stream = _stream_with_config(
        {
            "client_id": "cid",
            "client_secret": "sec",
            "refresh_token": "rt",
            "access_token": "not-a-jwt",
            "expires_in": 3600,
        }
    )
    auth = _authenticator(stream, PORTAL_TOKEN_URL)
    assert auth.is_token_valid()
    exp1 = auth._access_token_expires_at()
    exp2 = auth._access_token_expires_at()
    assert exp1 == exp2
    assert stream._tap._config["expires_in"] >= EXPIRES_IN_ABSOLUTE_THRESHOLD
