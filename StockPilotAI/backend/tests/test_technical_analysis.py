from datetime import date, timedelta

import pandas as pd
import pytest

from app.schemas.stock import StockHistoryItem
from app.services.technical_analysis import (
    TechnicalAnalysisError,
    TechnicalAnalysisService,
)


def test_bullish_analysis_calculates_all_indicators() -> None:
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2026-04-01", periods=60),
            "Close": [100.0 + index for index in range(60)],
        }
    ).rename(columns={"Date": "date"})

    service = TechnicalAnalysisService()
    indicators = service.calculate_indicators(history)
    report = service.analyze(history)

    assert indicators.iloc[-1]["ma20"] == pytest.approx(149.5)
    assert indicators.iloc[-1]["ma50"] == pytest.approx(134.5)
    assert indicators.iloc[-1]["rsi"] == pytest.approx(100.0)
    assert indicators.iloc[-1]["macd"] > indicators.iloc[-1]["macd_signal"]
    assert pd.notna(indicators.iloc[-1]["bollinger_upper"])
    assert pd.notna(indicators.iloc[-1]["bollinger_lower"])
    assert report.model_dump() == {
        "trend": "bullish",
        "signals": [
            "price above MA20",
            "MA20 above MA50",
            "MACD above signal line",
        ],
        "risk": ["RSI overbought"],
    }


def test_bearish_analysis_accepts_stock_history_items() -> None:
    start = date(2026, 4, 1)
    history = [
        StockHistoryItem(
            date=start + timedelta(days=index),
            open=160.0 - index,
            high=161.0 - index,
            low=158.0 - index,
            close=159.0 - index,
            volume=1_000_000,
        )
        for index in range(60)
    ]

    report = TechnicalAnalysisService().analyze(history)

    assert report.trend == "bearish"
    assert report.signals == [
        "price below MA20",
        "MA20 below MA50",
        "MACD below signal line",
    ]
    assert "RSI oversold" in report.risk


def test_flat_history_is_neutral_without_risk() -> None:
    history = pd.DataFrame({"Close": [100.0] * 60})

    report = TechnicalAnalysisService().analyze(history)

    assert report.trend == "neutral"
    assert report.risk == []


def test_analysis_requires_fifty_valid_prices() -> None:
    history = pd.DataFrame({"Close": [100.0] * 49})

    with pytest.raises(TechnicalAnalysisError, match="At least 50"):
        TechnicalAnalysisService().analyze(history)


def test_analysis_requires_close_column() -> None:
    history = pd.DataFrame({"Open": [100.0] * 60})

    with pytest.raises(TechnicalAnalysisError, match="Close column"):
        TechnicalAnalysisService().analyze(history)

