from fastapi import APIRouter

from app.api.routes.financial_documents import router as financial_documents_router
from app.api.routes.health import router as health_router
from app.api.routes.investment_journals import router as investment_journals_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.stock import router as stock_router

api_router = APIRouter()
api_router.include_router(
    financial_documents_router,
    prefix="/financial-documents",
    tags=["financial-documents"],
)
api_router.include_router(health_router, tags=["system"])
api_router.include_router(
    investment_journals_router,
    prefix="/investment-journals",
    tags=["investment-journals"],
)
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(stock_router, prefix="/stock", tags=["stock"])
