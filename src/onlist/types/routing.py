from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class MaxPrice(BaseModel):
    """USD-per-token price caps for provider routing."""

    prompt: float | None = None
    completion: float | None = None


class ProviderRouting(BaseModel):
    """OpenRouter-compatible provider routing controls.

    Pass as ``extra_body={"provider": routing.model_dump(exclude_none=True)}``
    or simply as a dict.

    Example::

        from onlist.types import ProviderRouting

        routing = ProviderRouting(only=["alice-shop"], sort="price")
        client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[...],
            extra_body={"provider": routing.model_dump(exclude_none=True)},
        )
    """

    only: list[str] | None = None
    sort: Literal["price", "throughput"] | None = None
    order: list[str] | None = None
    allow: list[str] | None = None
    ignore: list[str] | None = None
    allow_fallbacks: bool | None = None
    max_price: MaxPrice | None = None
