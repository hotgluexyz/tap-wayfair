# tap-wayfair

`tap-wayfair` is a Singer tap for [Wayfair](https://www.wayfair.com/), extracting dropship purchase orders from the Wayfair Orders GraphQL API.

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

| Setting         | Required | Description                                                                 |
|-----------------|----------|-----------------------------------------------------------------------------|
| `client_id`     | Yes      | Wayfair OAuth2 client ID                                                    |
| `client_secret` | Yes      | Wayfair OAuth2 client secret                                                |
| `api_url`       | No       | GraphQL endpoint (default: `https://api.wayfair.com/v1/graphql`)            |
| `start_date`    | No       | Earliest order `poDate` to sync (ISO 8601 / datetime format)                |

Example `config.json`:

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "api_url": "https://api.wayfair.com/v1/graphql",
  "start_date": "2024-01-01T00:00:00Z"
}
```

For sandbox credentials, set `api_url` to `https://sandbox.api.wayfair.com/v1/graphql`.

A full list of supported settings and capabilities for this tap is available by running:

```bash
tap-wayfair --about
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Source Authentication and Authorization

This tap uses OAuth2 client credentials against `https://sso.auth.wayfair.com/oauth/token`.
Register an application in the [Wayfair Developer Portal](https://developer.wayfair.io/) to obtain
a client ID and client secret with Dropship Orders API access.

## Supported Streams

| Stream   | Replication Key | Primary Key | Description                                      |
|----------|-----------------|-------------|--------------------------------------------------|
| `orders` | `poDate`        | `id`        | Dropship purchase orders (`getDropshipPurchaseOrders`) |

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
