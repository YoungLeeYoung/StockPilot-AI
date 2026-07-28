import json
from typing import Any

import pytest

from app.agents.contracts import AgentModelResponse, AgentToolDefinition
from app.services.financial_pdf_analysis import (
    FinancialPdfAnalysisService,
    FinancialPdfError,
)


class FinancialDocumentModel:
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        assert "Revenue was $100 million" in messages[-1]["content"]
        assert tools == []
        return AgentModelResponse(
            content=json.dumps(
                {
                    "revenue": "$100 million for FY2026",
                    "profit": "$18 million net income for FY2026",
                    "risk_factors": ["Customer concentration", "Supply constraints"],
                    "summary": "Revenue and profit increased, with concentration risk.",
                }
            )
        )


class ExtractablePdfService(FinancialPdfAnalysisService):
    def _extract_text(self, content: bytes) -> tuple[str, int, bool]:
        return "Revenue was $100 million. Net income was $18 million." * 3, 42, False


@pytest.mark.asyncio
async def test_pdf_analysis_returns_structured_financial_report() -> None:
    service = ExtractablePdfService(
        model=FinancialDocumentModel(),
        max_file_size_bytes=1_000_000,
        max_pages=300,
        max_text_chars=200_000,
    )

    result = await service.analyze("sample-10-k.pdf", b"%PDF-test")

    assert result.file_name == "sample-10-k.pdf"
    assert result.page_count == 42
    assert result.report.revenue == "$100 million for FY2026"
    assert result.report.risk_factors == ["Customer concentration", "Supply constraints"]


def test_pdf_analysis_rejects_non_pdf_content() -> None:
    service = FinancialPdfAnalysisService(
        model=FinancialDocumentModel(),
        max_file_size_bytes=1_000_000,
        max_pages=300,
        max_text_chars=200_000,
    )

    with pytest.raises(FinancialPdfError, match="not a valid PDF"):
        service._extract_text(b"not-a-pdf")

