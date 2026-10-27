"""Wayfair tap class."""

from typing import Any, List, Optional, Tuple, Type

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.authenticators import OAuthAuthenticator

from tap_wayfair.auth import CLIENT_CREDENTIALS_TOKEN_URL, WayfairAuthenticator
from tap_wayfair.client import (
    DEFAULT_CATALOG_API_BASE,
    DEFAULT_GRAPHQL_URL,
    SANDBOX_CATALOG_API_BASE,
    SANDBOX_GRAPHQL_URL,
)
from tap_wayfair.streams import (
    OrdersStream,
    TaxonomyAttributesStream,
    TaxonomyCategoriesStream,
)

STREAM_TYPES = [
    OrdersStream,
    TaxonomyCategoriesStream,
    TaxonomyAttributesStream,
]


class TapWayfair(Tap):
    """Wayfair tap class."""

    name = "tap-wayfair"

    config_jsonschema = th.PropertiesList(
        th.Property("client_id", th.StringType, required=True),
        th.Property("client_secret", th.StringType, required=True),
        th.Property(
            "api_url",
            th.StringType,
            description=(
                "Orders GraphQL endpoint URL "
                f"(default: {DEFAULT_GRAPHQL_URL}; sandbox: {SANDBOX_GRAPHQL_URL} when "
                "`is_sandbox` is true)."
            ),
        ),
        th.Property(
            "catalog_api_url",
            th.StringType,
            description=(
                "Product catalog API base URL; the catalog GraphQL path is appended "
                f"(default: {DEFAULT_CATALOG_API_BASE})."
            ),
        ),
        th.Property(
            "brand",
            th.StringType,
            description="Market context brand for taxonomy streams.",
        ),
        th.Property(
            "country",
            th.StringType,
            description="Market context country for taxonomy streams.",
        ),
        th.Property(
            "locale",
            th.StringType,
            description="Market context locale for taxonomy streams.",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest order poDate to sync",
        ),
        th.Property(
            "access_token",
            th.StringType,
            description="OAuth access token (set by hotglue after portal connect).",
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            description="OAuth refresh token (Developer Portal / hotglue connect).",
        ),
        th.Property(
            "expires_in",
            th.IntegerType,
            description="Access token TTL seconds or Unix expiry after refresh.",
        ),
        th.Property(
            "is_sandbox",
            th.BooleanType,
            description=(
                f"When true, use sandbox orders ({SANDBOX_GRAPHQL_URL}) and catalog "
                f"({SANDBOX_CATALOG_API_BASE}) unless api_url or catalog_api_url is set."
            ),
        ),
    ).to_dict()

    @classmethod
    def access_token_support(
        cls, _connector: Optional[Any] = None
    ) -> Tuple[Type[OAuthAuthenticator], str]:
        """Enable Hotglue ``--access-token`` and job accesstoken API refresh."""
        return WayfairAuthenticator, CLIENT_CREDENTIALS_TOKEN_URL

    def discover_streams(self) -> List[Stream]:
        """Return the list of streams supported by this tap."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapWayfair.cli()
