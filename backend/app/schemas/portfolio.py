from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PortfolioHolding(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    weight: float = Field(gt=0, le=100)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Symbol cannot be empty.")
        return normalized


class PortfolioAnalysisRequest(BaseModel):
    holdings: list[PortfolioHolding] = Field(min_length=2, max_length=50)

    @model_validator(mode="after")
    def validate_portfolio(self) -> "PortfolioAnalysisRequest":
        symbols = [holding.symbol for holding in self.holdings]
        if len(set(symbols)) != len(symbols):
            raise ValueError("Portfolio symbols must be unique.")
        total_weight = sum(holding.weight for holding in self.holdings)
        if abs(total_weight - 100) > 0.01:
            raise ValueError("Portfolio weights must total 100%.")
        return self


class PortfolioAnalysisReport(BaseModel):
    sector_concentration: dict[str, float]
    largest_position: PortfolioHolding
    concentration_hhi: float
    annualized_volatility: float
    risk_level: Literal["low", "moderate", "high"]
    risk_factors: list[str]
    observations: list[str]
    data_points: int


class PortfolioAiAnalysis(BaseModel):
    industry_concentration: str = Field(min_length=1)
    risk: str = Field(min_length=1)
    volatility: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class PortfolioResearchResult(BaseModel):
    quantitative: PortfolioAnalysisReport
    ai_analysis: PortfolioAiAnalysis
