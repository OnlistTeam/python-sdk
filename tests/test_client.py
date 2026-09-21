from __future__ import annotations

import httpx
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

    def test_httpx_url_base_url(self, api_key: str) -> None:
        """An ``httpx.URL`` must survive the hand-off to openai.

        openai runs on httpx2 while this SDK's own transport runs on httpx, so
        forwarding the object as-is raised ``TypeError: Invalid type for url``.
        The signature advertises ``httpx.URL``, so it has to work.
        """
        c = Onlist(api_key=api_key, base_url=httpx.URL("https://custom.example.com/v1"))
        assert "custom.example.com" in str(c.base_url)

    def test_user_agent_header(self, client: Onlist) -> None:
        headers = client._custom_headers
        ua = headers.get("user-agent") or headers.get("User-Agent", "")
        assert f"onlist-python/{__version__}" in ua

    def test_has_marketplace(self, client: Onlist) -> None:
        assert hasattr(client, "marketplace")
        assert hasattr(client.marketplace, "models")
        assert hasattr(client.marketplace, "providers")
        assert hasattr(client.marketplace, "rankings")

    def test_has_account_namespaces(self, client: Onlist) -> None:
        for ns in ("credits", "generations", "api_keys", "activity", "oauth"):
            assert hasattr(client, ns), ns

    def test_account_base_url_derived(self, client: Onlist) -> None:
        base = client._account_client.base_url
        assert "/v1" not in str(base)
        assert "onlist.io" in str(base)

    def test_marketplace_base_url_derived(self, client: Onlist) -> None:
        mkt_base = client.marketplace._client.base_url
        assert "/v1" not in str(mkt_base)
        assert "onlist.io" in str(mkt_base)

    def test_close_closes_account_client(self, api_key: str) -> None:
        with Onlist(api_key=api_key) as c:
            assert not c._account_client.is_closed
        assert c._account_client.is_closed


class TestAsyncOnlistClient:
    def test_inherits_async_openai(self) -> None:
        assert issubclass(AsyncOnlist, openai.AsyncOpenAI)

    def test_default_base_url(self, api_key: str) -> None:
        c = AsyncOnlist(api_key=api_key)
        assert str(c.base_url).rstrip("/") == BASE_URL

    def test_httpx_url_base_url(self, api_key: str) -> None:
        """Same httpx / httpx2 hand-off as the sync client. See its twin."""
        c = AsyncOnlist(api_key=api_key, base_url=httpx.URL("https://custom.example.com/v1"))
        assert "custom.example.com" in str(c.base_url)

    def test_has_marketplace(self, api_key: str) -> None:
        c = AsyncOnlist(api_key=api_key)
        assert hasattr(c, "marketplace")
        assert hasattr(c.marketplace, "models")
        assert hasattr(c.marketplace, "providers")
        assert hasattr(c.marketplace, "rankings")

    def test_has_account_namespaces(self, api_key: str) -> None:
        c = AsyncOnlist(api_key=api_key)
        for ns in ("credits", "generations", "api_keys", "activity", "oauth"):
            assert hasattr(c, ns), ns
