import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.agents.dependencies import AgentConfigurationError, get_agent_model
from app.db.session import get_db_session
from app.schemas.investment_journal import (
    InvestmentJournalCreate,
    InvestmentJournalRead,
    JournalReviewRequest,
)
from app.services.investment_journal import (
    InvestmentJournalNotFoundError,
    InvestmentJournalReviewService,
    InvestmentJournalService,
)

router = APIRouter()


def get_journal_service() -> InvestmentJournalService:
    return InvestmentJournalService()


@router.post("", response_model=InvestmentJournalRead, status_code=status.HTTP_201_CREATED)
def create_journal(
    payload: InvestmentJournalCreate,
    session: Annotated[Session, Depends(get_db_session)],
    service: Annotated[InvestmentJournalService, Depends(get_journal_service)],
) -> InvestmentJournalRead:
    try:
        return InvestmentJournalRead.model_validate(service.create(session, payload))
    except InvestmentJournalNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=list[InvestmentJournalRead])
def list_journals(
    user_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
    service: Annotated[InvestmentJournalService, Depends(get_journal_service)],
    symbol: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[InvestmentJournalRead]:
    return [
        InvestmentJournalRead.model_validate(entry)
        for entry in service.list_for_user(session, user_id, symbol, limit)
    ]


@router.post("/entries/{entry_id}/review", response_model=InvestmentJournalRead)
async def review_journal(
    entry_id: uuid.UUID,
    payload: JournalReviewRequest,
    session: Annotated[Session, Depends(get_db_session)],
    service: Annotated[InvestmentJournalService, Depends(get_journal_service)],
) -> InvestmentJournalRead:
    try:
        model = get_agent_model()
        entry = service.get(session, entry_id)
        review = await InvestmentJournalReviewService(model).review(
            entry,
            payload.outcome_notes,
        )
        return InvestmentJournalRead.model_validate(
            service.save_review(session, entry, review, payload.outcome_notes)
        )
    except AgentConfigurationError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except InvestmentJournalNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

