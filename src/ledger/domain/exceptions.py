class DomainError(Exception):
    pass


class InvalidTransactionError(DomainError):
    pass


class UnbalancedTransactionError(DomainError):
    pass


class AccountNotFoundError(DomainError):
    pass


class DuplicateAccountError(DomainError):
    pass
