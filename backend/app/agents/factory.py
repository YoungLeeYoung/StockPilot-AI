from app.agents.contracts import AgentModel
from app.agents.research_agent import ResearchAgent
from app.agents.tool_registry import AgentToolRegistry
from app.agents.tools import (
    FinancialReportTool,
    NewsTool,
    StockPriceTool,
    TechnicalAnalysisTool,
)
from app.integrations.financial_providers import FinancialReportProvider
from app.services.news_service import NewsService
from app.services.stock_service import StockService
from app.services.technical_analysis import TechnicalAnalysisService


def create_research_agent(
    model: AgentModel,
    stock_service: StockService,
    technical_service: TechnicalAnalysisService,
    news_service: NewsService,
    financial_provider: FinancialReportProvider,
    max_iterations: int = 8,
) -> ResearchAgent:
    registry = AgentToolRegistry(
        [
            StockPriceTool(stock_service),
            TechnicalAnalysisTool(stock_service, technical_service),
            NewsTool(news_service),
            FinancialReportTool(financial_provider),
        ]
    )
    return ResearchAgent(model, registry, max_iterations=max_iterations)

