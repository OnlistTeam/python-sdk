"""Shared HTTP transport for the Onlist REST resources.

Both the marketplace resources (``/api/mkt/*``) and the account resources
(``/api/v1/*``) go through here: same headers, same envelope handling, same
retry policy. Keeping one copy is what makes "GET retries, writes do not"
a property of the SDK rather than of whichever module remembered it.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any
from urllib.parse import quote

import httpx

from onlist._exceptions import _raise_for_status
from onlist._version import __version__

_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_RETRIES = 2
_RETRY_INITIAL_DELAY = 0.5
_RETRY_MAX_DELAY = 8.0
_RETRY_JITTER = 0.25
_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


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
    # Only the marketplace envelope ({"success":…,"data":…}) is unwrapped here.
    # The account face uses OpenRouter's {"data":…} without ``success``, and
    # POST /keys returns {"data":…,"key":…} where the sibling key is the whole
    # point — unwrapping either one would silently drop data.
    if isinstance(body, dict) and "data" in body and "success" in body:
        body = body["data"]
    return body


def _retry_delay(attempt: int, response: httpx.Response | None = None) -> float:
    """Compute retry delay with exponential backoff, jitter, and Retry-After support."""
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass

    delay = min(_RETRY_INITIAL_DELAY * (2.0**attempt), _RETRY_MAX_DELAY)
    jitter = delay * _RETRY_JITTER * (2 * random.random() - 1)
    return max(0.0, delay + jitter)


def _should_retry(method: str, status_code: int) -> bool:
    """Whether a request may be replayed.

    Only GET is retried. A replayed ``POST /api/v1/keys`` mints a second API
    key and a replayed ``POST /api/v1/auth/keys`` burns the authorization
    code — in both cases the caller ends up worse off than if the transient
    error had simply surfaced.
    """
    if method.upper() != "GET":
        return False
    return status_code in _RETRYABLE_STATUS_CODES


_RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.PoolTimeout,
    httpx.ConnectTimeout,
)


def _sync_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any = None,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> httpx.Response:
    """Execute an HTTP request with retry logic (exponential backoff + jitter)."""
    retries = max_retries if method.upper() == "GET" else 0
    last_response: httpx.Response | None = None
    last_exc: Exception | None = None

    for attempt in range(1 + retries):
        try:
            response = client.request(method, url, params=params, json=json)
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(_retry_delay(attempt))
                continue
            raise

        if not _should_retry(method, response.status_code) or attempt >= retries:
            return response

        last_response = response
        time.sleep(_retry_delay(attempt, response))

    # Should not reach here, but satisfy the type checker.
    if last_response is not None:
        return last_response
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("unexpected retry loop exit")


async def _async_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any = None,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> httpx.Response:
    """Execute an async HTTP request with retry logic."""
    retries = max_retries if method.upper() == "GET" else 0
    last_response: httpx.Response | None = None
    last_exc: Exception | None = None

    for attempt in range(1 + retries):
        try:
            response = await client.request(method, url, params=params, json=json)
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(_retry_delay(attempt))
                continue
            raise

        if not _should_retry(method, response.status_code) or attempt >= retries:
            return response

        last_response = response
        await asyncio.sleep(_retry_delay(attempt, response))

    if last_response is not None:
        return last_response
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("unexpected retry loop exit")
