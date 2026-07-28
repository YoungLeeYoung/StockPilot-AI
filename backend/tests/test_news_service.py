from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.integrations.news_providers import NewsProviderArticle
from app.services.news_service import (
    InvalidNewsRequestError,
    NewsProviderError,
    NewsService,
)


class FakeNewsProvider:
    def __init__(self) -> None:
        self.request: tuple[str, int] | None = None

    async def fetch_recent_news(
        self,
        symbol: str,
        limit: int,
    ) -> list[NewsProviderArticle]:
        self.request = (symbol, limit)
        return [
            NewsProviderArticle(
                title="  Apple updates product roadmap  ",
                source="Example Wire",
                published_at=datetime(2026, 7, 27, 9, 0),
                summary="  Management discussed its product roadmap.  ",
            ),
            NewsProviderArticle(
                title="Apple reports quarterly results",
                source="Market Desk",
                published_at=datetime(2026, 7, 28, 8, 0, tzinfo=timezone(timedelta(hours=8))),
                summary="Revenue and margin figures were released.",
            ),
            NewsProviderArticle(
                title="Apple updates product roadmap",
                source="Example Wire",
                published_at=datetime(2026, 7, 26, 9, 0, tzinfo=UTC),
                summary="Duplicate article from the same source.",
            ),
            NewsProviderArticle(
                title="Incomplete article",
                source="Example Wire",
                published_at=datetime(2026, 7, 25, 9, 0, tzinfo=UTC),
                summary="   ",
            ),
        ]


class FailingNewsProvider:
    async def fetch_recent_news(
        self,
        symbol: str,
        limit: int,
    ) -> list[NewsProviderArticle]:
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_news_service_normalizes_sorts_and_deduplicates() -> None:
    provider = FakeNewsProvider()

    articles = await NewsService(provider).get_recent_news(" aapl ", limit=10)

    assert provider.request == ("AAPL", 10)
    assert len(articles) == 2
    assert articles[0].title == "Apple reports quarterly results"
    assert articles[0].date == datetime(2026, 7, 28, 0, 0, tzinfo=UTC)
    assert articles[1].title == "Apple updates product roadmap"
    assert articles[1].summary == "Management discussed its product roadmap."
    assert set(articles[0].model_dump()) == {"title", "source", "date", "summary"}


@pytest.mark.asyncio
async def test_news_service_applies_result_limit() -> None:
    articles = await NewsService(FakeNewsProvider()).get_recent_news("AAPL", limit=1)

    assert len(articles) == 1


@pytest.mark.asyncio
async def test_news_service_rejects_invalid_symbol() -> None:
    with pytest.raises(InvalidNewsRequestError, match="Invalid stock symbol"):
        await NewsService(FakeNewsProvider()).get_recent_news("AAPL INVALID")


@pytest.mark.asyncio
async def test_news_service_rejects_invalid_limit() -> None:
    with pytest.raises(InvalidNewsRequestError, match="between 1 and 50"):
        await NewsService(FakeNewsProvider()).get_recent_news("AAPL", limit=0)


@pytest.mark.asyncio
async def test_news_service_wraps_provider_errors() -> None:
    with pytest.raises(NewsProviderError, match="Unable to retrieve news for AAPL"):
        await NewsService(FailingNewsProvider()).get_recent_news("AAPL")

