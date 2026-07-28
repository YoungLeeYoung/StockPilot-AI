import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User

REPORT_JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class AnalysisHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analysis_history"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="valid_status",
        ),
        Index("ix_analysis_history_user_created", "user_id", "created_at"),
        Index("ix_analysis_history_symbol_created", "symbol", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    model_name: Mapped[str | None] = mapped_column(String(120))
    report: Mapped[dict[str, Any] | None] = mapped_column(REPORT_JSON_TYPE)
    agent_trace: Mapped[list[dict[str, Any]] | None] = mapped_column(REPORT_JSON_TYPE)
    error_message: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="analysis_history")
