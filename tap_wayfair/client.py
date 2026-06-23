"""GraphQL client handling for Wayfair streams."""

from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import pendulum
import requests
from hotglue_singer_sdk.exceptions import FatalAPIError
from hotglue_singer_sdk.helpers.jsonpath import extract_jsonpath
from hotglue_singer_sdk.streams import GraphQLStream
from memoization import cached

from tap_wayfair.auth import WayfairAuthenticator

DEFAULT_GRAPHQL_URL = "https://api.wayfair.com/v1/graphql"
DATETIME_FIELDS = (
    "poDate",
    "estimatedShipDate",
    "scheduledDeliveryDate",
    "twoDayGuaranteeDeliveryDeadline",
    "startDate",
    "endDate",
)


class WayfairStream(GraphQLStream):
    """Base stream for the Wayfair Dropship Orders GraphQL API."""

    primary_keys = ["id"]
    replication_key = "poDate"
    limit = 100
    _pagination_skip_po_number: Optional[str] = None

    @property
    def url_base(self) -> str:
        """Return the configured GraphQL endpoint URL."""
        return self.config.get("api_url", DEFAULT_GRAPHQL_URL)

    @property
    @cached
    def authenticator(self) -> WayfairAuthenticator:
        return WayfairAuthenticator.create_for_stream(self)

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Build GraphQL variables for limit, sort order, and incremental/pagination filters."""
        params: Dict[str, Any] = {"limit": self.limit, "sortOrder": "ASC"}
        self._pagination_skip_po_number = None

        if next_page_token:
            if isinstance(next_page_token, dict):
                params["fromDate"] = next_page_token["fromDate"]
                self._pagination_skip_po_number = next_page_token.get("lastPoNumber")
            else:
                params["fromDate"] = next_page_token
        elif self.replication_key:
            start_date = self.get_starting_time(context, is_inclusive=False)
            if start_date:
                params["fromDate"] = self._format_from_date(start_date)

        return params

    @staticmethod
    def _format_from_date(value: datetime) -> str:
        """Format a datetime for the Wayfair API fromDate filter."""
        parsed = pendulum.instance(value)
        return parsed.format("YYYY-MM-DD HH:mm:ss.SSSSSS Z")

    @staticmethod
    def _normalize_datetime(value: Optional[str]) -> Optional[str]:
        """Convert a Wayfair datetime string to ISO 8601 for Singer state."""
        if not value:
            return value
        return pendulum.parse(value, strict=False).isoformat()

    def _normalize_record_datetimes(self, record: dict) -> dict:
        """Normalize all known datetime fields on an order record and nested objects."""
        for field in DATETIME_FIELDS:
            if field in record:
                record[field] = self._normalize_datetime(record[field])
        for product in record.get("products") or []:
            for field in DATETIME_FIELDS:
                if field in product:
                    product[field] = self._normalize_datetime(product[field])
            event = product.get("event")
            if event:
                for field in DATETIME_FIELDS:
                    if field in event:
                        event[field] = self._normalize_datetime(event[field])
        return record

    def post_process(self, row: dict, context: Optional[dict] = None) -> Optional[dict]:
        return self._normalize_record_datetimes(row)

    def get_next_page_token(
        self,
        response: requests.Response,
        previous_token: Optional[Any],
    ) -> Optional[Any]:
        """Return a fromDate/poNumber token when a full page of orders was returned."""
        records = list(extract_jsonpath(self.records_jsonpath, input=response.json()))
        if len(records) < self.limit:
            return None
        last = records[-1]
        return {"fromDate": last["poDate"], "lastPoNumber": last["poNumber"]}

    def validate_response(self, response: requests.Response) -> None:
        """Raise on HTTP errors and GraphQL error payloads."""
        super().validate_response(response)
        try:
            body = response.json()
        except ValueError as ex:
            raise FatalAPIError(f"Wayfair invalid JSON response: {response.text}") from ex
        gql_errors = body.get("errors")
        if gql_errors:
            msg = "; ".join(error.get("message", "") for error in gql_errors)
            raise FatalAPIError(f"Wayfair GraphQL error: {msg}")

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Yield order records, skipping the pagination overlap at inclusive fromDate boundaries."""
        for record in extract_jsonpath(self.records_jsonpath, input=response.json()):
            if (
                self._pagination_skip_po_number
                and record.get("poNumber") == self._pagination_skip_po_number
            ):
                self._pagination_skip_po_number = None
                continue
            yield record
