from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.dependencies import AgentConfigurationError, get_agent_model
from app.schemas.portfolio import (
    PortfolioAnalysisReport,
    PortfolioAnalysisRequest,
    PortfolioResearchResult,
)
from app.services.portfolio_analysis import (
    PortfolioAiAnalysisService,
    PortfolioAnalysisError,
    PortfolioAnalysisService,
)
from app.services.stock_service import StockDataProviderError, StockNotFoundError, StockService

router = APIRouter()


def get_portfolio_service() -> PortfolioAnalysisService:
    return PortfolioAnalysisService(StockService())


@router.post("/analyze", response_model=PortfolioAnalysisReport)
async def analyze_portfolio(
    request: PortfolioAnalysisRequest,
    service: Annotated[PortfolioAnalysisService, Depends(get_portfolio_service)],
) -> PortfolioAnalysisReport:
    try:
        return await service.analyze(request)
    except StockNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StockDataProviderError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Portfolio market data is temporarily unavailable.",
        ) from exc
    except PortfolioAnalysisError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.post("/ai-analyze", response_model=PortfolioResearchResult)
async def ai_analyze_portfolio(
    request: PortfolioAnalysisRequest,
    service: Annotated[PortfolioAnalysisService, Depends(get_portfolio_service)],
) -> PortfolioResearchResult:
    try:
        model = get_agent_model()
        quantitative = await service.analyze(request)
        ai_analysis = await PortfolioAiAnalysisService(model).analyze(quantitative)
        return PortfolioResearchResult(
            quantitative=quantitative,
            ai_analysis=ai_analysis,
        )
    except AgentConfigurationError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except StockNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except StockDataProviderError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Portfolio market data is temporarily unavailable.",
        ) from exc
    except PortfolioAnalysisError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
