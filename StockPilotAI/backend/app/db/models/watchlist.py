import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Watchlist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_watchlists_user_symbol"),
        CheckConstraint("symbol = upper(symbol)", name="symbol_uppercase"),
        Index("ix_watchlists_user_id", "user_id"),
        Index("ix_watchlists_symbol", "symbol"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["User"] = relationship(back_populates="watchlist")

