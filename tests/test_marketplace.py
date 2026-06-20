from __future__ import annotations

import httpx
import pytest
import respx

from onlist import Onlist
from onlist._exceptions import APIError, AuthenticationError
from onlist.types.model import ModelListResponse
from onlist.types.provider import ProviderListResponse


MOCK_MODELS_RESPONSE = {
    "success": True,
    "data": {
        "data": [
            {
                "id": "anthropic/claude-sonnet-4",
                "author": "anthropic",
                "name": "claude-sonnet-4",
                "pricing": {"prompt": "0.0000030000", "completion": "0.0000150000"},
            },
            {
                "id": "openai/gpt-4o",
                "author": "openai",
                "name": "gpt-4o",
                "pricing": {"prompt": "0.0000025000", "completion": "0.0000100000"},
            },
        ],
        "total": 2,
        "offset": 0,
        "limit": 20,
    },
}

MOCK_MODEL_DETAIL = {
    "success": True,
    "data": {
        "id": "anthropic/claude-sonnet-4",
        "author": "anthropic",
        "name": "claude-sonnet-4",
        "context_length": 200000,
        "pricing": {"prompt": "0.0000030000", "completion": "0.0000150000"},
        "providers": [
            {"slug": "alice-shop", "score": 95.0, "price_input_usd": "0.0000030000"},
            {"slug": "bob-relay", "score": 88.0, "price_input_usd": "0.0000028000"},
        ],
    },
}

MOCK_PROVIDERS_RESPONSE = {
    "success": True,
    "data": {
        "items": [
            {
                "id": 1,
                "slug": "alice-shop",
                "name": "Alice's Shop",
                "weighted_score": 95.0,
                "listing_count": 12,
            },
            {
                "id": 2,
                "slug": "bob-relay",
                "name": "Bob's Relay",
                "weighted_score": 88.0,
                "listing_count": 8,
            },
        ],
        "sort": "score",
    },
}

MOCK_PROVIDER_DETAIL = {
    "success": True,
    "data": {
        "id": 1,
        "slug": "alice-shop",
        "name": "Alice's Shop",
        "weighted_score": 95.0,
        "listing_count": 12,
        "listings": [],
    },
}


class TestMarketplaceModels:
    @respx.mock
    def test_list_models(self, client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/mkt/models").mock(
            return_value=httpx.Response(200, json=MOCK_MODELS_RESPONSE)
        )
        result = client.marketplace.models.list()
        assert isinstance(result, ModelListResponse)
        assert len(result.data) == 2
        assert result.data[0]["id"] == "anthropic/claude-sonnet-4"
        assert "limit=20" in str(route.calls[0].request.url)
        assert "offset=0" in str(route.calls[0].request.url)

    @respx.mock
    def test_list_models_with_query(self, client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/mkt/models").mock(
            return_value=httpx.Response(200, json=MOCK_MODELS_RESPONSE)
        )
        result = client.marketplace.models.list(q="claude", limit=5)
        assert isinstance(result, ModelListResponse)
        assert "q=claude" in str(route.calls[0].request.url)
        assert "limit=5" in str(route.calls[0].request.url)

    @respx.mock
    def test_get_model(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/models/anthropic/claude-sonnet-4").mock(
            return_value=httpx.Response(200, json=MOCK_MODEL_DETAIL)
        )
        detail = client.marketplace.models.get("anthropic/claude-sonnet-4")
        assert detail.id == "anthropic/claude-sonnet-4"
        assert len(detail.providers) == 2
        assert detail.providers[0].slug == "alice-shop"


class TestMarketplaceProviders:
    @respx.mock
    def test_list_providers(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/providers").mock(
            return_value=httpx.Response(200, json=MOCK_PROVIDERS_RESPONSE)
        )
        result = client.marketplace.providers.list()
        assert isinstance(result, ProviderListResponse)
        assert len(result.data) == 2
        assert result.data[0].slug == "alice-shop"
        assert result.data[0].score == 95.0
        assert result.data[0].model_count == 12

    @respx.mock
    def test_get_provider(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/provider/alice-shop").mock(
            return_value=httpx.Response(200, json=MOCK_PROVIDER_DETAIL)
        )
        provider = client.marketplace.providers.get("alice-shop")
        assert provider.slug == "alice-shop"
        assert provider.name == "Alice's Shop"


class TestMarketplaceErrors:
    @respx.mock
    def test_auth_error(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/providers").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"message": "invalid token", "type": "onlist_error", "code": "invalid_token"}},
            )
        )
        with pytest.raises(AuthenticationError):
            client.marketplace.providers.list()

    @respx.mock
    def test_generic_api_error(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/models").mock(
            return_value=httpx.Response(500, json={"error": {"message": "internal error"}})
        )
        with pytest.raises(APIError) as exc_info:
            client.marketplace.models.list()
        assert exc_info.value.status_code == 500
