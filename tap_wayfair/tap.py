"""Wayfair tap class."""

from typing import List

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th

from tap_wayfair.client import DEFAULT_GRAPHQL_URL
from tap_wayfair.streams import OrdersStream

STREAM_TYPES = [
    OrdersStream,
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
                "Wayfair Dropship Orders GraphQL endpoint. "
                f"Defaults to production ({DEFAULT_GRAPHQL_URL}). "
                "Use https://sandbox.api.wayfair.com/v1/graphql for sandbox credentials."
            ),
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
