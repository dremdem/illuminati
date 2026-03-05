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
    summary="Create account",
    description="Create a new financial account with the given name and type. "
    "The name must be unique and non-empty. Balance starts at 0.00.",
    response_description="The created account with a zero balance.",
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
    response_model=schemas.PaginatedAccountResponse,
    summary="List accounts",
    description="Retrieve all accounts with their balances computed via "
    "SQL aggregation. Supports optional pagination via limit and offset.",
    response_description="Paginated envelope of accounts with computed balances.",
)
async def list_accounts(
    service: typing.Annotated[
        account_service.AccountService,
        fastapi.Depends(dependencies.get_account_service),
    ],
    limit: typing.Annotated[
        int | None,
        fastapi.Query(
            ge=1, le=100, description="Maximum number of accounts to return."
        ),
    ] = None,
    offset: typing.Annotated[
        int,
        fastapi.Query(ge=0, description="Number of accounts to skip."),
    ] = 0,
) -> schemas.PaginatedAccountResponse:
    """
    List all accounts with computed balances.

    :param service: injected account service
    :param limit: maximum number of accounts to return (None = all)
    :param offset: number of accounts to skip
    :return: paginated envelope of accounts with balances
    """
    result = await service.get_all(limit=limit, offset=offset)
    return schemas.PaginatedAccountResponse(
        items=[_to_response(r) for r in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{account_id}",
    response_model=schemas.AccountResponse,
    summary="Get account",
    description="Retrieve a single account by its UUID, including the balance "
    "computed via SQL aggregation across all transaction entries.",
    response_description="The account with its computed balance.",
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
