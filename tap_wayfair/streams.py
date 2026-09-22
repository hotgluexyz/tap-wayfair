"""Stream type classes for tap-wayfair."""

from typing import Any, Dict, Iterable, Optional

import requests
from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.helpers._classproperty import classproperty
from hotglue_singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_wayfair.client import (
    CATALOG_GRAPHQL_PATH,
    DEFAULT_CATALOG_API_BASE,
    DEFAULT_MARKET_CONTEXT,
    WayfairStream,
)

ADDRESS_SCHEMA = th.ObjectType(
    th.Property("name", th.StringType),
    th.Property("address1", th.StringType),
    th.Property("address2", th.StringType),
    th.Property("address3", th.StringType),
    th.Property("city", th.StringType),
    th.Property("state", th.StringType),
    th.Property("country", th.StringType),
    th.Property("postalCode", th.StringType),
    th.Property("phoneNumber", th.StringType),
)

SALES_EVENT_SCHEMA = th.ObjectType(
    th.Property("id", th.StringType),
    th.Property("type", th.StringType),
    th.Property("name", th.StringType),
    th.Property("startDate", th.DateTimeType),
    th.Property("endDate", th.DateTimeType),
)

PRODUCT_SCHEMA = th.ObjectType(
    th.Property("partNumber", th.StringType),
    th.Property("quantity", th.StringType),
    th.Property("price", th.NumberType),
    th.Property("pieceCount", th.IntegerType),
    th.Property("totalCost", th.NumberType),
    th.Property("name", th.StringType),
    th.Property("weight", th.NumberType),
    th.Property("totalWeight", th.NumberType),
    th.Property("estShipDate", th.StringType),
    th.Property("fillDate", th.StringType),
    th.Property("sku", th.StringType),
    th.Property("isCancelled", th.BooleanType),
    th.Property("isTscaCompliant", th.BooleanType),
    th.Property("twoDayGuaranteeDeliveryDeadline", th.DateTimeType),
    th.Property("customComment", th.StringType),
    th.Property("event", SALES_EVENT_SCHEMA),
)

VALUE_FORMAT_SCHEMA = th.ObjectType(
    th.Property("canValueBeCustomized", th.BooleanType),
    th.Property("canValueBeSetToUnavailable", th.BooleanType),
    th.Property("canValueBeSetToNotApplicable", th.BooleanType),
    th.Property("datatype", th.StringType),
)

ATTRIBUTE_VALUE_SCHEMA = th.ObjectType(
    th.Property("value", th.StringType),
    th.Property("definition", th.StringType),
)

CONDITIONALITY_RULE_SCHEMA = th.ObjectType(
    th.Property(
        "upstreamCondition",
        th.ObjectType(
            th.Property("taxonomyAttributeId", th.StringType),
            th.Property("answers", th.ArrayType(th.StringType)),
            th.Property("operation", th.StringType),
        ),
    ),
    th.Property(
        "downstreamConditions",
        th.ArrayType(
            th.ObjectType(
                th.Property("taxonomyAttributeId", th.StringType),
                th.Property("validationType", th.StringType),
                th.Property("answers", th.ArrayType(th.StringType)),
                th.Property("operation", th.StringType),
            )
        ),
    ),
)

ORDERS_QUERY = """
query GetDropshipPurchaseOrders(
  $limit: Int32
  $fromDate: IsoDateTime
  $sortOrder: SortOrder
  $hasResponse: Boolean
) {
  getDropshipPurchaseOrders(
    limit: $limit
    fromDate: $fromDate
    sortOrder: $sortOrder
    hasResponse: $hasResponse
  ) {
    id
    storePrefix
    poNumber
    poDate
    orderId
    estimatedShipDate
    scheduledDeliveryDate
    deliveryMethodCode
    customerName
    customerAddress1
    customerAddress2
    customerCity
    customerState
    customerPostalCode
    customerCountry
    customerEmail
    salesChannelName
    orderType
    packingSlipUrl
    shippingInfo {
      shipSpeed
      carrierCode
    }
    warehouse {
      id
      name
      address {
        name
        address1
        address2
        address3
        city
        state
        country
        postalCode
        phoneNumber
      }
    }
    products {
      partNumber
      quantity
      price
      pieceCount
      totalCost
      name
      weight
      totalWeight
      estShipDate
      fillDate
      sku
      isCancelled
      isTscaCompliant
      twoDayGuaranteeDeliveryDeadline
      customComment
      event {
        id
        type
        name
        startDate
        endDate
      }
    }
    shipTo {
      name
      address1
      address2
      address3
      city
      state
      country
      postalCode
      phoneNumber
    }
    billTo {
      name
      address1
      address2
      address3
      city
      state
      country
      postalCode
      phoneNumber
    }
    billingInfo {
      vatNumber
    }
  }
}
"""

TAXONOMY_CATEGORIES_QUERY = """
query taxonomyCategories(
  $marketContext: MarketContextInput!
  $paginationOptions: PaginationOptions
) {
  taxonomyCategories(
    marketContext: $marketContext
    paginationOptions: $paginationOptions
  ) {
    pageInfo {
      page
      pageSize
      hasNextPage
      totalPages
    }
    taxonomyCategories {
      taxonomyCategoryId
      name
    }
  }
}
"""

TAXONOMY_ATTRIBUTES_QUERY = """
query GetTaxonomyAttributesByFilter($input: AttributesFilterInput!) {
  attributesByFilter(input: $input) {
    classId
    attributes {
      taxonomyAttributeId
      title
      description
      requirement
      valueFormat {
        canValueBeCustomized
        canValueBeSetToUnavailable
        canValueBeSetToNotApplicable
        datatype
      }
      possibleAttributeValues {
        value
        definition
      }
      parentAttributeId
      relatedAttributeIds
      classIds
    }
    conditionalityRules {
      taxonomyAttributeId
      rules {
        upstreamCondition {
          taxonomyAttributeId
          answers
          operation
        }
        downstreamConditions {
          taxonomyAttributeId
          validationType
          answers
          operation
        }
      }
    }
  }
}
"""

class OrdersStream(WayfairStream):
    """Dropship purchase orders from the Wayfair Orders GraphQL API."""

    name = "orders"

    @classproperty
    def records_jsonpath(cls) -> str:  # type: ignore[override]
        return "$.data.getDropshipPurchaseOrders[*]"

    @property
    def query(self) -> str:
        return ORDERS_QUERY

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType),
        th.Property("storePrefix", th.StringType),
        th.Property("poNumber", th.StringType),
        th.Property("poDate", th.DateTimeType),
        th.Property("orderId", th.IntegerType),
        th.Property("estimatedShipDate", th.DateTimeType),
        th.Property("scheduledDeliveryDate", th.DateTimeType),
        th.Property("deliveryMethodCode", th.StringType),
        th.Property("customerName", th.StringType),
        th.Property("customerAddress1", th.StringType),
        th.Property("customerAddress2", th.StringType),
        th.Property("customerCity", th.StringType),
        th.Property("customerState", th.StringType),
        th.Property("customerPostalCode", th.StringType),
        th.Property("customerCountry", th.StringType),
        th.Property("customerEmail", th.StringType),
        th.Property("salesChannelName", th.StringType),
        th.Property("orderType", th.StringType),
        th.Property("packingSlipUrl", th.StringType),
        th.Property(
            "shippingInfo",
            th.ObjectType(
                th.Property("shipSpeed", th.StringType),
                th.Property("carrierCode", th.StringType),
            ),
        ),
        th.Property(
            "warehouse",
            th.ObjectType(
                th.Property("id", th.StringType),
                th.Property("name", th.StringType),
                th.Property("address", ADDRESS_SCHEMA),
            ),
        ),
        th.Property(
            "products",
            th.ArrayType(PRODUCT_SCHEMA),
        ),
        th.Property("shipTo", ADDRESS_SCHEMA),
        th.Property("billTo", ADDRESS_SCHEMA),
        th.Property(
            "billingInfo",
            th.ObjectType(
                th.Property("vatNumber", th.StringType),
            ),
        ),
    ).to_dict()

class ProductCatalogStream(WayfairStream):
    """Product catalog streams sharing url_base, headers, and market context."""

    path = CATALOG_GRAPHQL_PATH
    replication_key = None
    page_size = 50

    @property
    def url_base(self) -> str:
        return self.config.get("catalog_api_url", DEFAULT_CATALOG_API_BASE).rstrip("/")

    @property
    def market_context(self) -> Dict[str, str]:
        return {
            key: self.config.get(key, default)
            for key, default in DEFAULT_MARKET_CONTEXT.items()
        }

    def post_process(self, row: dict, context: Optional[dict] = None) -> Optional[dict]:
        return row

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        return None

class TaxonomyCategoriesStream(ProductCatalogStream):
    """Taxonomy categories from the Wayfair Product Catalog GraphQL API."""

    name = "taxonomy_categories"
    primary_keys = ["taxonomyCategoryId"]

    @classproperty
    def records_jsonpath(cls) -> str:  # type: ignore[override]
        return "$.data.taxonomyCategories.taxonomyCategories[*]"

    @property
    def query(self) -> str:
        return TAXONOMY_CATEGORIES_QUERY

    schema = th.PropertiesList(
        th.Property("taxonomyCategoryId", th.StringType),
        th.Property("name", th.StringType),
    ).to_dict()

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "marketContext": self.market_context,
            "paginationOptions": {
                "page": next_page_token or 1,
                "pageSize": self.page_size,
            },
        }

    def get_next_page_token(
        self,
        response: requests.Response,
        previous_token: Optional[Any],
    ) -> Optional[Any]:
        page_info = (
            (response.json().get("data") or {})
            .get("taxonomyCategories", {})
            .get("pageInfo")
            or {}
        )
        if page_info.get("hasNextPage"):
            return int(page_info.get("page") or previous_token or 1) + 1
        return None

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        return {"taxonomyCategoryId": record["taxonomyCategoryId"]}


class TaxonomyAttributesStream(ProductCatalogStream):
    """Taxonomy attributes, one record per attribute returned by the catalog API."""

    name = "taxonomy_attributes"
    primary_keys = ["taxonomyCategoryId", "taxonomyAttributeId"]
    parent_stream_type = TaxonomyCategoriesStream

    @property
    def query(self) -> str:
        return TAXONOMY_ATTRIBUTES_QUERY

    schema = th.PropertiesList(
        th.Property("taxonomyCategoryId", th.StringType),
        th.Property("taxonomyAttributeId", th.StringType),
        th.Property("title", th.StringType),
        th.Property("description", th.StringType),
        th.Property("requirement", th.StringType),
        th.Property("valueFormat", VALUE_FORMAT_SCHEMA),
        th.Property(
            "possibleAttributeValues",
            th.ArrayType(ATTRIBUTE_VALUE_SCHEMA),
        ),
        th.Property("parentAttributeId", th.StringType),
        th.Property("relatedAttributeIds", th.ArrayType(th.StringType)),
        th.Property("classIds", th.ArrayType(th.StringType)),
        th.Property(
            "conditionalityRules",
            th.ArrayType(CONDITIONALITY_RULE_SCHEMA),
        ),
    ).to_dict()

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        return {
            "input": {
                # Live Product Catalog schema uses classId (legacy name for
                # taxonomyCategoryId).
                "classId": context["taxonomyCategoryId"],
                "marketContext": self.market_context,
            }
        }

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Yield one record per top-level attribute.

        Child attributes are already returned in ``attributes`` with
        ``parentAttributeId`` set, so they are not requested separately.
        """
        for result in (response.json().get("data") or {}).get("attributesByFilter") or []:
            category_id = str(result.get("classId"))
            rules = {
                rule.get("taxonomyAttributeId"): rule.get("rules") or []
                for rule in result.get("conditionalityRules") or []
            }
            for attribute in result.get("attributes") or []:
                record = dict(attribute)
                record["taxonomyCategoryId"] = category_id
                record["conditionalityRules"] = rules.get(
                    attribute.get("taxonomyAttributeId"), []
                )
                yield record
