import re
from collections.abc import Sequence
from datetime import UTC, datetime

from app.integrations.news_providers import NewsProvider, NewsProviderArticle
from app.schemas.news import NewsArticle

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-^=]{0,19}$")


class NewsServiceError(Exception):
    """Base exception for news service failures."""


class InvalidNewsRequestError(NewsServiceError, ValueError):
    """Raised when a symbol or result limit is invalid."""


class NewsProviderError(NewsServiceError):
    """Raised when the configured news provider fails."""


class NewsService:
    def __init__(self, provider: NewsProvider) -> None:
        self.provider = provider

    async def get_recent_news(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[NewsArticle]:
        normalized_symbol = self._normalize_symbol(symbol)
        if not 1 <= limit <= 50:
            raise InvalidNewsRequestError("News result limit must be between 1 and 50.")

        try:
            provider_articles = await self.provider.fetch_recent_news(
                symbol=normalized_symbol,
                limit=limit,
            )
        except Exception as exc:
            raise NewsProviderError(
                f"Unable to retrieve news for {normalized_symbol}."
            ) from exc

        articles = self._normalize_articles(provider_articles)
        articles.sort(key=lambda article: article.date, reverse=True)
        return articles[:limit]

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not SYMBOL_PATTERN.fullmatch(normalized):
            raise InvalidNewsRequestError("Invalid stock symbol.")
        return normalized

    def _normalize_articles(
        self,
        provider_articles: Sequence[NewsProviderArticle],
    ) -> list[NewsArticle]:
        if isinstance(provider_articles, (str, bytes)) or not isinstance(
            provider_articles, Sequence
        ):
            raise NewsProviderError("News provider returned an invalid response.")

        articles: list[NewsArticle] = []
        seen: set[tuple[str, str]] = set()
        for item in provider_articles:
            if not isinstance(item, NewsProviderArticle):
                raise NewsProviderError("News provider returned an invalid article.")

            title = " ".join(item.title.split())
            source = " ".join(item.source.split())
            summary = " ".join(item.summary.split())
            if not title or not source or not summary:
                continue

            identity = (title.casefold(), source.casefold())
            if identity in seen:
                continue
            seen.add(identity)

            articles.append(
                NewsArticle(
                    title=title,
                    source=source,
                    date=self._to_utc(item.published_at),
                    summary=summary,
                )
            )
        return articles

    @staticmethod
    def _to_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
