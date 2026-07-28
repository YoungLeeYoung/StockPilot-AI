import asyncio
from dataclasses import asdict
from typing import Any

from pydantic import BaseModel, Field

from app.agents.contracts import AgentToolDefinition
from app.integrations.financial_providers import FinancialReportProvider
from app.services.news_service import NewsService
from app.services.stock_service import StockService
from app.services.technical_analysis import TechnicalAnalysisService


class SymbolArguments(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9][A-Za-z0-9.\-^=]*$")


class NewsArguments(SymbolArguments):
    limit: int = Field(default=10, ge=1, le=20)


def _tool_parameters(model: type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()


class StockPriceTool:
    definition = AgentToolDefinition(
        name="get_stock_price",
        description=(
            "Get current price, market cap, P/E, 52-week range, and the latest daily OHLCV bars."
        ),
        parameters=_tool_parameters(SymbolArguments),
    )

    def __init__(self, stock_service: StockService) -> None:
        self.stock_service = stock_service

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        parsed = SymbolArguments.model_validate(arguments)
        stock = await asyncio.to_thread(
            self.stock_service.get_stock,
            parsed.symbol.upper(),
        )
        return {
            "symbol": stock.symbol,
            "basic_info": stock.basic_info.model_dump(mode="json"),
            "latest_history": [
                item.model_dump(mode="json") for item in stock.history[-10:]
            ],
            "history_points": len(stock.history),
        }


class TechnicalAnalysisTool:
    definition = AgentToolDefinition(
        name="get_technical_analysis",
        description=(
            "Calculate MA20, MA50, RSI, MACD, Bollinger Bands, trend, signals, and risk flags."
        ),
        parameters=_tool_parameters(SymbolArguments),
    )

    def __init__(
        self,
        stock_service: StockService,
        technical_service: TechnicalAnalysisService,
    ) -> None:
        self.stock_service = stock_service
        self.technical_service = technical_service

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        parsed = SymbolArguments.model_validate(arguments)
        stock = await asyncio.to_thread(
            self.stock_service.get_stock,
            parsed.symbol.upper(),
        )
        report = await asyncio.to_thread(
            self.technical_service.analyze,
            stock.history,
        )
        return report.model_dump(mode="json")


class NewsTool:
    definition = AgentToolDefinition(
        name="get_news",
        description="Get recent company-related news with source, date, and summary.",
        parameters=_tool_parameters(NewsArguments),
    )

    def __init__(self, news_service: NewsService) -> None:
        self.news_service = news_service

    async def execute(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        parsed = NewsArguments.model_validate(arguments)
        articles = await self.news_service.get_recent_news(
            parsed.symbol.upper(),
            limit=parsed.limit,
        )
        return [article.model_dump(mode="json") for article in articles]


class FinancialReportTool:
    definition = AgentToolDefinition(
        name="get_financial_report",
        description=(
            "Get the latest company profile and reported financial metrics for fundamental context."
        ),
        parameters=_tool_parameters(SymbolArguments),
    )

    def __init__(self, provider: FinancialReportProvider) -> None:
        self.provider = provider

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        parsed = SymbolArguments.model_validate(arguments)
        report = await self.provider.fetch_financial_report(parsed.symbol.upper())
        return asdict(report)

