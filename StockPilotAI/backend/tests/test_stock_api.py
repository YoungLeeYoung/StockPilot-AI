from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.stock import StockBasicInfo, StockHistoryItem, StockResponse
from app.services.stock_service import (
    StockDataProviderError,
    StockNotFoundError,
    get_stock_service,
)


class FakeStockService:
    def get_stock(self, symbol: str) -> StockResponse:
        return StockResponse(
            symbol=symbol,
            basic_info=StockBasicInfo(
                current_price=210.5,
                market_cap=3_100_000_000_000,
                trailing_pe=31.2,
                fifty_two_week_high=220.0,
                fifty_two_week_low=160.0,
            ),
            history=[
                StockHistoryItem(
                    date=date(2026, 7, 27),
                    open=208.0,
                    high=212.0,
                    low=207.5,
                    close=210.5,
                    volume=48_000_000,
                )
            ],
        )


class MissingStockService:
    def get_stock(self, symbol: str) -> StockResponse:
        raise StockNotFoundError(f"No stock data found for symbol {symbol}.")


class FailingStockService:
    def get_stock(self, symbol: str) -> StockResponse:
        raise StockDataProviderError(f"Unable to retrieve data for {symbol}.")


def test_get_stock() -> None:
    app.dependency_overrides[get_stock_service] = FakeStockService
    client = TestClient(app)

    response = client.get("/api/v1/stock/aapl")

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    assert response.json()["basic_info"]["current_price"] == 210.5
    assert response.json()["history"][0]["volume"] == 48_000_000
    app.dependency_overrides.clear()


def test_stock_not_found() -> None:
    app.dependency_overrides[get_stock_service] = MissingStockService
    client = TestClient(app)

    response = client.get("/api/v1/stock/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "stock_not_found"
    app.dependency_overrides.clear()


def test_stock_provider_error() -> None:
    app.dependency_overrides[get_stock_service] = FailingStockService
    client = TestClient(app)

    response = client.get("/api/v1/stock/AAPL")

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "stock_provider_error"
    app.dependency_overrides.clear()


def test_invalid_stock_symbol() -> None:
    response = TestClient(app).get("/api/v1/stock/AAPL%20INVALID")

    assert response.status_code == 422

