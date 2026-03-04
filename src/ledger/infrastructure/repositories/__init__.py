"""Repository implementations for data access."""

import ledger.infrastructure.repositories.account_repo as account_repo
import ledger.infrastructure.repositories.transaction_repo as transaction_repo

SqlaAccountRepository = account_repo.SqlaAccountRepository
SqlaTransactionRepository = transaction_repo.SqlaTransactionRepository

__all__ = ["SqlaAccountRepository", "SqlaTransactionRepository"]
