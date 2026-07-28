import json
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.agents.contracts import (
    AgentModelResponse,
    AgentToolCall,
    AgentToolDefinition,
)
from app.agents.research_agent import (
    AgentIterationLimitError,
    AgentOutputError,
    ResearchAgent,
)
from app.agents.tool_registry import AgentToolRegistry
from app.agents.tools import (
    FinancialReportTool,
    NewsTool,
    StockPriceTool,
    TechnicalAnalysisTool,
)
from app.integrations.financial_providers import FinancialReportSnapshot
from app.schemas.news import NewsArticle
from app.schemas.stock import StockBasicInfo, StockHistoryItem, StockResponse
from app.services.technical_analysis import TechnicalReport


class FakeStockService:
    def get_stock(self, symbol: str) -> StockResponse:
        history = [
            StockHistoryItem(
                date=date(2026, 5, 1).replace(day=1) if index == 0 else date(2026, 5, 1),
                open=100 + index,
                high=102 + index,
                low=99 + index,
                close=101 + index,
                volume=1_000_000 + index,
            )
            for index in range(60)
        ]
        return StockResponse(
            symbol=symbol,
            basic_info=StockBasicInfo(
                current_price=160,
                market_cap=3_900_000_000_000,
                trailing_pe=45,
                fifty_two_week_high=165,
                fifty_two_week_low=90,
            ),
            history=history,
        )


class FakeTechnicalService:
    def analyze(self, history: list[StockHistoryItem]) -> TechnicalReport:
        return TechnicalReport(
            trend="bullish",
            signals=["price above MA20"],
            risk=["RSI overbought"],
        )


class FakeNewsService:
    async def get_recent_news(self, symbol: str, limit: int = 10) -> list[NewsArticle]:
        return [
            NewsArticle(
                title=f"{symbol} launches new platform",
                source="Example Wire",
                date=datetime(2026, 7, 28, tzinfo=UTC),
                summary="The company announced a new platform.",
            )
        ][:limit]


class FakeFinancialProvider:
    async def fetch_financial_report(self, symbol: str) -> FinancialReportSnapshot:
        return FinancialReportSnapshot(
            symbol=symbol,
            company_name="NVIDIA Corporation",
            fiscal_period="FY2026 Q2",
            currency="USD",
            sector="Technology",
            metrics={"revenue": 44_000_000_000, "net_income": 19_000_000_000},
            source="Example Filing",
        )


class ScriptedModel:
    def __init__(self) -> None:
        self.calls = 0
        self.observed_messages: list[dict[str, Any]] = []

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        self.calls += 1
        self.observed_messages = messages
        if self.calls == 1:
            available = {tool.name for tool in tools}
            assert available == {
                "get_stock_price",
                "get_news",
                "get_technical_analysis",
                "get_financial_report",
            }
            return AgentModelResponse(
                tool_calls=[
                    AgentToolCall("news", "get_news", {"symbol": "NVDA"}),
                    AgentToolCall("financial", "get_financial_report", {"symbol": "NVDA"}),
                    AgentToolCall("price", "get_stock_price", {"symbol": "NVDA"}),
                    AgentToolCall("technical", "get_technical_analysis", {"symbol": "NVDA"}),
                ]
            )
        return AgentModelResponse(
            content=json.dumps(
                {
                    "company_overview": "NVIDIA is a technology company.",
                    "current_trend": "Price data indicates positive momentum.",
                    "technical_analysis": "The technical trend is bullish.",
                    "news_impact": "Recent platform news may support sentiment.",
                    "risk_factors": ["High valuation", "RSI is elevated"],
                    "summary": "Evidence is constructive, with valuation risk.",
                }
            )
        )


def build_tools() -> AgentToolRegistry:
    stock_service = FakeStockService()
    return AgentToolRegistry(
        [
            StockPriceTool(stock_service),
            TechnicalAnalysisTool(stock_service, FakeTechnicalService()),
            NewsTool(FakeNewsService()),
            FinancialReportTool(FakeFinancialProvider()),
        ]
    )


@pytest.mark.asyncio
async def test_agent_lets_model_select_tools_and_builds_report() -> None:
    model = ScriptedModel()

    report = await ResearchAgent(model, build_tools()).run("分析NVDA")

    assert report.company_overview == "NVIDIA is a technology company."
    assert report.risk_factors == ["High valuation", "RSI is elevated"]
    tool_messages = [
        message for message in model.observed_messages if message["role"] == "tool"
    ]
    assert {message["name"] for message in tool_messages} == {
        "get_stock_price",
        "get_news",
        "get_technical_analysis",
        "get_financial_report",
    }
    assert all(json.loads(message["content"])["ok"] for message in tool_messages)


class EmptyModel:
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        return AgentModelResponse()


@pytest.mark.asyncio
async def test_agent_rejects_empty_model_response() -> None:
    with pytest.raises(AgentOutputError):
        await ResearchAgent(EmptyModel(), build_tools()).run("分析NVDA")


class LoopingModel:
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        return AgentModelResponse(
            tool_calls=[AgentToolCall("loop", "get_news", {"symbol": "NVDA"})]
        )


@pytest.mark.asyncio
async def test_agent_stops_after_iteration_limit() -> None:
    with pytest.raises(AgentIterationLimitError):
        await ResearchAgent(LoopingModel(), build_tools(), max_iterations=2).run("分析NVDA")

