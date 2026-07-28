from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FinancialReportSnapshot:
    symbol: str
    company_name: str
    fiscal_period: str
    currency: str
    sector: str | None = None
    industry: str | None = None
    metrics: dict[str, float | int | None] = field(default_factory=dict)
    source: str | None = None


class FinancialReportProvider(Protocol):
    async def fetch_financial_report(self, symbol: str) -> FinancialReportSnapshot: ...

