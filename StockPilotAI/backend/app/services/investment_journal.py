import json
import uuid
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.contracts import AgentModel
from app.db.models import InvestmentJournal, User
from app.schemas.investment_journal import (
    InvestmentJournalCreate,
    JournalAiReview,
)

JOURNAL_REVIEW_PROMPT = """
You review an investor's historical decision journal.
Separate information known at decision time from later outcomes.
Identify reasoning quality, changed assumptions, lessons, future review questions,
and risk flags. Do not judge only by whether the price later rose or fell.
Do not provide personalized trading instructions.

Return JSON with: decision_context, what_changed, lessons, review_questions, risk_flags.
""".strip()


class InvestmentJournalNotFoundError(LookupError):
    """Raised when a journal entry or owner does not exist."""


class InvestmentJournalService:
    def create(
        self,
        session: Session,
        payload: InvestmentJournalCreate,
    ) -> InvestmentJournal:
        if session.get(User, payload.user_id) is None:
            raise InvestmentJournalNotFoundError("User not found.")
        entry = InvestmentJournal(**payload.model_dump())
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry

    def list_for_user(
        self,
        session: Session,
        user_id: uuid.UUID,
        symbol: str | None = None,
        limit: int = 100,
    ) -> list[InvestmentJournal]:
        statement = (
            select(InvestmentJournal)
            .where(InvestmentJournal.user_id == user_id)
            .order_by(InvestmentJournal.entry_date.desc(), InvestmentJournal.created_at.desc())
            .limit(limit)
        )
        if symbol:
            statement = statement.where(InvestmentJournal.symbol == symbol.strip().upper())
        return list(session.scalars(statement))

    def get(self, session: Session, entry_id: uuid.UUID) -> InvestmentJournal:
        entry = session.get(InvestmentJournal, entry_id)
        if entry is None:
            raise InvestmentJournalNotFoundError("Investment journal entry not found.")
        return entry

    def save_review(
        self,
        session: Session,
        entry: InvestmentJournal,
        review: JournalAiReview,
        outcome_notes: str | None,
    ) -> InvestmentJournal:
        entry.outcome_notes = outcome_notes
        entry.ai_review = review.model_dump(mode="json")
        entry.reviewed_at = datetime.now(UTC)
        session.commit()
        session.refresh(entry)
        return entry


class InvestmentJournalReviewService:
    def __init__(self, model: AgentModel) -> None:
        self.model = model

    async def review(
        self,
        entry: InvestmentJournal,
        outcome_notes: str | None,
    ) -> JournalAiReview:
        context = {
            "entry_date": entry.entry_date.isoformat(),
            "action": entry.action,
            "symbol": entry.symbol,
            "reason": entry.reason,
            "thesis": entry.thesis,
            "price": float(entry.price) if entry.price is not None else None,
            "review_date": entry.review_date.isoformat() if entry.review_date else None,
            "outcome_notes": outcome_notes,
        }
        response = await self.model.complete(
            [
                {"role": "system", "content": JOURNAL_REVIEW_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            [],
        )
        if not response.content or response.tool_calls:
            raise ValueError("LLM returned an invalid journal review response.")
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = "\n".join(content.splitlines()[1:-1]).strip()
            return JournalAiReview.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError("LLM returned an invalid journal review.") from exc
