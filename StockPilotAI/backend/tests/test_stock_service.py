from datetime import date

import pandas as pd
import pytest

from app.services.stock_service import (
    StockDataProviderError,
    StockNotFoundError,
    StockService,
)


class FakeTicker:
    info = {
        "currentPrice": 210.5,
        "marketCap": 3_100_000_000_000,
        "trailingPE": 31.2,
        "fiftyTwoWeekHigh": 220.0,
        "fiftyTwoWeekLow": 160.0,
    }

    def history(self, **_kwargs: object) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Open": [208.0, 210.0],
                "High": [212.0, 214.0],
                "Low": [207.5, 209.0],
                "Close": [210.5, 213.0],
                "Volume": [48_000_000, 45_000_000],
            },
            index=pd.to_datetime(["2026-07-27", "2026-07-28"]),
        )


class EmptyTicker:
    info: dict[str, object] = {}

    def history(self, **_kwargs: object) -> pd.DataFrame:
        return pd.DataFrame()


class FailingTicker:
    @property
    def info(self) -> dict[str, object]:
        raise RuntimeError("upstream unavailable")

    def history(self, **_kwargs: object) -> pd.DataFrame:
        raise RuntimeError("upstream unavailable")


def test_stock_service_builds_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.stock_service.yf.Ticker", lambda _symbol: FakeTicker())

    result = StockService().get_stock("AAPL")

    assert result.symbol == "AAPL"
    assert result.basic_info.current_price == 210.5
    assert result.basic_info.market_cap == 3_100_000_000_000
    assert result.history[-1].date == date(2026, 7, 28)
    assert result.history[-1].close == 213.0
    assert result.history[-1].volume == 45_000_000


def test_stock_service_rejects_empty_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.stock_service.yf.Ticker", lambda _symbol: EmptyTicker())

    with pytest.raises(StockNotFoundError):
        StockService().get_stock("UNKNOWN")


def test_stock_service_wraps_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.stock_service.yf.Ticker", lambda _symbol: FailingTicker())

    with pytest.raises(StockDataProviderError):
        StockService().get_stock("AAPL")

