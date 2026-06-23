"""Stream type classes for tap-wayfair."""

from hotglue_singer_sdk import typing as th
from hotglue_singer_sdk.helpers._classproperty import classproperty

from tap_wayfair.client import WayfairStream

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
