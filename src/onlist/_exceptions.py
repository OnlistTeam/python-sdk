from __future__ import annotations

from typing import Any


class OnlistError(Exception):
    """Base exception for all Onlist SDK errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class APIError(OnlistError):
    """An error returned by the Onlist API.

    ``code`` is whatever the server put in the error body. The marketplace
    face uses string codes (``"no_provider_available"``); the OpenRouter
    compatible account face uses the HTTP status as an integer. Both are
    surfaced as-is rather than normalised, so callers can branch on either.
    """

    status_code: int
    type: str | None
    code: str | int | None
    param: str | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        type: str | None = None,
        code: str | int | None = None,
        param: str | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.type = type
        self.code = code
        self.param = param
        self.body = body

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"code={self.code!r})"
        )


class AuthenticationError(APIError):
    """Raised on 401 responses (missing or invalid API key)."""

    def __init__(self, message: str = "Invalid API key", **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 401)
        super().__init__(message, **kwargs)


class BadRequestError(APIError):
    """Raised on 400 responses (malformed or rejected parameters)."""

    def __init__(self, message: str = "Bad request", **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 400)
        super().__init__(message, **kwargs)


class PermissionDeniedError(APIError):
    """Raised on 403 responses.

    Most commonly: an inference key (``sk-…``) was used on an endpoint that
    only accepts a management key (``mgmt_…``). The server's message is
    passed through unchanged.
    """

    def __init__(self, message: str = "Permission denied", **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 403)
        super().__init__(message, **kwargs)


class InsufficientBalanceError(APIError):
    """Raised on 402 responses (insufficient balance)."""

    def __init__(self, message: str = "Insufficient balance", **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 402)
        super().__init__(message, **kwargs)


class NotFoundError(APIError):
    """Raised on 404 responses (resource not found)."""

    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 404)
        super().__init__(message, **kwargs)


class RateLimitError(APIError):
    """Raised on 429 responses (rate limited)."""

    def __init__(self, message: str = "Rate limited", **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 429)
        super().__init__(message, **kwargs)


class ProviderError(APIError):
    """Raised when no provider is available for the request."""

    pass


def _raise_for_status(status_code: int, body: Any) -> None:
    """Parse an Onlist error response and raise the appropriate exception."""
    error = {}
    if isinstance(body, dict):
        error = body.get("error", body)

    message = error.get("message", str(body)) if isinstance(error, dict) else str(body)
    etype = error.get("type") if isinstance(error, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    param = error.get("param") if isinstance(error, dict) else None

    kwargs = dict(
        status_code=status_code,
        type=etype,
        code=code,
        param=param,
        body=body,
    )

    if status_code == 400:
        raise BadRequestError(message, **kwargs)
    if status_code == 401:
        raise AuthenticationError(message, **kwargs)
    if status_code == 402:
        raise InsufficientBalanceError(message, **kwargs)
    if status_code == 403:
        raise PermissionDeniedError(message, **kwargs)
    if status_code == 404:
        raise NotFoundError(message, **kwargs)
    if status_code == 429:
        raise RateLimitError(message, **kwargs)
    # ``no_provider_*`` always arrives as 503, so this stays reachable below the
    # status mappings. The isinstance guard is load-bearing: the account face
    # sends ``code`` as an int (the HTTP status), and ``int.startswith`` would
    # turn every one of its errors into an AttributeError.
    if isinstance(code, str) and code.startswith("no_provider"):
        raise ProviderError(message, **kwargs)

    raise APIError(message, **kwargs)
