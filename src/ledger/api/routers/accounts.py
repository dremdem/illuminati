"""Account API route handlers: create, list, and get by ID."""

import typing
import uuid

import fastapi

import ledger.api.dependencies as dependencies
import ledger.api.schemas as schemas
import ledger.application.account_service as account_service

router = fastapi.APIRouter(prefix="/api/accounts", tags=["accounts"])


def _to_response(
    awb: account_service.AccountWithBalance,
) -> schemas.AccountResponse:
    """
    Map an AccountWithBalance DTO to an API response schema.

    :param awb: account with balance from the service layer
    :return: Pydantic response model
    """
    return schemas.AccountResponse(
        id=str(awb.account.id),
        name=awb.account.name,
        type=awb.account.type,
        balance=f"{awb.balance:.2f}",
    )


@router.post(
    "",
    response_model=schemas.AccountResponse,
    status_code=201,
)
async def create_account(
    body: schemas.CreateAccountRequest,
    service: typing.Annotated[
        account_service.AccountService,
        fastapi.Depends(dependencies.get_account_service),
    ],
) -> schemas.AccountResponse:
    """
    Create a new financial account.

    :param body: request body with name and type
    :param service: injected account service
    :return: the created account with zero balance
    """
    result = await service.create_account(name=body.name, account_type=body.type)
    return _to_response(result)


@router.get(
    "",
    response_model=list[schemas.AccountResponse],
)
async def list_accounts(
    service: typing.Annotated[
        account_service.AccountService,
        fastapi.Depends(dependencies.get_account_service),
    ],
) -> list[schemas.AccountResponse]:
    """
    List all accounts with computed balances.

    :param service: injected account service
    :return: list of accounts with balances
    """
    results = await service.get_all()
    return [_to_response(r) for r in results]


@router.get(
    "/{account_id}",
    response_model=schemas.AccountResponse,
)
async def get_account(
    account_id: uuid.UUID,
    service: typing.Annotated[
        account_service.AccountService,
        fastapi.Depends(dependencies.get_account_service),
    ],
) -> schemas.AccountResponse:
    """
    Retrieve a single account by ID with its computed balance.

    :param account_id: UUID path parameter
    :param service: injected account service
    :return: account with balance
    """
    result = await service.get_by_id(account_id)
    return _to_response(result)
