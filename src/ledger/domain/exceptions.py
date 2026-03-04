class DomainError(Exception):
    """Base exception for all domain-layer errors."""


class InvalidTransactionError(DomainError):
    """Raised when a transaction violates structural rules."""


class UnbalancedTransactionError(DomainError):
    """Raised when total debits do not equal total credits."""


class AccountNotFoundError(DomainError):
    """Raised when a referenced account does not exist."""


class DuplicateAccountError(DomainError):
    """Raised when creating an account with a name that already exists."""
