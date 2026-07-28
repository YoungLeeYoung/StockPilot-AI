# API conventions

## Base path

All versioned endpoints use `/api/v1`.

## Formats

- Request and response bodies use JSON.
- Field names use `snake_case`.
- Timestamps will use ISO 8601 in UTC.
- HTTP status codes communicate the broad outcome.

## Health endpoint

`GET /api/v1/health` confirms that the API process is running. Dependency readiness checks will be added when database and cache connections are implemented.

## Stock endpoint

`GET /api/v1/stock/{symbol}` returns stock summary fields and one year of daily OHLCV history. Symbols are normalized to uppercase. Missing symbols return `404`, while temporary upstream failures return `502`.

## Advanced analysis endpoints

Portfolio analysis uses `/api/v1/portfolio`. Financial PDF uploads use `/api/v1/financial-documents`. Investment journal creation, listing, and review use `/api/v1/investment-journals`. LLM-backed operations return `503` until a model endpoint is configured.

## Error envelope

Domain errors use FastAPI's `detail` property with a stable error code and a user-safe message. Request identifiers can be added when centralized request logging is introduced.
