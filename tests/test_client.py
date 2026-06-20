from __future__ import annotations

import openai

from onlist import AsyncOnlist, Onlist, __version__
from onlist._constants import BASE_URL


class TestOnlistClient:
    def test_inherits_openai(self) -> None:
        assert issubclass(Onlist, openai.OpenAI)

    def test_default_base_url(self, client: Onlist) -> None:
        assert str(client.base_url).rstrip("/") == BASE_URL

    def test_custom_base_url(self, api_key: str) -> None:
        c = Onlist(api_key=api_key, base_url="https://custom.example.com/v1")
        assert "custom.example.com" in str(c.base_url)

    def test_user_agent_header(self, client: Onlist) -> None:
        headers = client._custom_headers
        ua = headers.get("user-agent") or headers.get("User-Agent", "")
        assert f"onlist-python/{__version__}" in ua

    def test_has_marketplace(self, client: Onlist) -> None:
        assert hasattr(client, "marketplace")
        assert hasattr(client.marketplace, "models")
        assert hasattr(client.marketplace, "providers")

    def test_marketplace_base_url_derived(self, client: Onlist) -> None:
        mkt_base = client.marketplace._client.base_url
        assert "/v1" not in str(mkt_base)
        assert "onlist.io" in str(mkt_base)


class TestAsyncOnlistClient:
    def test_inherits_async_openai(self) -> None:
        assert issubclass(AsyncOnlist, openai.AsyncOpenAI)

    def test_default_base_url(self, api_key: str) -> None:
        c = AsyncOnlist(api_key=api_key)
        assert str(c.base_url).rstrip("/") == BASE_URL

    def test_has_marketplace(self, api_key: str) -> None:
        c = AsyncOnlist(api_key=api_key)
        assert hasattr(c, "marketplace")
        assert hasattr(c.marketplace, "models")
        assert hasattr(c.marketplace, "providers")
