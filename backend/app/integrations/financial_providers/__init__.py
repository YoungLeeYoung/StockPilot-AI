"""Provider-neutral contracts for company financial data."""

from app.integrations.financial_providers.base import (
    FinancialReportProvider,
    FinancialReportSnapshot,
)

__all__ = ["FinancialReportProvider", "FinancialReportSnapshot"]

