import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User

JOURNAL_JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class InvestmentJournal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investment_journals"
    __table_args__ = (
        CheckConstraint(
            "action IN ('buy', 'sell', 'hold', 'watch')",
            name="valid_action",
        ),
        CheckConstraint("symbol = upper(symbol)", name="symbol_uppercase"),
        Index("ix_investment_journals_user_date", "user_id", "entry_date"),
        Index("ix_investment_journals_symbol_date", "symbol", "entry_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    thesis: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float | None] = mapped_column(Numeric(18, 4))
    review_date: Mapped[date | None] = mapped_column(Date)
    outcome_notes: Mapped[str | None] = mapped_column(Text)
    ai_review: Mapped[dict[str, Any] | None] = mapped_column(JOURNAL_JSON_TYPE)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="investment_journals")
