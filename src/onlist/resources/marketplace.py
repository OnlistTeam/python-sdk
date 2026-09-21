from __future__ import annotations

from typing import Any

import httpx

from onlist._transport import (
    _DEFAULT_MAX_RETRIES,
    _DEFAULT_TIMEOUT,
    _async_request,
    _default_headers,
    _encode_path,
    _parse_response,
    _sync_request,
)
from onlist.types.model import ModelDetail, ModelListResponse, UserModelListResponse
from onlist.types.provider import ProviderDetail, ProviderListResponse
from onlist.types.rankings import (
    AppListResponse,
    ModelRankingsResponse,
)

# ---------------------------------------------------------------------------
# Sync resource classes
# ---------------------------------------------------------------------------


class MarketplaceModels:
    """Query the Onlist model catalog."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        q: str | None = None,
    ) -> ModelListResponse:
        """List models with pricing and provider counts.

        Args:
            limit: Maximum results to return.
            offset: Number of results to skip.
            q: Optional search query.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if q:
            params["q"] = q
        resp = _sync_request(
            self._client, "GET", "/api/mkt/models", params=params, max_retries=self._max_retries
        )
        return ModelListResponse.model_validate(_parse_response(resp))

    def list_for_user(self) -> UserModelListResponse:
        """List only the models this client's API key can actually call.

        Wraps ``GET /v1/models/user`` (served at ``/api/v1/models/user``). The
        response has the same shape as ``client.models.list()`` — the public
        catalog — filtered by the key's model access list, then by the denied
        providers of its routing policy, then by its allowed providers. The
        allowed-provider filter applies even when the key falls back to every
        provider once its allowlist is exhausted: the list states intent, the
        fallback is a runtime safety net. ``zdr`` / ``data_collection`` are
        per-request parameters and never narrow it.

        Intended for a program holding one specific key, e.g. the model picker of
        an IDE agent. An unknown or revoked key raises ``AuthenticationError``.
        """
        resp = _sync_request(
            self._client, "GET", "/api/v1/models/user", max_retries=self._max_retries
        )
        return UserModelListResponse.model_validate(_parse_response(resp))

    def get(self, model_id: str) -> ModelDetail:
        """Get detailed info for a model, including all provider offers.

        Args:
            model_id: Model identifier, e.g. ``"anthropic/claude-sonnet-4-6"``.
        """
        resp = _sync_request(
            self._client,
            "GET",
            f"/api/mkt/models/{_encode_path(model_id)}",
            max_retries=self._max_retries,
        )
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ModelDetail.model_validate(data)


class MarketplaceProviders:
    """Query provider (seller) profiles."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def list(
        self,
        *,
        sort: str | None = None,
        q: str | None = None,
    ) -> ProviderListResponse:
        """List all providers on the marketplace.

        Args:
            sort: Sort order (e.g. ``"score"``).
            q: Optional search query.
        """
        params: dict[str, Any] = {}
        if sort:
            params["sort"] = sort
        if q:
            params["q"] = q
        resp = _sync_request(
            self._client, "GET", "/api/mkt/providers", params=params, max_retries=self._max_retries
        )
        return ProviderListResponse.model_validate(_parse_response(resp))

    def get(self, slug: str) -> ProviderDetail:
        """Get a provider's public profile by slug.

        Args:
            slug: Provider slug, e.g. ``"alice-shop"``.
        """
        resp = _sync_request(
            self._client,
            "GET",
            f"/api/mkt/provider/{_encode_path(slug)}",
            max_retries=self._max_retries,
        )
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ProviderDetail.model_validate(data)


class MarketplaceRankings:
    """Query model usage rankings and app rankings."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def models(
        self,
        *,
        sort: str = "popular",
        window: str = "week",
        limit: int = 20,
        offset: int = 0,
    ) -> ModelRankingsResponse:
        """Get the model usage leaderboard with chart data.

        Args:
            sort: ``"popular"`` (absolute usage) or ``"trending"`` (growth rate).
            window: Time window: ``"day"``, ``"week"``, or ``"month"``.
            limit: Maximum leaderboard entries.
            offset: Number of entries to skip.
        """
        params: dict[str, Any] = {
            "sort": sort,
            "window": window,
            "limit": limit,
            "offset": offset,
        }
        resp = _sync_request(
            self._client,
            "GET",
            "/api/mkt/rankings/models",
            params=params,
            max_retries=self._max_retries,
        )
        return ModelRankingsResponse.model_validate(_parse_response(resp))

    def apps(
        self,
        *,
        sort: str = "popular",
        window: str = "month",
        category: str | None = None,
        subcategory: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> AppListResponse:
        """Get the app usage rankings.

        Args:
            sort: ``"popular"`` or ``"trending"``.
            window: ``"day"``, ``"week"``, or ``"month"``.
            category: Filter by category group.
            subcategory: Filter by subcategory (takes priority over ``category``).
            page: Page number (1-based).
            limit: Results per page (max 100).
        """
        params: dict[str, Any] = {
            "sort": sort,
            "window": window,
            "page": page,
            "limit": limit,
        }
        if subcategory:
            params["subcategory"] = subcategory
        elif category:
            params["category"] = category
        resp = _sync_request(
            self._client, "GET", "/api/mkt/apps", params=params, max_retries=self._max_retries
        )
        return AppListResponse.model_validate(_parse_response(resp))


class Marketplace:
    """Access Onlist marketplace data.

    Provides read-only access to the public marketplace APIs:
    model catalog, provider directory, rankings, and more.

    Supports use as a context manager::

        with Marketplace(api_key="sk-...", base_url="https://onlist.io") as mkt:
            models = mkt.models.list()
    """

    models: MarketplaceModels
    providers: MarketplaceProviders
    rankings: MarketplaceRankings

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers=_default_headers(api_key),
            timeout=timeout,
        )
        self.models = MarketplaceModels(self._client, max_retries)
        self.providers = MarketplaceProviders(self._client, max_retries)
        self.rankings = MarketplaceRankings(self._client, max_retries)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Marketplace:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Async mirror
# ---------------------------------------------------------------------------


class AsyncMarketplaceModels:
    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        q: str | None = None,
    ) -> ModelListResponse:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if q:
            params["q"] = q
        resp = await _async_request(
            self._client, "GET", "/api/mkt/models", params=params, max_retries=self._max_retries
        )
        return ModelListResponse.model_validate(_parse_response(resp))

    async def list_for_user(self) -> UserModelListResponse:
        """List only the models this client's API key can actually call.

        Wraps ``GET /v1/models/user`` (served at ``/api/v1/models/user``). The
        response has the same shape as ``client.models.list()`` — the public
        catalog — filtered by the key's model access list, then by the denied
        providers of its routing policy, then by its allowed providers. The
        allowed-provider filter applies even when the key falls back to every
        provider once its allowlist is exhausted: the list states intent, the
        fallback is a runtime safety net. ``zdr`` / ``data_collection`` are
        per-request parameters and never narrow it.

        Intended for a program holding one specific key, e.g. the model picker of
        an IDE agent. An unknown or revoked key raises ``AuthenticationError``.
        """
        resp = await _async_request(
            self._client, "GET", "/api/v1/models/user", max_retries=self._max_retries
        )
        return UserModelListResponse.model_validate(_parse_response(resp))

    async def get(self, model_id: str) -> ModelDetail:
        resp = await _async_request(
            self._client,
            "GET",
            f"/api/mkt/models/{_encode_path(model_id)}",
            max_retries=self._max_retries,
        )
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ModelDetail.model_validate(data)


class AsyncMarketplaceProviders:
    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def list(
        self,
        *,
        sort: str | None = None,
        q: str | None = None,
    ) -> ProviderListResponse:
        params: dict[str, Any] = {}
        if sort:
            params["sort"] = sort
        if q:
            params["q"] = q
        resp = await _async_request(
            self._client, "GET", "/api/mkt/providers", params=params, max_retries=self._max_retries
        )
        return ProviderListResponse.model_validate(_parse_response(resp))

    async def get(self, slug: str) -> ProviderDetail:
        resp = await _async_request(
            self._client,
            "GET",
            f"/api/mkt/provider/{_encode_path(slug)}",
            max_retries=self._max_retries,
        )
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ProviderDetail.model_validate(data)


class AsyncMarketplaceRankings:
    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def models(
        self,
        *,
        sort: str = "popular",
        window: str = "week",
        limit: int = 20,
        offset: int = 0,
    ) -> ModelRankingsResponse:
        params: dict[str, Any] = {
            "sort": sort,
            "window": window,
            "limit": limit,
            "offset": offset,
        }
        resp = await _async_request(
            self._client,
            "GET",
            "/api/mkt/rankings/models",
            params=params,
            max_retries=self._max_retries,
        )
        return ModelRankingsResponse.model_validate(_parse_response(resp))

    async def apps(
        self,
        *,
        sort: str = "popular",
        window: str = "month",
        category: str | None = None,
        subcategory: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> AppListResponse:
        params: dict[str, Any] = {
            "sort": sort,
            "window": window,
            "page": page,
            "limit": limit,
        }
        if subcategory:
            params["subcategory"] = subcategory
        elif category:
            params["category"] = category
        resp = await _async_request(
            self._client, "GET", "/api/mkt/apps", params=params, max_retries=self._max_retries
        )
        return AppListResponse.model_validate(_parse_response(resp))


class AsyncMarketplace:
    """Async version of :class:`Marketplace`.

    Supports use as an async context manager::

        async with AsyncMarketplace(api_key="sk-...", base_url="https://onlist.io") as mkt:
            models = await mkt.models.list()
    """

    models: AsyncMarketplaceModels
    providers: AsyncMarketplaceProviders
    rankings: AsyncMarketplaceRankings

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=_default_headers(api_key),
            timeout=timeout,
        )
        self.models = AsyncMarketplaceModels(self._client, max_retries)
        self.providers = AsyncMarketplaceProviders(self._client, max_retries)
        self.rankings = AsyncMarketplaceRankings(self._client, max_retries)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncMarketplace:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
