"""SQLAlchemy ORM models mapping domain entities to PostgreSQL tables."""

import datetime
import decimal
import uuid

import sqlalchemy as sa
import sqlalchemy.orm as orm

import ledger.infrastructure.database as database

ACCOUNT_TYPE_VALUES = ("ASSET", "LIABILITY", "REVENUE", "EXPENSE")
ENTRY_TYPE_VALUES = ("DEBIT", "CREDIT")


class AccountModel(database.Base):
    """ORM model for the accounts table."""

    __tablename__ = "accounts"

    id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        unique=True,
        nullable=False,
    )
    type: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        nullable=False,
    )
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        sa.CheckConstraint(
            sa.column("type").in_(ACCOUNT_TYPE_VALUES),
            name="ck_accounts_type",
        ),
    )


class TransactionModel(database.Base):
    """ORM model for the transactions table."""

    __tablename__ = "transactions"

    id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    timestamp: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    description: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        nullable=False,
    )
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    entries: orm.Mapped[list["TransactionEntryModel"]] = orm.relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TransactionEntryModel(database.Base):
    """ORM model for the transaction_entries table."""

    __tablename__ = "transaction_entries"

    id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    transaction_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sa.ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    type: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        nullable=False,
    )
    amount: orm.Mapped[decimal.Decimal] = orm.mapped_column(
        sa.Numeric,
        nullable=False,
    )

    transaction: orm.Mapped["TransactionModel"] = orm.relationship(
        back_populates="entries",
    )

    __table_args__ = (
        sa.CheckConstraint(
            sa.column("type").in_(ENTRY_TYPE_VALUES),
            name="ck_transaction_entries_type",
        ),
        sa.CheckConstraint(
            sa.column("amount") > 0,
            name="ck_transaction_entries_amount_positive",
        ),
    )
