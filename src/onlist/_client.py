from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import httpx
import openai

from onlist._constants import (
    BASE_URL,
    ENV_API_KEY,
    ENV_MANAGEMENT_KEY,
    MARKETPLACE_BASE_URL,
)
from onlist._transport import _DEFAULT_TIMEOUT, _default_headers
from onlist._version import __version__
from onlist.resources.account import (
    AccountActivity,
    AccountAPIKeys,
    AccountCredits,
    AccountGenerations,
    AccountOAuth,
    AsyncAccountActivity,
    AsyncAccountAPIKeys,
    AsyncAccountCredits,
    AsyncAccountGenerations,
    AsyncAccountOAuth,
)
from onlist.resources.marketplace import AsyncMarketplace, Marketplace


def _resolve_api_key(api_key: str | None) -> str | None:
    return api_key or os.environ.get(ENV_API_KEY) or os.environ.get("OPENAI_API_KEY")


def _resolve_management_key(management_key: str | None, api_key: str | None) -> str | None:
    """Pick the credential for the account API.

    Falls back to the inference key so that a client built the OpenRouter way
    — one key, one keyhole — still reaches the account endpoints. Whether
    that key is allowed there is the server's call: the SDK never inspects
    key prefixes locally, it just surfaces the 403.
    """
    return management_key or os.environ.get(ENV_MANAGEMENT_KEY) or api_key


class Onlist(openai.OpenAI):
    """Onlist API client. Drop-in replacement for ``openai.OpenAI``.

    All OpenAI-compatible methods (``chat.completions``, ``embeddings``,
    ``images``, ``audio``, ``models``) work identically. The ``marketplace``
    attribute provides access to Onlist-specific APIs, and the ``credits`` /
    ``generations`` / ``api_keys`` / ``activity`` / ``oauth`` attributes to
    the account API.

    Supports use as a context manager::

        with Onlist(api_key="sk-...") as client:
            response = client.chat.completions.create(...)

    Example::

        from onlist import Onlist

        client = Onlist(api_key="sk-...", management_key="mgmt_...")

        # OpenAI-compatible
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[{"role": "user", "content": "Hello!"}],
        )

        # Onlist marketplace
        models = client.marketplace.models.list()

        # Onlist account
        print(client.credits.get().total_credits)
    """

    marketplace: Marketplace
    credits: AccountCredits
    generations: AccountGenerations
    api_keys: AccountAPIKeys
    activity: AccountActivity
    oauth: AccountOAuth

    def __init__(
        self,
        *,
        api_key: str | None = None,
        management_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        default_headers: Mapping[str, str] | None = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        resolved_key = _resolve_api_key(api_key)

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
            max_retries=max_retries,
        )

        # The account face gets its own httpx client: it authenticates with a
        # different credential than inference and marketplace do, and the
        # Authorization header is set per-client.
        self.management_key = _resolve_management_key(management_key, effective_key)
        self._account_client = httpx.Client(
            base_url=marketplace_base or MARKETPLACE_BASE_URL,
            headers=_default_headers(self.management_key),
            timeout=_DEFAULT_TIMEOUT,
        )
        self.credits = AccountCredits(self._account_client, max_retries)
        self.generations = AccountGenerations(self._account_client, max_retries)
        self.api_keys = AccountAPIKeys(self._account_client, max_retries)
        self.activity = AccountActivity(self._account_client, max_retries)
        self.oauth = AccountOAuth(self._account_client, max_retries)

    def close(self) -> None:
        super().close()
        self.marketplace.close()
        self._account_client.close()

    def __enter__(self) -> Onlist:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncOnlist(openai.AsyncOpenAI):
    """Async Onlist API client. Drop-in replacement for ``openai.AsyncOpenAI``.

    Supports use as an async context manager::

        async with AsyncOnlist(api_key="sk-...") as client:
            response = await client.chat.completions.create(...)

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
    credits: AsyncAccountCredits
    generations: AsyncAccountGenerations
    api_keys: AsyncAccountAPIKeys
    activity: AsyncAccountActivity
    oauth: AsyncAccountOAuth

    def __init__(
        self,
        *,
        api_key: str | None = None,
        management_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        default_headers: Mapping[str, str] | None = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        resolved_key = _resolve_api_key(api_key)

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
            max_retries=max_retries,
        )

        self.management_key = _resolve_management_key(management_key, effective_key)
        self._account_client = httpx.AsyncClient(
            base_url=marketplace_base or MARKETPLACE_BASE_URL,
            headers=_default_headers(self.management_key),
            timeout=_DEFAULT_TIMEOUT,
        )
        self.credits = AsyncAccountCredits(self._account_client, max_retries)
        self.generations = AsyncAccountGenerations(self._account_client, max_retries)
        self.api_keys = AsyncAccountAPIKeys(self._account_client, max_retries)
        self.activity = AsyncAccountActivity(self._account_client, max_retries)
        self.oauth = AsyncAccountOAuth(self._account_client, max_retries)

    async def close(self) -> None:
        await super().close()
        await self.marketplace.close()
        await self._account_client.aclose()

    async def __aenter__(self) -> AsyncOnlist:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
