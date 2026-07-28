import asyncio
import json
import math

import pandas as pd
from pydantic import ValidationError

from app.agents.contracts import AgentModel
from app.schemas.portfolio import (
    PortfolioAiAnalysis,
    PortfolioAnalysisReport,
    PortfolioAnalysisRequest,
    PortfolioHolding,
)
from app.schemas.stock import StockResponse
from app.services.stock_service import StockService


class PortfolioAnalysisError(ValueError):
    """Raised when portfolio market data cannot support analysis."""


class PortfolioAnalysisService:
    minimum_return_points = 20

    def __init__(self, stock_service: StockService) -> None:
        self.stock_service = stock_service

    async def analyze(
        self,
        request: PortfolioAnalysisRequest,
    ) -> PortfolioAnalysisReport:
        stocks = await asyncio.gather(
            *(
                asyncio.to_thread(self.stock_service.get_stock, holding.symbol)
                for holding in request.holdings
            )
        )
        returns = self._build_returns(request.holdings, stocks)
        weights = pd.Series(
            {holding.symbol: holding.weight / 100 for holding in request.holdings}
        )
        portfolio_returns = returns.mul(weights, axis="columns").sum(axis="columns")
        annualized_volatility = float(portfolio_returns.std(ddof=1) * math.sqrt(252))

        sector_concentration: dict[str, float] = {}
        for holding, stock in zip(request.holdings, stocks, strict=True):
            sector = stock.basic_info.sector or "Unknown"
            sector_concentration[sector] = sector_concentration.get(sector, 0) + holding.weight
        sector_concentration = {
            sector: round(weight, 2)
            for sector, weight in sorted(
                sector_concentration.items(), key=lambda item: item[1], reverse=True
            )
        }

        largest_position = max(request.holdings, key=lambda holding: holding.weight)
        concentration_hhi = sum((holding.weight / 100) ** 2 for holding in request.holdings)
        risk_level = self._risk_level(annualized_volatility)
        risk_factors = self._risk_factors(
            request,
            sector_concentration,
            annualized_volatility,
            concentration_hhi,
        )
        observations = [
            f"Largest position is {largest_position.symbol} at {largest_position.weight:.1f}%.",
            (
                f"Largest sector exposure is {next(iter(sector_concentration))} at "
                f"{next(iter(sector_concentration.values())):.1f}%."
            ),
            f"Estimated annualized volatility is {annualized_volatility:.1%}.",
        ]

        return PortfolioAnalysisReport(
            sector_concentration=sector_concentration,
            largest_position=largest_position,
            concentration_hhi=round(concentration_hhi, 4),
            annualized_volatility=round(annualized_volatility, 4),
            risk_level=risk_level,
            risk_factors=risk_factors,
            observations=observations,
            data_points=len(returns),
        )

    def _build_returns(
        self,
        holdings: list[PortfolioHolding],
        stocks: list[StockResponse],
    ) -> pd.DataFrame:
        series: list[pd.Series] = []
        for holding, stock in zip(holdings, stocks, strict=True):
            prices = pd.Series(
                {pd.Timestamp(item.date): item.close for item in stock.history},
                name=holding.symbol,
                dtype="float64",
            ).sort_index()
            series.append(prices.pct_change(fill_method=None).rename(holding.symbol))

        returns = pd.concat(series, axis="columns", join="inner").dropna()
        if len(returns) < self.minimum_return_points:
            raise PortfolioAnalysisError(
                f"At least {self.minimum_return_points} aligned return points are required."
            )
        return returns

    @staticmethod
    def _risk_level(volatility: float) -> str:
        if volatility < 0.15:
            return "low"
        if volatility < 0.30:
            return "moderate"
        return "high"

    @staticmethod
    def _risk_factors(
        request: PortfolioAnalysisRequest,
        sectors: dict[str, float],
        volatility: float,
        concentration_hhi: float,
    ) -> list[str]:
        risks: list[str] = []
        largest = max(request.holdings, key=lambda holding: holding.weight)
        if largest.weight >= 40:
            risks.append(
                f"Single-position concentration: {largest.symbol} is {largest.weight:.1f}%."
            )
        largest_sector, sector_weight = next(iter(sectors.items()))
        if sector_weight >= 60:
            risks.append(
                f"Sector concentration: {largest_sector} represents {sector_weight:.1f}%."
            )
        if concentration_hhi >= 0.30:
            risks.append("Portfolio concentration is high based on the HHI measure.")
        if volatility >= 0.30:
            risks.append("Historical annualized volatility is high.")
        if len(request.holdings) < 5:
            risks.append("The portfolio contains fewer than five positions.")
        return risks


class PortfolioAiAnalysisService:
    def __init__(self, model: AgentModel) -> None:
        self.model = model

    async def analyze(self, report: PortfolioAnalysisReport) -> PortfolioAiAnalysis:
        response = await self.model.complete(
            [
                {
                    "role": "system",
                    "content": (
                        "Explain a portfolio's industry concentration, risk, and historical "
                        "volatility using only the supplied metrics. Do not predict returns or "
                        "give personalized trading instructions. Return JSON with exactly: "
                        "industry_concentration, risk, volatility, summary."
                    ),
                },
                {
                    "role": "user",
                    "content": report.model_dump_json(),
                },
            ],
            [],
        )
        if not response.content or response.tool_calls:
            raise PortfolioAnalysisError("LLM returned an invalid portfolio analysis.")
        content = response.content.strip()
        if content.startswith("```"):
            content = "\n".join(content.splitlines()[1:-1]).strip()
        try:
            return PortfolioAiAnalysis.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise PortfolioAnalysisError("LLM returned an invalid portfolio analysis.") from exc
