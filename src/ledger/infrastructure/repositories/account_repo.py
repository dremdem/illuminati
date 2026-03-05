"""SQLAlchemy-based account repository implementation."""

import decimal
import uuid

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
import sqlalchemy.ext.asyncio as sa_async

import ledger.domain.enums as enums
import ledger.domain.exceptions as exceptions
import ledger.domain.models as models
import ledger.infrastructure.mappers as mappers
import ledger.infrastructure.models as orm_models


class SqlaAccountRepository:
    """Account repository backed by SQLAlchemy async sessions."""

    def __init__(self, session: sa_async.AsyncSession) -> None:
        """
        Initialise the repository with a database session.

        :param session: async SQLAlchemy session
        """
        self._session = session

    async def create(self, account: models.Account) -> models.Account:
        """
        Persist a new account.

        :param account: domain account to persist
        :return: the persisted account
        :raises DuplicateAccountError: if an account with the same name exists
        """
        orm_account = mappers.account_to_orm(account)
        self._session.add(orm_account)
        try:
            await self._session.flush()
        except sa_exc.IntegrityError as err:
            await self._session.rollback()
            raise exceptions.DuplicateAccountError(
                f"Account with name '{account.name}' already exists"
            ) from err
        return mappers.account_to_domain(orm_account)

    async def get_by_id(self, account_id: uuid.UUID) -> models.Account | None:
        """
        Retrieve an account by its unique identifier.

        :param account_id: UUID of the account
        :return: the account, or None if not found
        """
        row = await self._session.get(orm_models.AccountModel, account_id)
        if row is None:
            return None
        else:
            return mappers.account_to_domain(row)

    async def get_all(self) -> list[models.Account]:
        """
        Retrieve all accounts.

        :return: list of all accounts
        """
        result = await self._session.execute(sa.select(orm_models.AccountModel))
        rows = result.scalars().all()
        return [mappers.account_to_domain(r) for r in rows]

    async def exists(self, account_id: uuid.UUID) -> bool:
        """
        Check whether an account exists using an efficient EXISTS query.

        :param account_id: UUID of the account
        :return: True if the account exists, False otherwise
        """
        stmt = sa.select(sa.exists().where(orm_models.AccountModel.id == account_id))
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def get_with_balance(
        self, account_id: uuid.UUID
    ) -> tuple[models.Account, decimal.Decimal] | None:
        """
        Retrieve an account with its computed balance via SQL aggregation.

        :param account_id: UUID of the account
        :return: tuple of (account, balance), or None if not found
        """
        stmt = (
            sa.select(
                orm_models.AccountModel.id,
                orm_models.AccountModel.name,
                orm_models.AccountModel.account_type,
                self._balance_expression(),
            )
            .outerjoin(
                orm_models.TransactionEntryModel,
                orm_models.TransactionEntryModel.account_id
                == orm_models.AccountModel.id,
            )
            .where(orm_models.AccountModel.id == account_id)
            .group_by(
                orm_models.AccountModel.id,
                orm_models.AccountModel.name,
                orm_models.AccountModel.account_type,
            )
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        else:
            account = models.Account(
                id=row.id,
                name=row.name,
                type=enums.AccountType(row.account_type),
            )
            return account, row.balance

    async def get_all_with_balances(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[tuple[models.Account, decimal.Decimal]], int]:
        """
        Retrieve all accounts with their computed balances via SQL aggregation.

        :param limit: maximum number of accounts to return (None = all)
        :param offset: number of accounts to skip
        :return: tuple of (list of (account, balance) tuples, total count)
        """
        count_result = await self._session.execute(
            sa.select(sa.func.count()).select_from(orm_models.AccountModel)
        )
        total = count_result.scalar_one()

        stmt = (
            sa.select(
                orm_models.AccountModel.id,
                orm_models.AccountModel.name,
                orm_models.AccountModel.account_type,
                self._balance_expression(),
            )
            .outerjoin(
                orm_models.TransactionEntryModel,
                orm_models.TransactionEntryModel.account_id
                == orm_models.AccountModel.id,
            )
            .group_by(
                orm_models.AccountModel.id,
                orm_models.AccountModel.name,
                orm_models.AccountModel.account_type,
            )
            .order_by(orm_models.AccountModel.name)
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        items = [
            (
                models.Account(
                    id=row.id,
                    name=row.name,
                    type=enums.AccountType(row.account_type),
                ),
                row.balance,
            )
            for row in result.all()
        ]
        return items, total

    @staticmethod
    def _balance_expression() -> sa.Label[decimal.Decimal]:
        """
        Build a SQLAlchemy expression for balance computation.

        ASSET and EXPENSE are debit-normal (debits - credits).
        LIABILITY and REVENUE are credit-normal (credits - debits).

        :return: labelled SQL expression computing the balance
        """
        debit_sum = sa.func.coalesce(
            sa.func.sum(
                sa.case(
                    (
                        orm_models.TransactionEntryModel.entry_type
                        == enums.EntryType.DEBIT.value,
                        orm_models.TransactionEntryModel.amount,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        credit_sum = sa.func.coalesce(
            sa.func.sum(
                sa.case(
                    (
                        orm_models.TransactionEntryModel.entry_type
                        == enums.EntryType.CREDIT.value,
                        orm_models.TransactionEntryModel.amount,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        return sa.case(
            (
                orm_models.AccountModel.account_type.in_(
                    [
                        enums.AccountType.ASSET.value,
                        enums.AccountType.EXPENSE.value,
                    ]
                ),
                debit_sum - credit_sum,
            ),
            else_=credit_sum - debit_sum,
        ).label("balance")
