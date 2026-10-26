# tap-wayfair

`tap-wayfair` is a Singer tap for [Wayfair](https://www.wayfair.com/), extracting dropship purchase orders and product-catalog taxonomy data from Wayfair GraphQL APIs.

Built with the [Hotglue Singer SDK](https://github.com/hotgluexyz/HotglueSingerSDK) for Singer Taps.

## Installation

```bash
pip install tap-wayfair
```

Or install directly from the repository:

```bash
pip install git+https://github.com/hotgluexyz/tap-wayfair.git
```

## Configuration

### Accepted Config Options

| Setting                    | Required | Description                                                                 |
|----------------------------|----------|-----------------------------------------------------------------------------|
| `client_id`                | Yes      | Wayfair OAuth2 client ID                                                    |
| `client_secret`            | Yes      | Wayfair OAuth2 client secret                                                |
| `api_url`                  | No       | Orders GraphQL endpoint (overrides `is_sandbox`; default production or sandbox URL from `is_sandbox`) |
| `catalog_api_url`          | No       | Product catalog API base URL; path is appended (overrides `is_sandbox`) |
| `brand`                    | No       | Market context brand for taxonomy streams (default: `WAYFAIR`)              |
| `country`                  | No       | Market context country for taxonomy streams (default: `UNITED_STATES`)      |
| `locale`                   | No       | Market context locale for taxonomy streams (default: `en-US`)               |
| `start_date`               | No       | Earliest order `poDate` to sync (ISO 8601 / datetime format)                |
| `is_sandbox`               | No       | When `true`, orders use `https://sandbox.api.wayfair.com/v1/graphql` and catalog uses `https://api.wayfair.io/sandbox` unless URLs are overridden |
| `access_token`             | No       | Set by hotglue after Developer Portal OAuth (do not set manually)           |
| `refresh_token`            | No       | Set by hotglue after Developer Portal OAuth                                 |
| `expires_in`               | No       | Token TTL or Unix expiry from hotglue / after refresh                       |

**Client credentials** (manual or internal sandbox app):

Example `config.json`:

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "api_url": "https://api.wayfair.com/v1/graphql",
  "catalog_api_url": "https://api.wayfair.io",
  "brand": "WAYFAIR",
  "country": "UNITED_STATES",
  "locale": "en-US",
  "start_date": "2024-01-01T00:00:00Z"
}
```

For sandbox credentials, set `is_sandbox` to `true` (or override `api_url` / `catalog_api_url` explicitly).

**Developer Portal OAuth** (hotglue connect; includes `refresh_token`):

```json
{
  "client_id": "vendor-…",
  "client_secret": "…",
  "is_sandbox": true,
  "access_token": "…",
  "refresh_token": "…",
  "expires_in": 3600
}
```

A full list of supported settings and capabilities for this tap is available by running:

```bash
tap-wayfair --about
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

Wayfair supports two OAuth 2.0 flows. The tap picks the flow from config:

| Config | Flow | Token endpoint |
|--------|------|----------------|
| No `refresh_token` | [Client credentials](https://developer.wayfair.io/posts/api-access-tokens) | `https://sso.auth.wayfair.com/oauth/token` (JSON body) |
| `refresh_token` present | Developer Portal authorization code (hotglue UI) | `https://partners.wayfair.com/auth/realms/Developer_Portal/protocol/openid-connect/token` (form body, refresh grant) |

Tokens are refreshed automatically when they are close to expiry. With `TapWayfair.access_token_support`, jobs can also refresh via the hotglue accesstoken API before calling Wayfair locally.

Register an application in the [Wayfair Developer Portal](https://developer.wayfair.io/) to obtain credentials with access to the Orders and/or Product Catalog APIs.

## Supported Streams

| Stream                 | Replication Key | Primary Key                                      | Description |
|------------------------|-----------------|--------------------------------------------------|-------------|
| `orders`               | `poDate`        | `id`                                             | Dropship purchase orders (`getDropshipPurchaseOrders`) |
| `taxonomy_categories`  | —               | `taxonomyCategoryId`                             | Product catalog taxonomy categories |
| `taxonomy_attributes`  | —               | `taxonomyCategoryId`, `taxonomyAttributeId`      | Taxonomy attributes per category (one attribute per record, including nested child attributes) |

## Usage

You can easily run `tap-wayfair` by itself or in a pipeline.

### Executing the Tap Directly

```bash
tap-wayfair --version
tap-wayfair --help
tap-wayfair --config CONFIG --discover > ./catalog.json
tap-wayfair --config CONFIG --catalog CATALOG > ./data.singer
```

## Developer Resources

### Initialize your Development Environment

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install ruff
```

### Create and Run Tests

Create tests within the `tap_wayfair/tests` subfolder and then run:

```bash
.venv/bin/pytest
```

### Linting

```bash
.venv/bin/ruff check .
```
