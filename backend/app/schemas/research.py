from pydantic import BaseModel, Field


class InvestmentResearchReport(BaseModel):
    company_overview: str = Field(min_length=1)
    current_trend: str = Field(min_length=1)
    technical_analysis: str = Field(min_length=1)
    news_impact: str = Field(min_length=1)
    risk_factors: list[str] = Field(min_length=1)
    summary: str = Field(min_length=1)

