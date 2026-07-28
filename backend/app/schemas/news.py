from datetime import datetime

from pydantic import BaseModel


class NewsArticle(BaseModel):
    title: str
    source: str
    date: datetime
    summary: str

