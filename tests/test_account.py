from __future__ import annotations

import typing

import httpx
import pytest
import respx

from onlist import (
    APIError,
    APIKey,
    AsyncOnlist,
    BadRequestError,
    CreatedKey,
    Credits,
    CurrentKey,
    ExchangedKey,
    Generation,
    Onlist,
    PermissionDeniedError,
    async_exchange_auth_code,
    exchange_auth_code,
    generate_pkce,
)
from onlist._constants import ENV_MANAGEMENT_KEY
from onlist.resources.account import AccountAPIKeys, AsyncAccountAPIKeys


def _union_args(annotation: object) -> tuple[object, ...]:
    """Members of a union annotation, or a 1-tuple for a plain type."""
    return typing.get_args(annotation) or (annotation,)


MOCK_KEY = {
    "hash": "42",
    "name": "prod",
    "label": "sk-...cdef",
    "disabled": False,
    "limit": 25.0,
    "limit_remaining": 12.5,
    "limit_reset": "daily",
    "include_byok_in_limit": False,
    "usage": 12.5,
    "usage_daily": 1.25,
    "usage_weekly": 6.0,
    "usage_monthly": 12.5,
    "byok_usage": 0,
    "byok_usage_daily": 0,
    "byok_usage_weekly": 0,
    "byok_usage_monthly": 0,
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": None,
    "expires_at": None,
    "external_user": None,
    "creator_user_id": None,
    "workspace_id": "default",
}

MOCK_GENERATION = {
    "id": "req-abc",
    "model": "deepseek/deepseek-chat",
    "provider_name": "alice-shop",
    "streamed": True,
    "latency": 812.0,
    "generation_time": 4200,
    "created_at": "2026-09-06T10:00:00Z",
    "tokens_prompt": 120,
    "tokens_completion": 340,
    "native_tokens_prompt": 120,
    "native_tokens_completion": 340,
    "native_tokens_cached": 64,
    "native_tokens_reasoning": None,
    "total_cost": 0.000412,
    "usage": 0.000412,
    "cache_discount": None,
    "finish_reason": "stop",
    "native_finish_reason": "stop",
    "is_byok": False,
    "upstream_id": None,
    "http_referer": None,
    "user_agent": None,
    "origin": None,
    "api_type": None,
}

MOCK_ACTIVITY_ROW = {
    "date": "2026-09-05",
    "model": "deepseek/deepseek-chat",
    "model_permaslug": "deepseek/deepseek-chat",
    "endpoint_id": "alice-shop/deepseek/deepseek-chat",
    "provider_name": "alice-shop",
    "usage": 1.25,
    "byok_usage_inference": 0,
    "requests": 40,
    "prompt_tokens": 4800,
    "completion_tokens": 13600,
    "reasoning_tokens": 0,
}

# The account face uses OpenRouter's envelope, where ``code`` is the HTTP
# status as an *integer* rather than a string.
FORBIDDEN_BODY = {
    "error": {"code": 403, "message": "Only management keys can perform this operation"}
}


@pytest.fixture
def account_client(monkeypatch: pytest.MonkeyPatch) -> Onlist:
    monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
    return Onlist(api_key="sk-test", management_key="mgmt_test")


class TestCredits:
    @respx.mock
    def test_get(self, account_client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/v1/credits").mock(
            return_value=httpx.Response(
                200, json={"data": {"total_credits": 50.0, "total_usage": 12.25}}
            )
        )
        result = account_client.credits.get()
        assert isinstance(result, Credits)
        assert result.total_credits == 50.0
        assert result.total_usage == 12.25
        auth = route.calls[0].request.headers["Authorization"]
        assert auth == "Bearer mgmt_test"


class TestGenerations:
    @respx.mock
    def test_get(self, account_client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/v1/generation").mock(
            return_value=httpx.Response(200, json={"data": MOCK_GENERATION})
        )
        result = account_client.generations.get("req-abc")
        assert isinstance(result, Generation)
        assert result.provider_name == "alice-shop"
        assert result.total_cost == 0.000412
        assert result.native_tokens_reasoning is None
        assert "id=req-abc" in str(route.calls[0].request.url)


class TestAPIKeys:
    @respx.mock
    def test_current_inference_key(self, account_client: Onlist) -> None:
        respx.get("https://onlist.io/api/v1/key").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        **MOCK_KEY,
                        "is_free_tier": False,
                        "is_management_key": False,
                        "is_provisioning_key": False,
                        "rate_limit": {"requests": -1, "interval": "", "note": "deprecated"},
                    }
                },
            )
        )
        result = account_client.api_keys.current()
        assert isinstance(result, CurrentKey)
        assert result.is_management_key is False
        assert result.rate_limit is not None
        assert result.rate_limit.requests == -1

    @respx.mock
    def test_current_management_key(self, account_client: Onlist) -> None:
        """The 10-field management projection must parse through the same model."""
        respx.get("https://onlist.io/api/v1/key").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "label": "mgmt_...cdef",
                        "name": "ci",
                        "limit": None,
                        "limit_remaining": None,
                        "limit_reset": None,
                        "usage": 0,
                        "is_free_tier": False,
                        "is_management_key": True,
                        "is_provisioning_key": False,
                        "rate_limit": {"requests": -1, "interval": "", "note": "deprecated"},
                    }
                },
            )
        )
        result = account_client.api_keys.current()
        assert result.is_management_key is True
        assert result.hash is None
        assert result.limit is None

    @respx.mock
    def test_list(self, account_client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/v1/keys").mock(
            return_value=httpx.Response(200, json={"data": [MOCK_KEY]})
        )
        result = account_client.api_keys.list(offset=100, include_disabled=True)
        assert len(result) == 1
        assert isinstance(result[0], APIKey)
        assert result[0].hash == "42"
        url = str(route.calls[0].request.url)
        assert "offset=100" in url
        assert "include_disabled=true" in url

    @respx.mock
    def test_list_empty(self, account_client: Onlist) -> None:
        respx.get("https://onlist.io/api/v1/keys").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        assert account_client.api_keys.list() == []

    @respx.mock
    def test_create_returns_plaintext_and_data(self, account_client: Onlist) -> None:
        route = respx.post("https://onlist.io/api/v1/keys").mock(
            return_value=httpx.Response(201, json={"data": MOCK_KEY, "key": "sk-plaintext-once"})
        )
        result = account_client.api_keys.create("prod", limit=25.0, limit_reset="daily")
        assert isinstance(result, CreatedKey)
        # The sibling ``key`` must survive envelope handling — it is returned once.
        assert result.key == "sk-plaintext-once"
        assert result.data.hash == "42"
        body = respx.calls[0].request.content.decode()
        assert '"name":"prod"' in body.replace(" ", "")
        assert '"limit":25.0' in body.replace(" ", "")
        assert route.call_count == 1

    @respx.mock
    def test_create_omits_unset_optionals(self, account_client: Onlist) -> None:
        respx.post("https://onlist.io/api/v1/keys").mock(
            return_value=httpx.Response(201, json={"data": MOCK_KEY, "key": "sk-x"})
        )
        account_client.api_keys.create("minimal")
        body = respx.calls[0].request.content.decode()
        assert "limit" not in body
        assert "expires_at" not in body

    @respx.mock
    def test_get(self, account_client: Onlist) -> None:
        respx.get("https://onlist.io/api/v1/keys/42").mock(
            return_value=httpx.Response(200, json={"data": MOCK_KEY})
        )
        assert account_client.api_keys.get("42").name == "prod"

    @respx.mock
    def test_update_omits_absent_fields(self, account_client: Onlist) -> None:
        respx.patch("https://onlist.io/api/v1/keys/42").mock(
            return_value=httpx.Response(200, json={"data": MOCK_KEY})
        )
        account_client.api_keys.update("42", name="renamed")
        body = respx.calls[0].request.content.decode()
        assert '"name"' in body
        # Anything not passed must not appear at all: an absent key means
        # "leave it alone", a present null means "clear it".
        for absent in ("disabled", "limit", "limit_reset", "expires_at"):
            assert absent not in body

    @respx.mock
    def test_update_none_sends_json_null(self, account_client: Onlist) -> None:
        respx.patch("https://onlist.io/api/v1/keys/42").mock(
            return_value=httpx.Response(200, json={"data": MOCK_KEY})
        )
        account_client.api_keys.update("42", limit=None)
        body = respx.calls[0].request.content.decode().replace(" ", "")
        assert '"limit":null' in body

    @respx.mock
    def test_update_disabled_false_is_sent(self, account_client: Onlist) -> None:
        """``disabled=False`` is a real instruction, not an absent value."""
        respx.patch("https://onlist.io/api/v1/keys/42").mock(
            return_value=httpx.Response(200, json={"data": MOCK_KEY})
        )
        account_client.api_keys.update("42", disabled=False)
        body = respx.calls[0].request.content.decode().replace(" ", "")
        assert '"disabled":false' in body

    @respx.mock
    def test_delete(self, account_client: Onlist) -> None:
        respx.delete("https://onlist.io/api/v1/keys/42").mock(
            return_value=httpx.Response(200, json={"data": {"deleted": True}})
        )
        assert account_client.api_keys.delete("42") is True


class TestActivity:
    @respx.mock
    def test_list(self, account_client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/v1/activity").mock(
            return_value=httpx.Response(200, json={"data": [MOCK_ACTIVITY_ROW]})
        )
        rows = account_client.activity.list(date="2026-09-05", api_key_hash="42")
        assert len(rows) == 1
        assert rows[0].requests == 40
        assert rows[0].usage == 1.25
        url = str(route.calls[0].request.url)
        assert "date=2026-09-05" in url
        assert "api_key_hash=42" in url

    @respx.mock
    def test_list_no_params(self, account_client: Onlist) -> None:
        route = respx.get("https://onlist.io/api/v1/activity").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        assert account_client.activity.list() == []
        assert str(route.calls[0].request.url).endswith("/api/v1/activity")


class TestOAuth:
    @respx.mock
    def test_exchange(self, account_client: Onlist) -> None:
        # The exchange response is bare — no ``data`` envelope at all.
        respx.post("https://onlist.io/api/v1/auth/keys").mock(
            return_value=httpx.Response(200, json={"key": "sk-from-oauth", "user_id": None})
        )
        result = account_client.oauth.exchange("code-123", code_verifier="v" * 43)
        assert isinstance(result, ExchangedKey)
        assert result.key == "sk-from-oauth"
        assert result.user_id is None
        body = respx.calls[0].request.content.decode().replace(" ", "")
        assert '"code":"code-123"' in body


class TestExchangeAuthCode:
    """The credential-free path.

    An app running the sign-in flow has no API key yet — that is the point of
    the flow — so the exchange must not require a constructed client.
    """

    def test_onlist_still_requires_a_credential(self) -> None:
        import openai

        with pytest.raises(openai.OpenAIError):
            Onlist(api_key=None)

    @respx.mock
    def test_module_level_exchange_needs_no_client(self) -> None:
        respx.post("https://example.test/api/v1/auth/keys").mock(
            return_value=httpx.Response(200, json={"key": "sk-from-oauth", "user_id": None})
        )
        result = exchange_auth_code(
            "code-123", code_verifier="v" * 43, base_url="https://example.test"
        )
        assert isinstance(result, ExchangedKey)
        assert result.key == "sk-from-oauth"
        # No Authorization header: the endpoint is unauthenticated.
        assert "authorization" not in respx.calls[0].request.headers

    @respx.mock
    async def test_async_module_level_exchange(self) -> None:
        respx.post("https://example.test/api/v1/auth/keys").mock(
            return_value=httpx.Response(200, json={"key": "sk-async", "user_id": None})
        )
        result = await async_exchange_auth_code(
            "code-123", code_verifier="v" * 43, base_url="https://example.test"
        )
        assert result.key == "sk-async"

    @respx.mock
    def test_defaults_to_production(self) -> None:
        respx.post("https://onlist.io/api/v1/auth/keys").mock(
            return_value=httpx.Response(200, json={"key": "sk-prod", "user_id": None})
        )
        assert exchange_auth_code("code-123").key == "sk-prod"


class TestGeneratePkce:
    def test_shape(self) -> None:
        verifier, challenge = generate_pkce()
        # RFC 7636 requires 43-128 characters; the server enforces the same.
        assert len(verifier) == 43
        assert len(challenge) == 43
        assert "=" not in verifier and "=" not in challenge

    def test_challenge_is_s256_of_verifier(self) -> None:
        import base64
        import hashlib

        verifier, challenge = generate_pkce()
        expected = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        assert challenge == expected

    def test_unique_per_call(self) -> None:
        assert generate_pkce()[0] != generate_pkce()[0]


class TestUpdateSignature:
    """The three-state contract on ``api_keys.update`` is enforced by types.

    ``name`` and ``disabled`` must not accept ``None``: the server reads
    ``{"name": null}`` as an empty name (400) and ``{"disabled": null}`` as
    ``false``, which re-enables a key the caller only meant to leave alone.
    Only ``limit`` / ``limit_reset`` / ``expires_at`` are clearable.
    """

    @pytest.mark.parametrize("cls", [AccountAPIKeys, AsyncAccountAPIKeys])
    def test_name_and_disabled_reject_none(self, cls: type) -> None:
        hints = typing.get_type_hints(cls.update)
        assert type(None) not in _union_args(hints["name"])
        assert type(None) not in _union_args(hints["disabled"])

    @pytest.mark.parametrize("cls", [AccountAPIKeys, AsyncAccountAPIKeys])
    def test_clearable_fields_accept_none(self, cls: type) -> None:
        hints = typing.get_type_hints(cls.update)
        for field in ("limit", "limit_reset", "expires_at"):
            assert type(None) in _union_args(hints[field])


class TestAccountErrors:
    @respx.mock
    def test_403_raises_permission_denied_with_server_message(self, account_client: Onlist) -> None:
        respx.get("https://onlist.io/api/v1/credits").mock(
            return_value=httpx.Response(403, json=FORBIDDEN_BODY)
        )
        with pytest.raises(PermissionDeniedError) as exc_info:
            account_client.credits.get()
        assert exc_info.value.status_code == 403
        # The server's wording is already precise; the SDK must not rewrite it.
        assert exc_info.value.message == "Only management keys can perform this operation"

    @respx.mock
    def test_integer_error_code_does_not_crash(self, account_client: Onlist) -> None:
        """OpenRouter's ``code`` is an int; string methods on it used to blow up."""
        respx.get("https://onlist.io/api/v1/keys").mock(
            return_value=httpx.Response(
                400, json={"error": {"code": 400, "message": "invalid key hash"}}
            )
        )
        with pytest.raises(BadRequestError) as exc_info:
            account_client.api_keys.list()
        assert exc_info.value.code == 400
        assert exc_info.value.message == "invalid key hash"


class TestAccountRetry:
    @respx.mock
    def test_get_retries_on_503(self, account_client: Onlist) -> None:
        calls = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls < 3:
                return httpx.Response(503, json={"error": {"code": 503, "message": "down"}})
            return httpx.Response(200, json={"data": {"total_credits": 1.0, "total_usage": 0.0}})

        respx.get("https://onlist.io/api/v1/credits").mock(side_effect=side_effect)
        assert account_client.credits.get().total_credits == 1.0
        assert calls == 3

    @respx.mock
    def test_post_is_never_retried(self, account_client: Onlist) -> None:
        """Replaying POST /keys would mint a second key."""
        calls = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(503, json={"error": {"code": 503, "message": "down"}})

        respx.post("https://onlist.io/api/v1/keys").mock(side_effect=side_effect)
        with pytest.raises(APIError):
            account_client.api_keys.create("prod")
        assert calls == 1

    @respx.mock
    def test_oauth_exchange_is_never_retried(self, account_client: Onlist) -> None:
        """Replaying the exchange would burn an already-consumed code."""
        calls = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(500, json={"error": {"code": 500, "message": "boom"}})

        respx.post("https://onlist.io/api/v1/auth/keys").mock(side_effect=side_effect)
        with pytest.raises(APIError):
            account_client.oauth.exchange("code-123")
        assert calls == 1


class TestManagementKeyResolution:
    def test_explicit_management_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = Onlist(api_key="sk-a", management_key="mgmt_b")
        assert client.management_key == "mgmt_b"

    def test_env_management_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENV_MANAGEMENT_KEY, "mgmt_from_env")
        client = Onlist(api_key="sk-a")
        assert client.management_key == "mgmt_from_env"

    def test_falls_back_to_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = Onlist(api_key="sk-a")
        assert client.management_key == "sk-a"

    @respx.mock
    def test_fallback_key_reaches_the_wire(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No local prefix check: an ``sk-`` key is sent, and the server decides."""
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = Onlist(api_key="sk-only")
        route = respx.get("https://onlist.io/api/v1/credits").mock(
            return_value=httpx.Response(403, json=FORBIDDEN_BODY)
        )
        with pytest.raises(PermissionDeniedError):
            client.credits.get()
        assert route.calls[0].request.headers["Authorization"] == "Bearer sk-only"


class TestAsyncAccount:
    async def test_credits_get(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = AsyncOnlist(api_key="sk-test", management_key="mgmt_test")
        with respx.mock:
            respx.get("https://onlist.io/api/v1/credits").mock(
                return_value=httpx.Response(
                    200, json={"data": {"total_credits": 8.0, "total_usage": 3.0}}
                )
            )
            result = await client.credits.get()
        assert result.total_credits == 8.0
        await client.close()

    async def test_api_keys_roundtrip(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = AsyncOnlist(api_key="sk-test", management_key="mgmt_test")
        with respx.mock:
            respx.post("https://onlist.io/api/v1/keys").mock(
                return_value=httpx.Response(201, json={"data": MOCK_KEY, "key": "sk-new"})
            )
            respx.patch("https://onlist.io/api/v1/keys/42").mock(
                return_value=httpx.Response(200, json={"data": MOCK_KEY})
            )
            respx.delete("https://onlist.io/api/v1/keys/42").mock(
                return_value=httpx.Response(200, json={"data": {"deleted": True}})
            )
            created = await client.api_keys.create("prod")
            assert created.key == "sk-new"
            updated = await client.api_keys.update("42", limit=None)
            assert updated.hash == "42"
            assert await client.api_keys.delete("42") is True
        await client.close()

    async def test_generations_and_activity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = AsyncOnlist(api_key="sk-test", management_key="mgmt_test")
        with respx.mock:
            respx.get("https://onlist.io/api/v1/generation").mock(
                return_value=httpx.Response(200, json={"data": MOCK_GENERATION})
            )
            respx.get("https://onlist.io/api/v1/activity").mock(
                return_value=httpx.Response(200, json={"data": [MOCK_ACTIVITY_ROW]})
            )
            gen = await client.generations.get("req-abc")
            rows = await client.activity.list()
        assert gen.model == "deepseek/deepseek-chat"
        assert rows[0].date == "2026-09-05"
        await client.close()

    async def test_current_and_oauth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(ENV_MANAGEMENT_KEY, raising=False)
        client = AsyncOnlist(api_key="sk-test", management_key="mgmt_test")
        with respx.mock:
            respx.get("https://onlist.io/api/v1/key").mock(
                return_value=httpx.Response(200, json={"data": {"is_management_key": True}})
            )
            respx.post("https://onlist.io/api/v1/auth/keys").mock(
                return_value=httpx.Response(200, json={"key": "sk-oauth", "user_id": None})
            )
            current = await client.api_keys.current()
            exchanged = await client.oauth.exchange("code", code_verifier="v" * 43)
        assert current.is_management_key is True
        assert exchanged.key == "sk-oauth"
        await client.close()
