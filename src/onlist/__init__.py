"""Onlist Python SDK -- Official client for the Onlist AI API marketplace."""

from onlist._client import AsyncOnlist, Onlist
from onlist._exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    InsufficientBalanceError,
    NotFoundError,
    OnlistError,
    PermissionDeniedError,
    ProviderError,
    RateLimitError,
)
from onlist._version import __version__
from onlist.resources.account import (
    async_exchange_auth_code,
    exchange_auth_code,
    generate_pkce,
)
from onlist.types import (
    ActivityRow,
    APIKey,
    AppEntry,
    AppListResponse,
    ChartPoint,
    CreatedKey,
    Credits,
    CurrentKey,
    ExchangedKey,
    Generation,
    MaxPrice,
    Model,
    ModelDetail,
    ModelListResponse,
    ModelRankingEntry,
    ModelRankingsResponse,
    Pricing,
    Provider,
    ProviderDetail,
    ProviderListResponse,
    ProviderOffer,
    ProviderRouting,
    RateLimit,
    UserModelListResponse,
)

__all__ = [
    # Clients
    "AsyncOnlist",
    "Onlist",
    # Exceptions
    "APIError",
    "AuthenticationError",
    "BadRequestError",
    "InsufficientBalanceError",
    "NotFoundError",
    "OnlistError",
    "PermissionDeniedError",
    "ProviderError",
    "RateLimitError",
    # Types — Models
    "Model",
    "ModelDetail",
    "ModelListResponse",
    "Pricing",
    "ProviderOffer",
    "UserModelListResponse",
    # Types — Providers
    "Provider",
    "ProviderDetail",
    "ProviderListResponse",
    # Types — Rankings
    "AppEntry",
    "AppListResponse",
    "ChartPoint",
    "ModelRankingEntry",
    "ModelRankingsResponse",
    # Types — Routing
    "MaxPrice",
    "ProviderRouting",
    # Types — Account
    "APIKey",
    "ActivityRow",
    "CreatedKey",
    "Credits",
    "CurrentKey",
    "ExchangedKey",
    "Generation",
    "RateLimit",
    # Helpers
    "async_exchange_auth_code",
    "exchange_auth_code",
    "generate_pkce",
    # Meta
    "__version__",
]
