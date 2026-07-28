from collections.abc import Sequence
from typing import Literal

import pandas as pd
from pydantic import BaseModel

from app.schemas.stock import StockHistoryItem


class TechnicalAnalysisError(ValueError):
    """Raised when historical data cannot produce a reliable analysis."""


class TechnicalReport(BaseModel):
    trend: Literal["bullish", "bearish", "neutral"]
    signals: list[str]
    risk: list[str]


class TechnicalAnalysisService:
    minimum_periods = 50
    rsi_period = 14

    def analyze(
        self,
        history: pd.DataFrame | Sequence[StockHistoryItem],
    ) -> TechnicalReport:
        indicators = self.calculate_indicators(history)
        latest = indicators.iloc[-1]

        price = float(latest["close"])
        ma20 = float(latest["ma20"])
        ma50 = float(latest["ma50"])
        rsi = float(latest["rsi"])
        macd = float(latest["macd"])
        macd_signal = float(latest["macd_signal"])
        upper_band = float(latest["bollinger_upper"])
        lower_band = float(latest["bollinger_lower"])

        signals = [
            self._relationship_signal(price, ma20, "price", "MA20"),
            self._relationship_signal(ma20, ma50, "MA20", "MA50"),
            self._relationship_signal(macd, macd_signal, "MACD", "signal line"),
        ]

        risk: list[str] = []
        if rsi >= 70:
            risk.append("RSI overbought")
        elif rsi <= 30:
            risk.append("RSI oversold")

        if price > upper_band:
            risk.append("price above upper Bollinger Band")
        elif price < lower_band:
            risk.append("price below lower Bollinger Band")

        trend_score = sum(
            (
                self._direction(price, ma20),
                self._direction(ma20, ma50),
                self._direction(macd, macd_signal),
            )
        )
        if trend_score >= 2:
            trend = "bullish"
        elif trend_score <= -2:
            trend = "bearish"
        else:
            trend = "neutral"

        return TechnicalReport(trend=trend, signals=signals, risk=risk)

    def calculate_indicators(
        self,
        history: pd.DataFrame | Sequence[StockHistoryItem],
    ) -> pd.DataFrame:
        frame = self._prepare_history(history)
        close = frame["close"]

        frame["ma20"] = close.rolling(window=20, min_periods=20).mean()
        frame["ma50"] = close.rolling(window=50, min_periods=50).mean()
        frame["rsi"] = self._calculate_rsi(close)

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        frame["macd"] = ema12 - ema26
        frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()
        frame["macd_histogram"] = frame["macd"] - frame["macd_signal"]

        rolling_std = close.rolling(window=20, min_periods=20).std(ddof=0)
        frame["bollinger_middle"] = frame["ma20"]
        frame["bollinger_upper"] = frame["ma20"] + (2 * rolling_std)
        frame["bollinger_lower"] = frame["ma20"] - (2 * rolling_std)

        required = [
            "ma20",
            "ma50",
            "rsi",
            "macd",
            "macd_signal",
            "bollinger_upper",
            "bollinger_lower",
        ]
        if frame.iloc[-1][required].isna().any():
            raise TechnicalAnalysisError("Historical data cannot produce all indicators.")

        return frame

    def _prepare_history(
        self,
        history: pd.DataFrame | Sequence[StockHistoryItem],
    ) -> pd.DataFrame:
        if isinstance(history, pd.DataFrame):
            frame = history.copy()
            close_column = next(
                (column for column in frame.columns if str(column).lower() == "close"),
                None,
            )
            if close_column is None:
                raise TechnicalAnalysisError("Historical data must contain a Close column.")
            frame = frame.rename(columns={close_column: "close"})
            if "date" in frame.columns:
                frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
                frame = frame.sort_values("date")
            else:
                frame = frame.sort_index()
        else:
            frame = pd.DataFrame(
                {"date": item.date, "close": item.close}
                for item in history
            )
            if frame.empty:
                raise TechnicalAnalysisError("Historical data is empty.")
            frame = frame.sort_values("date")

        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame = frame.dropna(subset=["close"]).reset_index(drop=True)

        if len(frame) < self.minimum_periods:
            raise TechnicalAnalysisError(
                f"At least {self.minimum_periods} valid closing prices are required."
            )
        return frame

    def _calculate_rsi(self, close: pd.Series) -> pd.Series:
        delta = close.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        average_gain = gains.ewm(
            alpha=1 / self.rsi_period,
            min_periods=self.rsi_period,
            adjust=False,
        ).mean()
        average_loss = losses.ewm(
            alpha=1 / self.rsi_period,
            min_periods=self.rsi_period,
            adjust=False,
        ).mean()

        relative_strength = average_gain / average_loss.mask(average_loss == 0)
        rsi = 100 - (100 / (1 + relative_strength))
        rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
        return rsi.mask((average_loss == 0) & (average_gain == 0), 50)

    @staticmethod
    def _direction(left: float, right: float) -> int:
        if left > right:
            return 1
        if left < right:
            return -1
        return 0

    @classmethod
    def _relationship_signal(
        cls,
        left: float,
        right: float,
        left_label: str,
        right_label: str,
    ) -> str:
        direction = cls._direction(left, right)
        if direction > 0:
            return f"{left_label} above {right_label}"
        if direction < 0:
            return f"{left_label} below {right_label}"
        return f"{left_label} at {right_label}"

