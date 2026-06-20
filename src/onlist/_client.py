from __future__ import annotations

import os
from typing import Any, Mapping

import httpx
import openai

from onlist._constants import BASE_URL, ENV_API_KEY, MARKETPLACE_BASE_URL
from onlist._version import __version__
from onlist.resources.marketplace import AsyncMarketplace, Marketplace


class Onlist(openai.OpenAI):
    """Onlist API client. Drop-in replacement for ``openai.OpenAI``.

    All OpenAI-compatible methods (``chat.completions``, ``embeddings``,
    ``images``, ``audio``, ``models``) work identically. The ``marketplace``
    attribute provides access to Onlist-specific APIs.

    Example::

        from onlist import Onlist

        client = Onlist(api_key="sk-...")

        # OpenAI-compatible
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[{"role": "user", "content": "Hello!"}],
        )

        # Onlist marketplace
        models = client.marketplace.models.list()
    """

    marketplace: Marketplace

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        default_headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        resolved_key = api_key or os.environ.get(ENV_API_KEY)

        merged_headers = dict(default_headers or {})
        merged_headers.setdefault("User-Agent", f"onlist-python/{__version__}")
        merged_headers.setdefault("HTTP-Referer", "https://onlist.io")

        super().__init__(
            api_key=resolved_key,
            base_url=base_url or BASE_URL,
            default_headers=merged_headers,
            **kwargs,
        )

        marketplace_base = str(self.base_url).split("/v1")[0]

        effective_key = self.api_key if isinstance(self.api_key, str) else resolved_key
        self.marketplace = Marketplace(
            api_key=effective_key,
            base_url=marketplace_base or MARKETPLACE_BASE_URL,
        )

    def close(self) -> None:
        super().close()
        self.marketplace.close()


class AsyncOnlist(openai.AsyncOpenAI):
    """Async Onlist API client. Drop-in replacement for ``openai.AsyncOpenAI``.

    Example::

        import asyncio
        from onlist import AsyncOnlist

        async def main():
            client = AsyncOnlist(api_key="sk-...")
            response = await client.chat.completions.create(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "Hello!"}],
            )
            print(response.choices[0].message.content)

        asyncio.run(main())
    """

    marketplace: AsyncMarketplace

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        default_headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        resolved_key = api_key or os.environ.get(ENV_API_KEY)

        merged_headers = dict(default_headers or {})
        merged_headers.setdefault("User-Agent", f"onlist-python/{__version__}")
        merged_headers.setdefault("HTTP-Referer", "https://onlist.io")

        super().__init__(
            api_key=resolved_key,
            base_url=base_url or BASE_URL,
            default_headers=merged_headers,
            **kwargs,
        )

        marketplace_base = str(self.base_url).split("/v1")[0]

        effective_key = self.api_key if isinstance(self.api_key, str) else resolved_key
        self.marketplace = AsyncMarketplace(
            api_key=effective_key,
            base_url=marketplace_base or MARKETPLACE_BASE_URL,
        )

    async def close(self) -> None:
        await super().close()
        await self.marketplace.close()
