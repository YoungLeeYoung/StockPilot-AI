"""Create initial StockPilot AI schema.

Revision ID: 20260728_0001
Revises:
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260728_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "analysis_history",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("agent_trace", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="valid_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_analysis_history_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_history"),
    )
    op.create_index(
        "ix_analysis_history_symbol_created",
        "analysis_history",
        ["symbol", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_history_user_created",
        "analysis_history",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "investment_journals",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("ai_review", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('buy', 'sell', 'hold', 'watch')",
            name="valid_action",
        ),
        sa.CheckConstraint(
            "symbol = upper(symbol)",
            name="symbol_uppercase",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_investment_journals_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investment_journals"),
    )
    op.create_index(
        "ix_investment_journals_symbol_date",
        "investment_journals",
        ["symbol", "entry_date"],
        unique=False,
    )
    op.create_index(
        "ix_investment_journals_user_date",
        "investment_journals",
        ["user_id", "entry_date"],
        unique=False,
    )

    op.create_table(
        "watchlists",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "symbol = upper(symbol)",
            name="symbol_uppercase",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_watchlists_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_watchlists"),
        sa.UniqueConstraint("user_id", "symbol", name="uq_watchlists_user_symbol"),
    )
    op.create_index("ix_watchlists_symbol", "watchlists", ["symbol"], unique=False)
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_watchlists_user_id", table_name="watchlists")
    op.drop_index("ix_watchlists_symbol", table_name="watchlists")
    op.drop_table("watchlists")

    op.drop_index(
        "ix_investment_journals_user_date",
        table_name="investment_journals",
    )
    op.drop_index(
        "ix_investment_journals_symbol_date",
        table_name="investment_journals",
    )
    op.drop_table("investment_journals")

    op.drop_index("ix_analysis_history_user_created", table_name="analysis_history")
    op.drop_index("ix_analysis_history_symbol_created", table_name="analysis_history")
    op.drop_table("analysis_history")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
