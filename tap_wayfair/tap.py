"""Wayfair tap class."""

from typing import List

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th

from tap_wayfair.client import DEFAULT_CATALOG_API_BASE, DEFAULT_GRAPHQL_URL
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
                "Wayfair API URL. Orders use the full GraphQL endpoint "
                f"(default: {DEFAULT_GRAPHQL_URL}). "
                "Product catalog streams use this as the API base URL "
                f"(default: {DEFAULT_CATALOG_API_BASE}) with the stream path appended."
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
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return the list of streams supported by this tap."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapWayfair.cli()
