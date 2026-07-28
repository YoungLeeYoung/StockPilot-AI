from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NewsProviderArticle:
    """Normalized article produced by a provider adapter."""

    title: str
    source: str
    published_at: datetime
    summary: str


class NewsProvider(Protocol):
    """Contract implemented by each external news API adapter."""

    async def fetch_recent_news(
        self,
        symbol: str,
        limit: int,
    ) -> Sequence[NewsProviderArticle]: ...

