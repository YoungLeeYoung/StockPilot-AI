# Advanced research features

## Portfolio analysis

`POST /api/v1/portfolio/analyze` calculates sector concentration, largest position, HHI concentration, aligned historical annualized volatility, and deterministic risk flags.

`POST /api/v1/portfolio/ai-analyze` returns the same quantitative report plus LLM interpretation. Holdings must be unique and weights must total 100 percent.

## Financial PDF analysis

`POST /api/v1/financial-documents/analyze` accepts a multipart PDF upload. It validates file size, PDF signature, encryption, page count, and extractable text before sending bounded filing text to the configured LLM. The response separates revenue, profit, risk factors, summary, and extraction limitations.

Scanned filings require an OCR adapter, which is not included in the initial implementation.

## Investment journal

`POST /api/v1/investment-journals` records the decision-time facts.

`GET /api/v1/investment-journals/{user_id}` returns a user's journal, optionally filtered by symbol.

`POST /api/v1/investment-journals/entries/{entry_id}/review` adds outcome notes and a structured AI review without changing the original reason or thesis.

## AI configuration

AI endpoints require `LLM_BASE_URL`, `LLM_MODEL`, and optionally `LLM_API_KEY`. When no model is configured, they return `503` instead of fabricated output.

