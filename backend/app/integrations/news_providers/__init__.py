"""Provider-neutral contracts for external news integrations."""

from app.integrations.news_providers.base import NewsProvider, NewsProviderArticle

__all__ = ["NewsProvider", "NewsProviderArticle"]

