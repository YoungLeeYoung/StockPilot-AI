from pydantic import BaseModel, Field


class FinancialDocumentReport(BaseModel):
    revenue: str = Field(min_length=1)
    profit: str = Field(min_length=1)
    risk_factors: list[str] = Field(min_length=1)
    summary: str = Field(min_length=1)


class FinancialPdfAnalysis(BaseModel):
    file_name: str
    page_count: int
    report: FinancialDocumentReport
    limitations: list[str]

