"""Transaction API route handlers: create, get by ID, and get by account."""

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
    "/{transaction_id}",
    response_model=schemas.TransactionResponse,
    response_model_by_alias=True,
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
    response_model=list[schemas.TransactionResponse],
    response_model_by_alias=True,
)
async def get_account_transactions(
    account_id: uuid.UUID,
    service: typing.Annotated[
        transaction_service.TransactionService,
        fastapi.Depends(dependencies.get_transaction_service),
    ],
) -> list[schemas.TransactionResponse]:
    """
    Retrieve all transactions affecting a given account.

    :param account_id: UUID path parameter for the account
    :param service: injected transaction service
    :return: list of transactions with entries
    """
    results = await service.get_by_account_id(account_id)
    return [_txn_to_response(r) for r in results]
