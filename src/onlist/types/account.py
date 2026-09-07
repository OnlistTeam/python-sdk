"""Response types for the account API (``/api/v1/*``).

Field names mirror the wire format one-for-one, which is OpenRouter's, so
code written against OpenRouter's responses reads the same fields here.
Every model allows extra keys: new server-side fields must not break old
SDK versions.
"""

from __future__ import annotations

from pydantic import BaseModel


class RateLimit(BaseModel):
    """The deprecated per-key rate limit descriptor on :class:`CurrentKey`.

    Onlist has no per-key request-rate limit — only spend budgets — so
    ``requests`` is always ``-1``. Do not use it to drive client-side
    throttling.
    """

    requests: int | None = None
    interval: str | None = None
    note: str | None = None

    model_config = {"extra": "allow"}


class APIKey(BaseModel):
    """An inference key (``sk-…``) as returned by the ``api_keys`` resource.

    ``limit``, ``limit_remaining`` and ``limit_reset`` move together: either
    all three are set, or all three are ``None`` (no spend budget). Amounts
    are USD. ``created_at`` / ``expires_at`` are RFC 3339 UTC strings, or
    ``None`` for "never".
    """

    hash: str
    name: str
    label: str
    disabled: bool = False
    limit: float | None = None
    limit_remaining: float | None = None
    limit_reset: str | None = None
    include_byok_in_limit: bool = False
    usage: float = 0.0
    usage_daily: float = 0.0
    usage_weekly: float = 0.0
    usage_monthly: float = 0.0
    byok_usage: float = 0.0
    byok_usage_daily: float = 0.0
    byok_usage_weekly: float = 0.0
    byok_usage_monthly: float = 0.0
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None
    external_user: str | None = None
    creator_user_id: str | None = None
    workspace_id: str | None = None

    model_config = {"extra": "allow"}


class CurrentKey(BaseModel):
    """The credential used for the request, from ``api_keys.current()``.

    Every field is optional because the endpoint answers for both credential
    types and they carry different information: a management key has no
    usage and no budget (reporting ``0`` would read as "an inference key that
    has never spent"), so those fields are simply absent from its projection.
    Branch on :attr:`is_management_key`.
    """

    hash: str | None = None
    name: str | None = None
    label: str | None = None
    disabled: bool | None = None
    limit: float | None = None
    limit_remaining: float | None = None
    limit_reset: str | None = None
    include_byok_in_limit: bool | None = None
    usage: float | None = None
    usage_daily: float | None = None
    usage_weekly: float | None = None
    usage_monthly: float | None = None
    byok_usage: float | None = None
    byok_usage_daily: float | None = None
    byok_usage_weekly: float | None = None
    byok_usage_monthly: float | None = None
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None
    external_user: str | None = None
    creator_user_id: str | None = None
    workspace_id: str | None = None
    is_free_tier: bool | None = None
    is_management_key: bool | None = None
    is_provisioning_key: bool | None = None
    rate_limit: RateLimit | None = None

    model_config = {"extra": "allow"}


class CreatedKey(BaseModel):
    """The result of ``api_keys.create()``.

    :attr:`key` is the full secret in plaintext and is returned **only here,
    only once** — the server keeps a hash. Store it before discarding this
    object. :attr:`data` is the same key object later reads return.
    """

    key: str
    data: APIKey

    model_config = {"extra": "allow"}


class Credits(BaseModel):
    """Account balance, in USD.

    Remaining balance is ``total_credits - total_usage``: the endpoint reports
    lifetime totals rather than a single "balance" number, matching
    OpenRouter.
    """

    total_credits: float = 0.0
    total_usage: float = 0.0

    model_config = {"extra": "allow"}


class Generation(BaseModel):
    """Cost and timing for a single completed call, from ``generations.get()``.

    Fields Onlist has no data for are ``None`` rather than ``0``:
    ``upstream_id``, ``http_referer``, ``user_agent``, ``origin``,
    ``api_type``, ``cache_discount`` and ``native_tokens_reasoning``. For
    reconciliation, "not measured" and "measured as zero" are different
    statements.

    ``latency`` is time-to-first-token in milliseconds and is ``None`` for
    non-streamed calls, which never measure it. ``generation_time`` is total
    wall time in milliseconds. ``total_cost`` and ``usage`` are the same USD
    amount under both of OpenRouter's names.
    """

    id: str
    model: str
    provider_name: str | None = None
    streamed: bool = False
    latency: float | None = None
    generation_time: int = 0
    created_at: str | None = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    native_tokens_prompt: int = 0
    native_tokens_completion: int = 0
    native_tokens_cached: int | None = None
    native_tokens_reasoning: int | None = None
    total_cost: float = 0.0
    usage: float = 0.0
    cache_discount: float | None = None
    finish_reason: str | None = None
    native_finish_reason: str | None = None
    is_byok: bool = False
    upstream_id: str | None = None
    http_referer: str | None = None
    user_agent: str | None = None
    origin: str | None = None
    api_type: str | None = None

    model_config = {"extra": "allow"}


class ActivityRow(BaseModel):
    """One day × model × provider bucket from ``activity.list()``.

    ``date`` is a ``YYYY-MM-DD`` UTC day and ``usage`` is USD. Only complete
    days appear — today is still accumulating, and this endpoint exists for
    reconciliation.
    """

    date: str
    model: str
    model_permaslug: str
    endpoint_id: str
    provider_name: str | None = None
    usage: float = 0.0
    byok_usage_inference: float = 0.0
    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0

    model_config = {"extra": "allow"}


class ExchangedKey(BaseModel):
    """The result of ``oauth.exchange()``.

    :attr:`key` is a new inference key in plaintext, returned once.
    :attr:`user_id` is always ``None`` on Onlist: on OpenRouter it carries the
    calling application's own external user identifier, which Onlist has no
    concept of.
    """

    key: str
    user_id: str | None = None

    model_config = {"extra": "allow"}
