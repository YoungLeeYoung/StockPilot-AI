from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.agents.dependencies import AgentConfigurationError, get_agent_model
from app.core.config import settings
from app.schemas.financial_document import FinancialPdfAnalysis
from app.services.financial_pdf_analysis import (
    FinancialPdfAnalysisService,
    FinancialPdfError,
)

router = APIRouter()


def get_financial_pdf_service() -> FinancialPdfAnalysisService:
    try:
        model = get_agent_model()
    except AgentConfigurationError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return FinancialPdfAnalysisService(
        model=model,
        max_file_size_bytes=settings.pdf_max_file_size_mb * 1024 * 1024,
        max_pages=settings.pdf_max_pages,
        max_text_chars=settings.pdf_max_text_chars,
    )


@router.post("/analyze", response_model=FinancialPdfAnalysis)
async def analyze_financial_pdf(
    file: Annotated[UploadFile, File(description="10-K or other financial report PDF")],
    service: Annotated[FinancialPdfAnalysisService, Depends(get_financial_pdf_service)],
) -> FinancialPdfAnalysis:
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="PDF required.")
    content = await file.read(settings.pdf_max_file_size_mb * 1024 * 1024 + 1)
    try:
        return await service.analyze(file.filename or "financial-report.pdf", content)
    except FinancialPdfError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

