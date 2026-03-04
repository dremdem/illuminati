"""Mappers converting between domain entities and SQLAlchemy ORM models."""

import ledger.domain.enums as enums
import ledger.domain.models as domain_models
import ledger.infrastructure.models as orm_models


def account_to_orm(account: domain_models.Account) -> orm_models.AccountModel:
    """
    Convert a domain Account to an ORM AccountModel.

    :param account: domain account entity
    :return: ORM account model
    """
    return orm_models.AccountModel(
        id=account.id,
        name=account.name,
        account_type=account.type.value,
    )


def account_to_domain(row: orm_models.AccountModel) -> domain_models.Account:
    """
    Convert an ORM AccountModel to a domain Account.

    :param row: ORM account model
    :return: domain account entity
    """
    return domain_models.Account(
        id=row.id,
        name=row.name,
        type=enums.AccountType(row.account_type),
    )


def entry_to_orm(
    entry: domain_models.TransactionEntry,
) -> orm_models.TransactionEntryModel:
    """
    Convert a domain TransactionEntry to an ORM TransactionEntryModel.

    :param entry: domain transaction entry
    :return: ORM transaction entry model
    """
    return orm_models.TransactionEntryModel(
        id=entry.id,
        transaction_id=entry.transaction_id,
        account_id=entry.account_id,
        entry_type=entry.type.value,
        amount=entry.amount,
    )


def entry_to_domain(
    row: orm_models.TransactionEntryModel,
) -> domain_models.TransactionEntry:
    """
    Convert an ORM TransactionEntryModel to a domain TransactionEntry.

    :param row: ORM transaction entry model
    :return: domain transaction entry
    """
    return domain_models.TransactionEntry(
        id=row.id,
        transaction_id=row.transaction_id,
        account_id=row.account_id,
        type=enums.EntryType(row.entry_type),
        amount=row.amount,
    )


def transaction_to_orm(
    txn: domain_models.Transaction,
) -> orm_models.TransactionModel:
    """
    Convert a domain Transaction to an ORM TransactionModel with entries.

    :param txn: domain transaction entity
    :return: ORM transaction model with attached entry models
    """
    orm_txn = orm_models.TransactionModel(
        id=txn.id,
        timestamp=txn.timestamp,
        description=txn.description,
    )
    orm_txn.entries = [entry_to_orm(e) for e in txn.entries]
    return orm_txn


def transaction_to_domain(
    row: orm_models.TransactionModel,
) -> domain_models.Transaction:
    """
    Convert an ORM TransactionModel to a domain Transaction with entries.

    :param row: ORM transaction model with loaded entries
    :return: domain transaction entity
    """
    return domain_models.Transaction(
        id=row.id,
        timestamp=row.timestamp,
        description=row.description,
        entries=[entry_to_domain(e) for e in row.entries],
    )
