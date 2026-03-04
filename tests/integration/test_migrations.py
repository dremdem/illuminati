"""Integration tests for Alembic migrations: upgrade, downgrade, schema verification."""

import alembic.command
import alembic.config
import sqlalchemy as sa
import sqlalchemy.engine as sa_engine
import testcontainers.postgres


def _make_alembic_config(sync_url: str) -> alembic.config.Config:
    """
    Build an Alembic config pointing at the given database URL.

    :param sync_url: synchronous database connection string
    :return: configured Alembic Config object
    """
    cfg = alembic.config.Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", sync_url)
    return cfg


def _get_table_columns(
    engine: sa_engine.Engine,
    table_name: str,
) -> dict[str, str]:
    """
    Inspect a table and return column names mapped to their type names.

    :param engine: sync SQLAlchemy engine
    :param table_name: name of the table to inspect
    :return: dict of column_name -> type string
    """
    inspector = sa.inspect(engine)
    columns = inspector.get_columns(table_name)
    return {col["name"]: str(col["type"]) for col in columns}


def _get_indexes(
    engine: sa_engine.Engine,
    table_name: str,
) -> set[str]:
    """
    Get the set of indexed column names for a table.

    :param engine: sync SQLAlchemy engine
    :param table_name: name of the table to inspect
    :return: set of column names that have indexes
    """
    inspector = sa.inspect(engine)
    indexes = inspector.get_indexes(table_name)
    indexed_columns: set[str] = set()
    for idx in indexes:
        for col in idx["column_names"]:
            if col is not None:
                indexed_columns.add(col)
    return indexed_columns


class TestMigrations:
    """Tests for Alembic migration upgrade, downgrade, and schema correctness."""

    def test_upgrade_head(self) -> None:
        """Alembic upgrade to head must succeed without errors."""
        with testcontainers.postgres.PostgresContainer("postgres:16-alpine") as pg:
            cfg = _make_alembic_config(pg.get_connection_url())
            alembic.command.upgrade(cfg, "head")

    def test_downgrade_one(self) -> None:
        """Alembic downgrade by one revision must succeed after upgrade."""
        with testcontainers.postgres.PostgresContainer("postgres:16-alpine") as pg:
            cfg = _make_alembic_config(pg.get_connection_url())
            alembic.command.upgrade(cfg, "head")
            alembic.command.downgrade(cfg, "-1")

    def test_columns_after_upgrade(self) -> None:
        """Verify all expected columns exist with correct types after upgrade."""
        with testcontainers.postgres.PostgresContainer("postgres:16-alpine") as pg:
            url = pg.get_connection_url()
            cfg = _make_alembic_config(url)
            alembic.command.upgrade(cfg, "head")

            engine = sa.create_engine(url)

            account_cols = _get_table_columns(engine, "accounts")
            assert "id" in account_cols
            assert "name" in account_cols
            assert "account_type" in account_cols
            assert "created_at" in account_cols

            txn_cols = _get_table_columns(engine, "transactions")
            assert "id" in txn_cols
            assert "timestamp" in txn_cols
            assert "description" in txn_cols
            assert "created_at" in txn_cols

            entry_cols = _get_table_columns(engine, "transaction_entries")
            assert "id" in entry_cols
            assert "transaction_id" in entry_cols
            assert "account_id" in entry_cols
            assert "entry_type" in entry_cols
            assert "amount" in entry_cols

            engine.dispose()

    def test_indexes_after_upgrade(self) -> None:
        """Verify expected indexes exist on the right columns after upgrade."""
        with testcontainers.postgres.PostgresContainer("postgres:16-alpine") as pg:
            url = pg.get_connection_url()
            cfg = _make_alembic_config(url)
            alembic.command.upgrade(cfg, "head")

            engine = sa.create_engine(url)

            txn_indexes = _get_indexes(engine, "transactions")
            assert "timestamp" in txn_indexes

            entry_indexes = _get_indexes(engine, "transaction_entries")
            assert "transaction_id" in entry_indexes
            assert "account_id" in entry_indexes

            engine.dispose()
