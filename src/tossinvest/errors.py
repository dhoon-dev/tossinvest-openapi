"""Exception hierarchy and metadata-bearing HTTP errors."""

from __future__ import annotations

from collections.abc import Mapping


class TossInvestError(Exception):
    """Base class for all SDK exceptions."""


class TossInvestConfigError(TossInvestError):
    """Raised when SDK configuration is invalid."""


class TossInvestValidationError(TossInvestError):
    """Raised before an invalid request is sent."""


class TossInvestHTTPError(TossInvestError):
    """Raised for HTTP transport failures or non-success API responses.

    Attributes:
        status_code: HTTP status code when a response exists.
        response_body: Parsed JSON body, plain text body, or ``None``.
        request_id: API request identifier from the error body or headers.
        trace_id: Edge trace identifier when returned by the server.
        retry_after: Retry delay hint from the ``Retry-After`` header.
        endpoint: SDK endpoint path associated with the failed request.
        api_code: TossInvest error code when returned by the API.
        api_message: Upstream API message when returned by the API.
        response_headers: Response headers copied without request secrets.

    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: object | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        retry_after: str | None = None,
        endpoint: str | None = None,
        api_code: str | None = None,
        api_message: str | None = None,
        response_headers: Mapping[str, str] | None = None,
    ) -> None:
        """Store sanitized response metadata without exposing request secrets."""
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id
        self.trace_id = trace_id
        self.retry_after = retry_after
        self.endpoint = endpoint
        self.api_code = api_code
        self.api_message = api_message
        self.response_headers = dict(response_headers or {})


class TossInvestAPIError(TossInvestHTTPError):
    """Raised for TossInvest API error responses."""


class TossInvestAuthError(TossInvestAPIError):
    """Raised for authentication or authorization failures."""


class TossInvestRateLimitError(TossInvestAPIError):
    """Raised when the API returns a rate limit response."""
