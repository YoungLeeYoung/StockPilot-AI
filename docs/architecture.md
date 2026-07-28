# Architecture overview

## Purpose

StockPilot AI helps users understand stock market information by bringing together market data, technical indicators, news, and LLM-assisted research. It is not intended to predict prices or issue trading instructions.

## High-level components

```text
React Web
    |
FastAPI Backend
    |
    +-- Market Data Provider
    +-- News Provider
    +-- LLM Agent Provider
    |
PostgreSQL and Redis
```

## Backend boundaries

- `api`: HTTP transport, validation, and response handling
- `services`: application use cases and business orchestration
- `integrations`: stock, news, and LLM provider adapters
- `agents`: controlled LLM workflows, tools, prompts, and output validation
- `db`: persistence models, repositories, and migrations
- `tasks`: asynchronous data collection and report generation

## Architectural principles

1. Calculations are deterministic; the LLM explains results but does not calculate source-of-truth indicators.
2. Provider-specific details stay behind adapters.
3. Generated claims remain traceable to market data or news sources.
4. Long-running research jobs execute outside API request workers.
5. The product communicates uncertainty and avoids predictive investment language.

## Current status

The application foundation, stock data endpoint, pandas technical analysis service, provider-neutral news service, model-driven research Agent, and SQLAlchemy persistence models are implemented. Concrete news, financial-data, and LLM provider adapters will be added incrementally.
