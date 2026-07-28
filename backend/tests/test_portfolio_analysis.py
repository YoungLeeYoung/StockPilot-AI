import json
from datetime import date, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from app.agents.contracts import AgentModelResponse, AgentToolDefinition
from app.schemas.portfolio import PortfolioAnalysisRequest, PortfolioHolding
from app.schemas.stock import StockBasicInfo, StockHistoryItem, StockResponse
from app.services.portfolio_analysis import (
    PortfolioAiAnalysisService,
    PortfolioAnalysisService,
)


class PortfolioStockService:
    sectors = {"AAPL": "Technology", "NVDA": "Technology", "MO": "Consumer Defensive"}

    def get_stock(self, symbol: str) -> StockResponse:
        start = date(2026, 1, 1)
        history = []
        for index in range(80):
            base = 100 + index * (0.25 if symbol != "MO" else 0.08)
            movement = ((index % 7) - 3) * (0.7 if symbol == "NVDA" else 0.25)
            close = base + movement
            history.append(
                StockHistoryItem(
                    date=start + timedelta(days=index),
                    open=close - 0.3,
                    high=close + 1,
                    low=close - 1,
                    close=close,
                    volume=1_000_000,
                )
            )
        return StockResponse(
            symbol=symbol,
            basic_info=StockBasicInfo(
                company_name=symbol,
                sector=self.sectors[symbol],
                current_price=history[-1].close,
                market_cap=100_000_000,
                trailing_pe=20,
                fifty_two_week_high=150,
                fifty_two_week_low=80,
            ),
            history=history,
        )


@pytest.mark.asyncio
async def test_portfolio_analysis_calculates_concentration_and_volatility() -> None:
    request = PortfolioAnalysisRequest(
        holdings=[
            PortfolioHolding(symbol="AAPL", weight=40),
            PortfolioHolding(symbol="NVDA", weight=30),
            PortfolioHolding(symbol="MO", weight=30),
        ]
    )

    report = await PortfolioAnalysisService(PortfolioStockService()).analyze(request)

    assert report.sector_concentration == {
        "Technology": 70.0,
        "Consumer Defensive": 30.0,
    }
    assert report.largest_position.symbol == "AAPL"
    assert report.concentration_hhi == pytest.approx(0.34)
    assert report.annualized_volatility > 0
    assert report.data_points == 79
    assert any("Sector concentration" in risk for risk in report.risk_factors)


def test_portfolio_weights_must_total_one_hundred() -> None:
    with pytest.raises(ValidationError, match="total 100"):
        PortfolioAnalysisRequest(
            holdings=[
                PortfolioHolding(symbol="AAPL", weight=40),
                PortfolioHolding(symbol="NVDA", weight=30),
            ]
        )


class PortfolioModel:
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        assert "Technology" in messages[-1]["content"]
        return AgentModelResponse(
            content=json.dumps(
                {
                    "industry_concentration": "Technology represents 70% of the portfolio.",
                    "risk": "The portfolio has position and sector concentration risk.",
                    "volatility": "Historical volatility is moderate.",
                    "summary": "Diversification is limited across three holdings.",
                }
            )
        )


@pytest.mark.asyncio
async def test_portfolio_ai_explains_quantitative_report() -> None:
    request = PortfolioAnalysisRequest(
        holdings=[
            PortfolioHolding(symbol="AAPL", weight=40),
            PortfolioHolding(symbol="NVDA", weight=30),
            PortfolioHolding(symbol="MO", weight=30),
        ]
    )
    quantitative = await PortfolioAnalysisService(PortfolioStockService()).analyze(request)

    analysis = await PortfolioAiAnalysisService(PortfolioModel()).analyze(quantitative)

    assert analysis.industry_concentration == "Technology represents 70% of the portfolio."
    assert "concentration risk" in analysis.risk
