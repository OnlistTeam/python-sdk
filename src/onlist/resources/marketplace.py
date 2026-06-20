from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from onlist._exceptions import _raise_for_status
from onlist._version import __version__
from onlist.types.model import ModelDetail, ModelListResponse
from onlist.types.provider import Provider, ProviderDetail, ProviderListResponse


_DEFAULT_TIMEOUT = 30.0


def _default_headers(api_key: str | None) -> dict[str, str]:
    headers: dict[str, str] = {
        "User-Agent": f"onlist-python/{__version__}",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _encode_path(segment: str) -> str:
    """URL-encode a path segment, preserving ``/`` for model IDs like ``author/model``."""
    return quote(segment, safe="/")


def _parse_response(response: httpx.Response) -> Any:
    if response.status_code >= 400:
        try:
            body = response.json()
        except Exception:
            body = response.text
        _raise_for_status(response.status_code, body)
    body = response.json()
    if isinstance(body, dict) and "data" in body and "success" in body:
        body = body["data"]
    return body


class MarketplaceModels:
    """Query the Onlist model catalog."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

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
        resp = self._client.get("/api/mkt/models", params=params)
        return ModelListResponse.model_validate(_parse_response(resp))

    def get(self, model_id: str) -> ModelDetail:
        """Get detailed info for a model, including all provider offers.

        Args:
            model_id: Model identifier, e.g. ``"anthropic/claude-sonnet-4-6"``.
        """
        resp = self._client.get(f"/api/mkt/models/{_encode_path(model_id)}")
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ModelDetail.model_validate(data)


class MarketplaceProviders:
    """Query provider (seller) profiles."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

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
        resp = self._client.get("/api/mkt/providers", params=params)
        return ProviderListResponse.model_validate(_parse_response(resp))

    def get(self, slug: str) -> ProviderDetail:
        """Get a provider's public profile by slug.

        Args:
            slug: Provider slug, e.g. ``"alice-shop"``.
        """
        resp = self._client.get(f"/api/mkt/provider/{_encode_path(slug)}")
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ProviderDetail.model_validate(data)


class Marketplace:
    """Access Onlist marketplace data.

    Provides read-only access to the public marketplace APIs:
    model catalog, provider directory, and more.
    """

    models: MarketplaceModels
    providers: MarketplaceProviders

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers=_default_headers(api_key),
            timeout=timeout,
        )
        self.models = MarketplaceModels(self._client)
        self.providers = MarketplaceProviders(self._client)

    def close(self) -> None:
        self._client.close()


# ---------------------------------------------------------------------------
# Async mirror
# ---------------------------------------------------------------------------


class AsyncMarketplaceModels:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

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
        resp = await self._client.get("/api/mkt/models", params=params)
        return ModelListResponse.model_validate(_parse_response(resp))

    async def get(self, model_id: str) -> ModelDetail:
        resp = await self._client.get(f"/api/mkt/models/{_encode_path(model_id)}")
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ModelDetail.model_validate(data)


class AsyncMarketplaceProviders:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

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
        resp = await self._client.get("/api/mkt/providers", params=params)
        return ProviderListResponse.model_validate(_parse_response(resp))

    async def get(self, slug: str) -> ProviderDetail:
        resp = await self._client.get(f"/api/mkt/provider/{_encode_path(slug)}")
        data = _parse_response(resp)
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        return ProviderDetail.model_validate(data)


class AsyncMarketplace:
    """Async version of :class:`Marketplace`."""

    models: AsyncMarketplaceModels
    providers: AsyncMarketplaceProviders

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=_default_headers(api_key),
            timeout=timeout,
        )
        self.models = AsyncMarketplaceModels(self._client)
        self.providers = AsyncMarketplaceProviders(self._client)

    async def close(self) -> None:
        await self._client.aclose()
