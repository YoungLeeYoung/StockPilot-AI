from datetime import date

from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import AnalysisHistory, Base, InvestmentJournal, User, Watchlist


def build_test_engine() -> Engine:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


def test_models_persist_relationships_and_json_report() -> None:
    engine = build_test_engine()
    with Session(engine) as session:
        user = User(email="researcher@example.com", display_name="Researcher")
        user.watchlist.append(Watchlist(symbol="NVDA", note="AI infrastructure"))
        user.analysis_history.append(
            AnalysisHistory(
                symbol="NVDA",
                prompt="分析NVDA",
                status="completed",
                model_name="test-model",
                report={
                    "company_overview": "NVIDIA is a technology company.",
                    "risk_factors": ["Valuation"],
                },
                agent_trace=[{"tool": "get_stock_price", "ok": True}],
            )
        )
        user.investment_journals.append(
            InvestmentJournal(
                entry_date=date(2026, 7, 28),
                action="buy",
                symbol="MO",
                reason="Dividend",
            )
        )
        session.add(user)
        session.commit()

        stored = session.scalar(select(User).where(User.email == user.email))
        assert stored is not None
        assert stored.watchlist[0].symbol == "NVDA"
        assert stored.analysis_history[0].report is not None
        assert stored.analysis_history[0].report["risk_factors"] == ["Valuation"]
        assert stored.investment_journals[0].reason == "Dividend"


def test_deleting_user_cascades_owned_records() -> None:
    engine = build_test_engine()
    with Session(engine) as session:
        user = User(email="delete@example.com")
        user.watchlist.append(Watchlist(symbol="AAPL"))
        user.analysis_history.append(
            AnalysisHistory(symbol="AAPL", prompt="分析AAPL", status="pending")
        )
        user.investment_journals.append(
            InvestmentJournal(
                entry_date=date(2026, 7, 28),
                action="buy",
                symbol="AAPL",
                reason="Long-term thesis",
            )
        )
        session.add(user)
        session.commit()

        session.delete(user)
        session.commit()

        assert session.scalar(select(Watchlist)) is None
        assert session.scalar(select(AnalysisHistory)) is None
        assert session.scalar(select(InvestmentJournal)) is None


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) >= {
        "users",
        "watchlists",
        "analysis_history",
        "investment_journals",
    }
