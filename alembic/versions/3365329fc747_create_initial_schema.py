"""create initial schema

Revision ID: 3365329fc747
Revises:
Create Date: 2026-03-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3365329fc747"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type IN ('ASSET', 'LIABILITY', 'REVENUE', 'EXPENSE')",
            name="ck_accounts_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transactions_timestamp"),
        "transactions",
        ["timestamp"],
        unique=False,
    )
    op.create_table(
        "transaction_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.CheckConstraint(
            "type IN ('DEBIT', 'CREDIT')",
            name="ck_transaction_entries_type",
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_transaction_entries_amount_positive",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transaction_entries_account_id"),
        "transaction_entries",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transaction_entries_transaction_id"),
        "transaction_entries",
        ["transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_transaction_entries_transaction_id"),
        table_name="transaction_entries",
    )
    op.drop_index(
        op.f("ix_transaction_entries_account_id"),
        table_name="transaction_entries",
    )
    op.drop_table("transaction_entries")
    op.drop_index(
        op.f("ix_transactions_timestamp"),
        table_name="transactions",
    )
    op.drop_table("transactions")
    op.drop_table("accounts")
