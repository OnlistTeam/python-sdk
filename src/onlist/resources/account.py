"""Account resources — the OpenRouter-compatible ``/api/v1/*`` face.

Namespaces follow the wire path segments (``credits``, ``generations``,
``api_keys``, ``activity``) and methods use a fixed verb set
(``list``/``get``/``create``/``update``/``delete``). Two departures, both
forced: ``GET /api/v1/key`` has no matching verb so it is
:meth:`AccountAPIKeys.current`, and ``/api/v1/auth/*`` would read as client
authentication config so the namespace is ``oauth``.

Most of these endpoints require a **management key** (``mgmt_…``). The SDK
does not inspect key prefixes locally — it sends whatever credential it was
given and surfaces the server's 403 as
:class:`~onlist.PermissionDeniedError`.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Any, Union

import httpx
from openai import NOT_GIVEN, NotGiven

from onlist._constants import MARKETPLACE_BASE_URL
from onlist._transport import (
    _DEFAULT_TIMEOUT,
    _async_request,
    _default_headers,
    _encode_path,
    _parse_response,
    _sync_request,
)
from onlist.types.account import (
    ActivityRow,
    APIKey,
    CreatedKey,
    Credits,
    CurrentKey,
    ExchangedKey,
    Generation,
)

__all__ = [
    "AccountAPIKeys",
    "AccountActivity",
    "AccountCredits",
    "AccountGenerations",
    "AccountOAuth",
    "AsyncAccountAPIKeys",
    "AsyncAccountActivity",
    "AsyncAccountCredits",
    "AsyncAccountGenerations",
    "AsyncAccountOAuth",
    "async_exchange_auth_code",
    "exchange_auth_code",
    "generate_pkce",
]

# Three-state parameters on ``api_keys.update``. ``None`` means "send JSON
# null" (clear the value); ``NOT_GIVEN`` means "omit the key" (leave it
# alone). ``Union`` rather than ``X | Y`` because these are runtime values,
# and the SDK supports Python 3.9.
_OptionalFloat = Union[float, None, NotGiven]
_OptionalStr = Union[str, None, NotGiven]
_OptionalInt = Union[int, None, NotGiven]


def generate_pkce() -> tuple[str, str]:
    """Generate an S256 PKCE ``(code_verifier, code_challenge)`` pair.

    Send the challenge to ``/auth`` when starting the browser flow, keep the
    verifier in memory, and pass it back to :meth:`AccountOAuth.exchange`::

        verifier, challenge = generate_pkce()
        webbrowser.open(
            f"https://onlist.io/auth?callback_url={cb}"
            f"&code_challenge={challenge}&code_challenge_method=S256"
        )
        result = client.oauth.exchange(code, code_verifier=verifier)
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def exchange_auth_code(
    code: str,
    *,
    code_verifier: str = "",
    base_url: str = MARKETPLACE_BASE_URL,
    timeout: float = _DEFAULT_TIMEOUT,
) -> ExchangedKey:
    """Exchange a PKCE authorization code for an inference key, with no client.

    ``client.oauth.exchange()`` does the same thing, but building an
    :class:`~onlist.Onlist` requires an API key — and an app running the
    "Sign in with Onlist" flow does not have one yet. That is the entire
    point of the flow, so it gets a credential-free entry point::

        verifier, challenge = generate_pkce()
        # ...user approves in the browser, your callback receives ?code=...
        result = exchange_auth_code(code, code_verifier=verifier)
        client = Onlist(api_key=result.key)

    Single-use: the code is consumed even when the verifier turns out to be
    wrong, so a failure means restarting the browser flow.
    """
    with httpx.Client(base_url=base_url, headers=_default_headers(None), timeout=timeout) as client:
        return AccountOAuth(client, 0).exchange(code, code_verifier=code_verifier)


async def async_exchange_auth_code(
    code: str,
    *,
    code_verifier: str = "",
    base_url: str = MARKETPLACE_BASE_URL,
    timeout: float = _DEFAULT_TIMEOUT,
) -> ExchangedKey:
    """Async version of :func:`exchange_auth_code`."""
    async with httpx.AsyncClient(
        base_url=base_url, headers=_default_headers(None), timeout=timeout
    ) as client:
        return await AsyncAccountOAuth(client, 0).exchange(code, code_verifier=code_verifier)


def _unwrap(body: Any) -> Any:
    """Unwrap the OpenRouter ``{"data": …}`` envelope.

    Only used where the payload is entirely inside ``data``. ``POST /keys``
    and ``POST /auth/keys`` carry fields alongside it and are parsed whole.
    """
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _list_params(offset: int, include_disabled: bool) -> dict[str, Any]:
    return {"offset": offset, "include_disabled": str(include_disabled).lower()}


def _activity_params(date: str | None, api_key_hash: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if date:
        params["date"] = date
    if api_key_hash:
        params["api_key_hash"] = api_key_hash
    return params


def _create_body(
    name: str,
    limit: float | None,
    limit_reset: str | None,
    expires_at: int | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name}
    if limit is not None:
        body["limit"] = limit
    if limit_reset is not None:
        body["limit_reset"] = limit_reset
    if expires_at is not None:
        body["expires_at"] = expires_at
    return body


def _update_body(
    name: str | NotGiven,
    disabled: bool | NotGiven,
    limit: _OptionalFloat,
    limit_reset: _OptionalStr,
    expires_at: _OptionalInt,
) -> dict[str, Any]:
    """Build a PATCH body where an absent key means "do not touch".

    ``name`` and ``disabled`` accept no ``None``: the server reads
    ``{"name": null}`` as an empty name (400) and ``{"disabled": null}`` as
    ``false``, which would silently *re-enable* a key someone meant to leave
    alone. The type signature is what keeps that from happening.
    """
    body: dict[str, Any] = {}
    if not isinstance(name, NotGiven):
        body["name"] = name
    if not isinstance(disabled, NotGiven):
        body["disabled"] = disabled
    if not isinstance(limit, NotGiven):
        body["limit"] = limit
    if not isinstance(limit_reset, NotGiven):
        body["limit_reset"] = limit_reset
    if not isinstance(expires_at, NotGiven):
        body["expires_at"] = expires_at
    return body


def _deleted(body: Any) -> bool:
    data = _unwrap(body)
    return bool(data.get("deleted")) if isinstance(data, dict) else False


# ---------------------------------------------------------------------------
# Sync resource classes
# ---------------------------------------------------------------------------


class AccountCredits:
    """Account balance. Requires a management key."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def get(self) -> Credits:
        """Get lifetime credits purchased and credits used, in USD."""
        resp = _sync_request(self._client, "GET", "/api/v1/credits", max_retries=self._max_retries)
        return Credits.model_validate(_unwrap(_parse_response(resp)))


class AccountGenerations:
    """Per-call cost and timing.

    Accepts either credential type: an inference key can look up only the
    calls it made, a management key any call on the account.
    """

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def get(self, request_id: str) -> Generation:
        """Look up one call by request ID.

        Args:
            request_id: The value of the ``X-Oneapi-Request-Id`` response
                header from the original call.
        """
        resp = _sync_request(
            self._client,
            "GET",
            "/api/v1/generation",
            params={"id": request_id},
            max_retries=self._max_retries,
        )
        return Generation.model_validate(_unwrap(_parse_response(resp)))


class AccountAPIKeys:
    """Manage inference keys (``sk-…``). Requires a management key.

    The exception is :meth:`current`, which answers for whichever credential
    made the request.
    """

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def current(self) -> CurrentKey:
        """Describe the credential this client is using."""
        resp = _sync_request(self._client, "GET", "/api/v1/key", max_retries=self._max_retries)
        return CurrentKey.model_validate(_unwrap(_parse_response(resp)))

    def list(self, *, offset: int = 0, include_disabled: bool = False) -> list[APIKey]:
        """List inference keys.

        Pages are a fixed 100 keys and no total is returned: request
        ``offset += 100`` until you get a short page.

        Args:
            offset: Number of keys to skip.
            include_disabled: Include disabled keys in the result.
        """
        resp = _sync_request(
            self._client,
            "GET",
            "/api/v1/keys",
            params=_list_params(offset, include_disabled),
            max_retries=self._max_retries,
        )
        rows = _unwrap(_parse_response(resp)) or []
        return [APIKey.model_validate(row) for row in rows]

    def create(
        self,
        name: str,
        *,
        limit: float | None = None,
        limit_reset: str | None = None,
        expires_at: int | None = None,
    ) -> CreatedKey:
        """Create an inference key.

        The plaintext secret is on ``.key`` of the result and is never
        retrievable again.

        Args:
            name: Display name for the key. Required.
            limit: Spend budget in USD. ``None`` means no budget.
            limit_reset: ``"daily"``, ``"weekly"``, or ``None`` for a
                lifetime total. ``"monthly"`` is rejected by the server.
            expires_at: Expiry as a Unix timestamp. ``None`` never expires.
        """
        resp = _sync_request(
            self._client,
            "POST",
            "/api/v1/keys",
            json=_create_body(name, limit, limit_reset, expires_at),
            max_retries=self._max_retries,
        )
        return CreatedKey.model_validate(_parse_response(resp))

    def get(self, hash: str) -> APIKey:
        """Get one inference key by its ``hash``."""
        resp = _sync_request(
            self._client, "GET", f"/api/v1/keys/{_encode_path(hash)}", max_retries=self._max_retries
        )
        return APIKey.model_validate(_unwrap(_parse_response(resp)))

    def update(
        self,
        hash: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        disabled: bool | NotGiven = NOT_GIVEN,
        limit: _OptionalFloat = NOT_GIVEN,
        limit_reset: _OptionalStr = NOT_GIVEN,
        expires_at: _OptionalInt = NOT_GIVEN,
    ) -> APIKey:
        """Update an inference key. Omitted arguments are left unchanged.

        For ``limit``, ``limit_reset`` and ``expires_at``, passing ``None``
        clears the value; omitting the argument leaves it alone.
        """
        resp = _sync_request(
            self._client,
            "PATCH",
            f"/api/v1/keys/{_encode_path(hash)}",
            json=_update_body(name, disabled, limit, limit_reset, expires_at),
            max_retries=self._max_retries,
        )
        return APIKey.model_validate(_unwrap(_parse_response(resp)))

    def delete(self, hash: str) -> bool:
        """Delete an inference key. Returns ``True`` on success."""
        resp = _sync_request(
            self._client,
            "DELETE",
            f"/api/v1/keys/{_encode_path(hash)}",
            max_retries=self._max_retries,
        )
        return _deleted(_parse_response(resp))


class AccountActivity:
    """Daily usage rollups. Requires a management key."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def list(
        self, *, date: str | None = None, api_key_hash: str | None = None
    ) -> list[ActivityRow]:
        """List usage grouped by day, model and provider.

        Covers the last 30 complete UTC days; today is excluded.

        Args:
            date: Restrict to one ``YYYY-MM-DD`` UTC day inside the window.
            api_key_hash: Restrict to one inference key. A hash belonging to
                another account yields an empty list, not an error.
        """
        resp = _sync_request(
            self._client,
            "GET",
            "/api/v1/activity",
            params=_activity_params(date, api_key_hash),
            max_retries=self._max_retries,
        )
        rows = _unwrap(_parse_response(resp)) or []
        return [ActivityRow.model_validate(row) for row in rows]


class AccountOAuth:
    """Sign in with Onlist — the PKCE authorization-code exchange.

    Only the exchange lives here. The authorization step itself happens in
    the user's browser at ``https://onlist.io/auth``; there is no SDK call
    for it, because the SDK has no session to authorize with.
    """

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def exchange(self, code: str, *, code_verifier: str = "") -> ExchangedKey:
        """Exchange an authorization code for a new inference key.

        Unauthenticated, and single-use: the code is consumed even when the
        verifier turns out to be wrong, so a failure means restarting the
        browser flow.

        Args:
            code: The ``code`` query parameter from the callback URL.
            code_verifier: The verifier from :func:`generate_pkce`. Required
                whenever the authorization request carried a challenge.
        """
        resp = _sync_request(
            self._client,
            "POST",
            "/api/v1/auth/keys",
            json={"code": code, "code_verifier": code_verifier},
            max_retries=self._max_retries,
        )
        return ExchangedKey.model_validate(_parse_response(resp))


# ---------------------------------------------------------------------------
# Async mirror
# ---------------------------------------------------------------------------


class AsyncAccountCredits:
    """Async version of :class:`AccountCredits`."""

    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def get(self) -> Credits:
        resp = await _async_request(
            self._client, "GET", "/api/v1/credits", max_retries=self._max_retries
        )
        return Credits.model_validate(_unwrap(_parse_response(resp)))


class AsyncAccountGenerations:
    """Async version of :class:`AccountGenerations`."""

    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def get(self, request_id: str) -> Generation:
        resp = await _async_request(
            self._client,
            "GET",
            "/api/v1/generation",
            params={"id": request_id},
            max_retries=self._max_retries,
        )
        return Generation.model_validate(_unwrap(_parse_response(resp)))


class AsyncAccountAPIKeys:
    """Async version of :class:`AccountAPIKeys`."""

    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def current(self) -> CurrentKey:
        resp = await _async_request(
            self._client, "GET", "/api/v1/key", max_retries=self._max_retries
        )
        return CurrentKey.model_validate(_unwrap(_parse_response(resp)))

    async def list(self, *, offset: int = 0, include_disabled: bool = False) -> list[APIKey]:
        resp = await _async_request(
            self._client,
            "GET",
            "/api/v1/keys",
            params=_list_params(offset, include_disabled),
            max_retries=self._max_retries,
        )
        rows = _unwrap(_parse_response(resp)) or []
        return [APIKey.model_validate(row) for row in rows]

    async def create(
        self,
        name: str,
        *,
        limit: float | None = None,
        limit_reset: str | None = None,
        expires_at: int | None = None,
    ) -> CreatedKey:
        resp = await _async_request(
            self._client,
            "POST",
            "/api/v1/keys",
            json=_create_body(name, limit, limit_reset, expires_at),
            max_retries=self._max_retries,
        )
        return CreatedKey.model_validate(_parse_response(resp))

    async def get(self, hash: str) -> APIKey:
        resp = await _async_request(
            self._client, "GET", f"/api/v1/keys/{_encode_path(hash)}", max_retries=self._max_retries
        )
        return APIKey.model_validate(_unwrap(_parse_response(resp)))

    async def update(
        self,
        hash: str,
        *,
        name: str | NotGiven = NOT_GIVEN,
        disabled: bool | NotGiven = NOT_GIVEN,
        limit: _OptionalFloat = NOT_GIVEN,
        limit_reset: _OptionalStr = NOT_GIVEN,
        expires_at: _OptionalInt = NOT_GIVEN,
    ) -> APIKey:
        resp = await _async_request(
            self._client,
            "PATCH",
            f"/api/v1/keys/{_encode_path(hash)}",
            json=_update_body(name, disabled, limit, limit_reset, expires_at),
            max_retries=self._max_retries,
        )
        return APIKey.model_validate(_unwrap(_parse_response(resp)))

    async def delete(self, hash: str) -> bool:
        resp = await _async_request(
            self._client,
            "DELETE",
            f"/api/v1/keys/{_encode_path(hash)}",
            max_retries=self._max_retries,
        )
        return _deleted(_parse_response(resp))


class AsyncAccountActivity:
    """Async version of :class:`AccountActivity`."""

    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def list(
        self, *, date: str | None = None, api_key_hash: str | None = None
    ) -> list[ActivityRow]:
        resp = await _async_request(
            self._client,
            "GET",
            "/api/v1/activity",
            params=_activity_params(date, api_key_hash),
            max_retries=self._max_retries,
        )
        rows = _unwrap(_parse_response(resp)) or []
        return [ActivityRow.model_validate(row) for row in rows]


class AsyncAccountOAuth:
    """Async version of :class:`AccountOAuth`."""

    def __init__(self, client: httpx.AsyncClient, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    async def exchange(self, code: str, *, code_verifier: str = "") -> ExchangedKey:
        resp = await _async_request(
            self._client,
            "POST",
            "/api/v1/auth/keys",
            json={"code": code, "code_verifier": code_verifier},
            max_retries=self._max_retries,
        )
        return ExchangedKey.model_validate(_parse_response(resp))
