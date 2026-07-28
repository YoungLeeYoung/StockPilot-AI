import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from starlette.concurrency import run_in_threadpool

from app.schemas.stock import StockResponse
from app.services.stock_service import (
    StockDataProviderError,
    StockNotFoundError,
    StockService,
    get_stock_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()

StockSymbol = Annotated[
    str,
    Path(
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9.\-^=]*$",
        description="Exchange ticker symbol, for example AAPL or BRK-B",
    ),
]


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: StockSymbol,
    service: Annotated[StockService, Depends(get_stock_service)],
) -> StockResponse:
    normalized_symbol = symbol.strip().upper()

    try:
        return await run_in_threadpool(service.get_stock, normalized_symbol)
    except StockNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "stock_not_found", "message": str(exc)},
        ) from exc
    except StockDataProviderError as exc:
        logger.warning("Stock provider failed for %s: %s", normalized_symbol, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "stock_provider_error",
                "message": "Stock data is temporarily unavailable.",
            },
        ) from exc

