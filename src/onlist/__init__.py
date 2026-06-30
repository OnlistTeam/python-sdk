"""Onlist Python SDK -- Official client for the Onlist AI API marketplace."""

from onlist._client import AsyncOnlist, Onlist
from onlist._exceptions import (
    APIError,
    AuthenticationError,
    InsufficientBalanceError,
    NotFoundError,
    OnlistError,
    ProviderError,
    RateLimitError,
)
from onlist._version import __version__
from onlist.types import (
    AppEntry,
    AppListResponse,
    ChartPoint,
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
)

__all__ = [
    # Clients
    "AsyncOnlist",
    "Onlist",
    # Exceptions
    "APIError",
    "AuthenticationError",
    "InsufficientBalanceError",
    "NotFoundError",
    "OnlistError",
    "ProviderError",
    "RateLimitError",
    # Types — Models
    "Model",
    "ModelDetail",
    "ModelListResponse",
    "Pricing",
    "ProviderOffer",
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
    # Meta
    "__version__",
]
