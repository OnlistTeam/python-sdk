from __future__ import annotations

import httpx
import pytest
import respx

from onlist import Onlist
from onlist._exceptions import APIError, AuthenticationError, NotFoundError
from onlist.types.model import Model, ModelListResponse, UserModelListResponse
from onlist.types.provider import ProviderListResponse
from onlist.types.rankings import AppListResponse, ModelRankingsResponse

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

MOCK_MODEL_RANKINGS = {
    "success": True,
    "data": {
        "leaderboard": [
            {
                "rank": 1,
                "model_name": "claude-sonnet-4",
                "author": "anthropic",
                "author_icon": "/icons/anthropic.svg",
                "total_tokens": "123456789",
                "total_requests": 5000,
                "growth_pct": None,
            },
            {
                "rank": 2,
                "model_name": "gpt-4o",
                "author": "openai",
                "author_icon": "/icons/openai.svg",
                "total_tokens": "98765432",
                "total_requests": 3200,
                "growth_pct": 15.3,
            },
        ],
        "series": [
            {"bucket": "2026-06-25", "value": 100000, "type": "claude-sonnet-4"},
            {"bucket": "2026-06-25", "value": 80000, "type": "gpt-4o"},
        ],
        "top_models": ["claude-sonnet-4", "gpt-4o"],
        "sort": "popular",
        "window": "week",
        "start_date": "2026-06-25",
        "end_date": "2026-06-30",
    },
}

MOCK_APPS_RESPONSE = {
    "success": True,
    "data": {
        "apps": [
            {
                "app_id": 1,
                "url_key": "cursor.com",
                "slug": "cursor",
                "title": "Cursor",
                "description": "AI code editor",
                "domain": "cursor.com",
                "icon_url": "https://example.com/cursor.png",
                "categories": ["coding"],
                "rank": 1,
                "total_requests": 10000,
                "total_tokens": "500000000",
                "growth_pct": None,
            },
        ],
        "page": 1,
        "limit": 20,
        "has_more": False,
        "sort": "popular",
        "window": "month",
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
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
        assert isinstance(result.data[0], Model)
        assert result.data[0].id == "anthropic/claude-sonnet-4"
        assert result.data[0].author == "anthropic"
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


class TestMarketplaceUserModels:
    @respx.mock
    def test_list_for_user(self, client: Onlist, api_key: str) -> None:
        route = respx.get("https://onlist.io/api/v1/models/user").mock(
            return_value=httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [
                        {
                            "id": "openai/gpt-4o",
                            "name": "OpenAI: GPT-4o",
                            "context_length": 128000,
                        }
                    ],
                },
            )
        )
        result = client.marketplace.models.list_for_user()
        assert isinstance(result, UserModelListResponse)
        assert result.object == "list"
        assert len(result.data) == 1
        assert isinstance(result.data[0], Model)
        assert result.data[0].id == "openai/gpt-4o"
        assert route.calls[0].request.headers["Authorization"] == f"Bearer {api_key}"

    @respx.mock
    def test_list_for_user_empty(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/v1/models/user").mock(
            return_value=httpx.Response(200, json={"object": "list", "data": []})
        )
        assert client.marketplace.models.list_for_user().data == []

    @respx.mock
    def test_list_for_user_auth_error(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/v1/models/user").mock(
            return_value=httpx.Response(
                401, json={"error": {"code": 401, "message": "Invalid credentials"}}
            )
        )
        with pytest.raises(AuthenticationError):
            client.marketplace.models.list_for_user()


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


class TestMarketplaceRankings:
    @respx.mock
    def test_model_rankings(self, client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/mkt/rankings/models").mock(
            return_value=httpx.Response(200, json=MOCK_MODEL_RANKINGS)
        )
        result = client.marketplace.rankings.models()
        assert isinstance(result, ModelRankingsResponse)
        assert len(result.leaderboard) == 2
        assert result.leaderboard[0].model_name == "claude-sonnet-4"
        assert result.leaderboard[0].total_tokens == "123456789"
        assert result.leaderboard[1].growth_pct == 15.3
        assert len(result.series) == 2
        assert result.top_models == ["claude-sonnet-4", "gpt-4o"]
        assert result.sort == "popular"
        assert result.window == "week"
        assert "sort=popular" in str(route.calls[0].request.url)

    @respx.mock
    def test_model_rankings_params(self, client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/mkt/rankings/models").mock(
            return_value=httpx.Response(200, json=MOCK_MODEL_RANKINGS)
        )
        client.marketplace.rankings.models(sort="trending", window="month", limit=10)
        url = str(route.calls[0].request.url)
        assert "sort=trending" in url
        assert "window=month" in url
        assert "limit=10" in url

    @respx.mock
    def test_apps_rankings(self, client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/mkt/apps").mock(
            return_value=httpx.Response(200, json=MOCK_APPS_RESPONSE)
        )
        result = client.marketplace.rankings.apps()
        assert isinstance(result, AppListResponse)
        assert len(result.apps) == 1
        assert result.apps[0].title == "Cursor"
        assert result.apps[0].total_tokens == "500000000"
        assert result.apps[0].categories == ["coding"]
        assert result.has_more is False
        assert "sort=popular" in str(route.calls[0].request.url)

    @respx.mock
    def test_apps_rankings_with_category(self, client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/mkt/apps").mock(
            return_value=httpx.Response(200, json=MOCK_APPS_RESPONSE)
        )
        client.marketplace.rankings.apps(category="coding", page=2)
        url = str(route.calls[0].request.url)
        assert "category=coding" in url
        assert "page=2" in url


class TestMarketplaceErrors:
    @respx.mock
    def test_auth_error(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/providers").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": {
                        "message": "invalid token",
                        "type": "onlist_error",
                        "code": "invalid_token",
                    }
                },
            )
        )
        with pytest.raises(AuthenticationError):
            client.marketplace.providers.list()

    @respx.mock
    def test_not_found_error(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/models/nonexistent/model").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"message": "model not found"}},
            )
        )
        with pytest.raises(NotFoundError) as exc_info:
            client.marketplace.models.get("nonexistent/model")
        assert exc_info.value.status_code == 404

    @respx.mock
    def test_generic_api_error(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/models").mock(
            return_value=httpx.Response(500, json={"error": {"message": "internal error"}})
        )
        with pytest.raises(APIError) as exc_info:
            client.marketplace.models.list()
        assert exc_info.value.status_code == 500


class TestContextManager:
    def test_sync_context_manager(self, api_key: str) -> None:
        with Onlist(api_key=api_key) as client:
            assert hasattr(client, "marketplace")
            assert hasattr(client.marketplace, "rankings")
        # After exiting, the marketplace httpx client should be closed
        assert client.marketplace._client.is_closed


class TestRetry:
    @respx.mock
    def test_retry_on_503(self, client: Onlist) -> None:
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return httpx.Response(503, json={"error": {"message": "unavailable"}})
            return httpx.Response(200, json=MOCK_PROVIDERS_RESPONSE)

        respx.get("https://onlist.io/api/mkt/providers").mock(side_effect=side_effect)
        result = client.marketplace.providers.list()
        assert isinstance(result, ProviderListResponse)
        assert call_count == 3  # 1 initial + 2 retries

    @respx.mock
    def test_no_retry_on_400(self, client: Onlist) -> None:
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(400, json={"error": {"message": "bad request"}})

        respx.get("https://onlist.io/api/mkt/providers").mock(side_effect=side_effect)
        with pytest.raises(APIError) as exc_info:
            client.marketplace.providers.list()
        assert exc_info.value.status_code == 400
        assert call_count == 1  # No retries for 400

    @respx.mock
    def test_retry_exhausted_raises(self, client: Onlist) -> None:
        respx.get("https://onlist.io/api/mkt/providers").mock(
            return_value=httpx.Response(429, json={"error": {"message": "rate limited"}})
        )
        from onlist._exceptions import RateLimitError

        with pytest.raises(RateLimitError):
            client.marketplace.providers.list()
