"""Transaction API route handlers: create, get by ID, and get by account."""

import datetime
import typing
import uuid

import fastapi

import ledger.api.dependencies as dependencies
import ledger.api.schemas as schemas
import ledger.application.transaction_service as transaction_service
import ledger.domain.models as models

router = fastapi.APIRouter(prefix="/api/transactions", tags=["transactions"])

account_transactions_router = fastapi.APIRouter(
    prefix="/api/accounts", tags=["transactions"]
)


def _entry_to_response(
    entry: models.TransactionEntry,
) -> schemas.TransactionEntryResponse:
    """
    Map a domain TransactionEntry to an API response schema.

    :param entry: domain transaction entry
    :return: Pydantic response model
    """
    return schemas.TransactionEntryResponse(
        id=str(entry.id),
        account_id=str(entry.account_id),
        type=entry.type,
        amount=f"{entry.amount:.2f}",
    )


def _txn_to_response(
    txn: models.Transaction,
) -> schemas.TransactionResponse:
    """
    Map a domain Transaction to an API response schema.

    :param txn: domain transaction with entries
    :return: Pydantic response model
    """
    return schemas.TransactionResponse(
        id=str(txn.id),
        description=txn.description,
        timestamp=txn.timestamp.isoformat(),
        entries=[_entry_to_response(e) for e in txn.entries],
    )


@router.post(
    "",
    response_model=schemas.TransactionResponse,
    status_code=201,
    response_model_by_alias=True,
    summary="Create transaction",
    description="Create a new double-entry transaction. Requires at least two entries "
    "(one DEBIT and one CREDIT) whose amounts balance exactly. All referenced "
    "accounts must exist.",
    response_description="The created transaction with all entries.",
)
async def create_transaction(
    body: schemas.CreateTransactionRequest,
    service: typing.Annotated[
        transaction_service.TransactionService,
        fastapi.Depends(dependencies.get_transaction_service),
    ],
) -> schemas.TransactionResponse:
    """
    Create a new financial transaction with balanced entries.

    :param body: request body with description, date, and entries
    :param service: injected transaction service
    :return: the created transaction with entries
    """
    entries_data = [
        transaction_service.EntryData(
            account_id=uuid.UUID(entry.account_id),
            type=entry.type,
            amount=entry.amount,
        )
        for entry in body.entries
    ]
    result = await service.create_transaction(
        description=body.description,
        timestamp=body.timestamp,
        entries_data=entries_data,
    )
    return _txn_to_response(result)


@router.get(
    "",
    response_model=schemas.PaginatedTransactionResponse,
    response_model_by_alias=True,
    summary="List transactions",
    description="Retrieve all transactions with optional pagination and date "
    "filtering. Results are ordered by timestamp ascending.",
    response_description="Paginated envelope of transactions with entries.",
)
async def list_transactions(
    service: typing.Annotated[
        transaction_service.TransactionService,
        fastapi.Depends(dependencies.get_transaction_service),
    ],
    limit: typing.Annotated[
        int | None,
        fastapi.Query(
            ge=1, le=100, description="Maximum number of transactions to return."
        ),
    ] = None,
    offset: typing.Annotated[
        int,
        fastapi.Query(ge=0, description="Number of transactions to skip."),
    ] = 0,
    from_date: typing.Annotated[
        datetime.datetime | None,
        fastapi.Query(
            description="Inclusive lower bound on transaction timestamp (ISO 8601)."
        ),
    ] = None,
    to_date: typing.Annotated[
        datetime.datetime | None,
        fastapi.Query(
            description="Inclusive upper bound on transaction timestamp (ISO 8601)."
        ),
    ] = None,
) -> schemas.PaginatedTransactionResponse:
    """
    List all transactions with optional filtering.

    :param service: injected transaction service
    :param limit: maximum number of transactions to return (None = all)
    :param offset: number of transactions to skip
    :param from_date: inclusive lower bound on transaction timestamp
    :param to_date: inclusive upper bound on transaction timestamp
    :return: paginated envelope of transactions with entries
    """
    result = await service.get_all(
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
    )
    return schemas.PaginatedTransactionResponse(
        items=[_txn_to_response(t) for t in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{transaction_id}",
    response_model=schemas.TransactionResponse,
    response_model_by_alias=True,
    summary="Get transaction",
    description="Retrieve a single transaction by its UUID, including all "
    "debit and credit entries.",
    response_description="The transaction with all entries.",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    service: typing.Annotated[
        transaction_service.TransactionService,
        fastapi.Depends(dependencies.get_transaction_service),
    ],
) -> schemas.TransactionResponse:
    """
    Retrieve a single transaction by ID with all entries.

    :param transaction_id: UUID path parameter
    :param service: injected transaction service
    :return: transaction with entries
    """
    result = await service.get_by_id(transaction_id)
    return _txn_to_response(result)


@account_transactions_router.get(
    "/{account_id}/transactions",
    response_model=schemas.PaginatedTransactionResponse,
    response_model_by_alias=True,
    summary="List account transactions",
    description="Retrieve transactions affecting a given account. Supports "
    "pagination via limit/offset and date filtering via from_date/to_date "
    "(inclusive). Results are ordered by timestamp ascending.",
    response_description="Paginated envelope of transactions with all entries.",
)
async def get_account_transactions(
    account_id: uuid.UUID,
    service: typing.Annotated[
        transaction_service.TransactionService,
        fastapi.Depends(dependencies.get_transaction_service),
    ],
    limit: typing.Annotated[
        int | None,
        fastapi.Query(
            ge=1, le=100, description="Maximum number of transactions to return."
        ),
    ] = None,
    offset: typing.Annotated[
        int,
        fastapi.Query(ge=0, description="Number of transactions to skip."),
    ] = 0,
    from_date: typing.Annotated[
        datetime.datetime | None,
        fastapi.Query(
            description="Inclusive lower bound on transaction timestamp (ISO 8601)."
        ),
    ] = None,
    to_date: typing.Annotated[
        datetime.datetime | None,
        fastapi.Query(
            description="Inclusive upper bound on transaction timestamp (ISO 8601)."
        ),
    ] = None,
) -> schemas.PaginatedTransactionResponse:
    """
    Retrieve transactions affecting a given account.

    :param account_id: UUID path parameter for the account
    :param service: injected transaction service
    :param limit: maximum number of transactions to return (None = all)
    :param offset: number of transactions to skip
    :param from_date: inclusive lower bound on transaction timestamp
    :param to_date: inclusive upper bound on transaction timestamp
    :return: paginated envelope of transactions with entries
    """
    result = await service.get_by_account_id(
        account_id,
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
    )
    return schemas.PaginatedTransactionResponse(
        items=[_txn_to_response(r) for r in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )
