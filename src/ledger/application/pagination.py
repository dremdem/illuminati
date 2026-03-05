"""Generic paginated result container for application-layer use cases."""

import dataclasses
import typing

T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class PaginatedResult(typing.Generic[T]):
    """A page of items paired with the total count before pagination."""

    items: list[T]
    total: int
