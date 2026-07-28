from datetime import date

from pydantic import BaseModel, ConfigDict


class StockBasicInfo(BaseModel):
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    current_price: float | None
    market_cap: int | None
    trailing_pe: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None


class StockHistoryItem(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "One year of daily stock data"})

    symbol: str
    basic_info: StockBasicInfo
    history: list[StockHistoryItem]
