import json
from datetime import date
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.agents.contracts import AgentModelResponse, AgentToolDefinition
from app.db import Base, User
from app.schemas.investment_journal import InvestmentJournalCreate
from app.services.investment_journal import (
    InvestmentJournalReviewService,
    InvestmentJournalService,
)


class JournalReviewModel:
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[AgentToolDefinition],
    ) -> AgentModelResponse:
        assert "Dividend" in messages[-1]["content"]
        return AgentModelResponse(
            content=json.dumps(
                {
                    "decision_context": "MO was purchased for dividend income.",
                    "what_changed": "The investor later reviewed dividend sustainability.",
                    "lessons": ["Record expected dividend coverage at entry."],
                    "review_questions": ["Did free cash flow cover the dividend?"],
                    "risk_flags": ["Single-factor thesis"],
                }
            )
        )


@pytest.mark.asyncio
async def test_journal_persists_original_decision_and_ai_review() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    service = InvestmentJournalService()

    with Session(engine) as session:
        user = User(email="journal@example.com")
        session.add(user)
        session.commit()
        entry = service.create(
            session,
            InvestmentJournalCreate(
                user_id=user.id,
                entry_date=date(2026, 7, 28),
                action="buy",
                symbol="mo",
                reason="Dividend",
                review_date=date(2027, 1, 28),
            ),
        )

        review = await InvestmentJournalReviewService(JournalReviewModel()).review(
            entry,
            "Dividend remained covered by cash flow.",
        )
        stored = service.save_review(
            session,
            entry,
            review,
            "Dividend remained covered by cash flow.",
        )

        assert stored.symbol == "MO"
        assert stored.reason == "Dividend"
        assert stored.ai_review is not None
        assert stored.ai_review["risk_flags"] == ["Single-factor thesis"]
        assert service.list_for_user(session, user.id, symbol="MO") == [stored]

