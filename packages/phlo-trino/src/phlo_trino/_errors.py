"""Shared exception-chain utilities."""

from __future__ import annotations

from collections.abc import Iterable


def iter_exception_chain(exc: BaseException) -> Iterable[BaseException]:
    """Yield an exception and its chained causes/contexts.

    Args:
        exc: Starting exception.

    Yields:
        Exception objects from the chain, root first.

    """
    current: BaseException | None = exc
    while current is not None:
        yield current
        current = current.__cause__ or current.__context__
