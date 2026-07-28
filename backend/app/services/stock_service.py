import logging
import math
from functools import lru_cache
from typing import Any

import yfinance as yf

from app.schemas.stock import StockBasicInfo, StockHistoryItem, StockResponse

logger = logging.getLogger(__name__)


class StockServiceError(Exception):
    """Base exception for stock data failures."""


class StockNotFoundError(StockServiceError):
    """Raised when a symbol has no usable market data."""


class StockDataProviderError(StockServiceError):
    """Raised when the upstream stock provider cannot be reached or parsed."""


class StockService:
    history_period = "1y"
    history_interval = "1d"

    def get_stock(self, symbol: str) -> StockResponse:
        try:
            ticker = yf.Ticker(symbol)
            history_frame = ticker.history(
                period=self.history_period,
                interval=self.history_interval,
                auto_adjust=False,
                actions=False,
            )
            info = ticker.info or {}
        except Exception as exc:
            logger.exception("yfinance request failed for symbol %s", symbol)
            raise StockDataProviderError(f"Unable to retrieve data for {symbol}.") from exc

        history = self._build_history(history_frame)
        if not history:
            raise StockNotFoundError(f"No stock data found for symbol {symbol}.")

        basic_info = StockBasicInfo(
            company_name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            current_price=self._first_number(
                info,
                "currentPrice",
                "regularMarketPrice",
                fallback=history[-1].close,
            ),
            market_cap=self._optional_int(info.get("marketCap")),
            trailing_pe=self._optional_float(info.get("trailingPE")),
            fifty_two_week_high=self._first_number(
                info,
                "fiftyTwoWeekHigh",
                fallback=max(item.high for item in history),
            ),
            fifty_two_week_low=self._first_number(
                info,
                "fiftyTwoWeekLow",
                fallback=min(item.low for item in history),
            ),
        )

        return StockResponse(symbol=symbol, basic_info=basic_info, history=history)

    def _build_history(self, history_frame: Any) -> list[StockHistoryItem]:
        if history_frame is None or history_frame.empty:
            return []

        items: list[StockHistoryItem] = []
        for timestamp, row in history_frame.iterrows():
            open_price = self._optional_float(row.get("Open"))
            high = self._optional_float(row.get("High"))
            low = self._optional_float(row.get("Low"))
            close = self._optional_float(row.get("Close"))

            if None in (open_price, high, low, close):
                continue

            volume = self._optional_int(row.get("Volume"))
            items.append(
                StockHistoryItem(
                    date=timestamp.date(),
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume or 0,
                )
            )

        return items

    @classmethod
    def _first_number(
        cls,
        values: dict[str, Any],
        *keys: str,
        fallback: float | None = None,
    ) -> float | None:
        for key in keys:
            value = cls._optional_float(values.get(key))
            if value is not None:
                return value
        return fallback

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if math.isfinite(result) else None

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        number = StockService._optional_float(value)
        return int(number) if number is not None else None


@lru_cache
def get_stock_service() -> StockService:
    return StockService()
