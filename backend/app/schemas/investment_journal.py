import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvestmentJournalCreate(BaseModel):
    user_id: uuid.UUID
    entry_date: date
    action: Literal["buy", "sell", "hold", "watch"]
    symbol: str = Field(min_length=1, max_length=20)
    reason: str = Field(min_length=1, max_length=4000)
    thesis: str | None = Field(default=None, max_length=8000)
    price: float | None = Field(default=None, gt=0)
    review_date: date | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class InvestmentJournalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    entry_date: date
    action: str
    symbol: str
    reason: str
    thesis: str | None
    price: float | None
    review_date: date | None
    outcome_notes: str | None
    ai_review: dict[str, object] | None
    reviewed_at: datetime | None
    created_at: datetime


class JournalReviewRequest(BaseModel):
    outcome_notes: str | None = Field(default=None, max_length=8000)


class JournalAiReview(BaseModel):
    decision_context: str = Field(min_length=1)
    what_changed: str = Field(min_length=1)
    lessons: list[str] = Field(min_length=1)
    review_questions: list[str] = Field(min_length=1)
    risk_flags: list[str]

