from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping

import httpx

from ._serialization import join_url, json_body, serialize_query
from .auth import OAuth2TokenProvider
from .config import TossInvestConfig
from .errors import (
    TossInvestAPIError,
    TossInvestAuthError,
    TossInvestHTTPError,
    TossInvestRateLimitError,
    TossInvestValidationError,
)

SAFE_RETRY_METHODS = {"GET", "HEAD", "OPTIONS"}
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
DEFAULT_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 30.0


class SyncHTTPClient:
    """Internal synchronous HTTP adapter shared by public resources."""

    def __init__(
        self,
        config: TossInvestConfig,
        token_provider: OAuth2TokenProvider,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self.token_provider = token_provider
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=config.timeout)

    @property
    def is_closed(self) -> bool:
        """Return whether the owned or injected sync HTTP client is closed."""
        return self._client.is_closed

    def close(self) -> None:
        """Close the owned sync HTTP client, leaving injected clients open."""
        if self._owns_client:
            self._client.close()

    def get_access_token(self) -> str:
        """Return a valid access token using the sync transport."""
        return self.token_provider.get_token(self._client, self.config.base_url)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, object | None] | None = None,
        json: object | None = None,
        authenticated: bool = True,
        account_required: bool = False,
        account: str | int | None = None,
    ) -> object | None:
        """Send a sync API request with auth, account headers, retry, and error mapping."""
        method = method.upper()
        attempt = 0
        retried_auth = False
        while True:
            response = self._send(
                method,
                path,
                params=params,
                json=json,
                authenticated=authenticated,
                account_required=account_required,
                account=account,
            )
            if (
                response.status_code == 401
                and authenticated
                and not retried_auth
                and path != self.token_provider.token_path
            ):
                self.token_provider.invalidate()
                retried_auth = True
                continue
            if response.status_code < 400:
                return parse_success_response(response)
            if _should_retry(method, response.status_code, attempt, self.config.max_retries):
                _sleep_before_retry(response, attempt)
                attempt += 1
                continue
            raise_api_error(response, endpoint=path)

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, object | None] | None,
        json: object | None,
        authenticated: bool,
        account_required: bool,
        account: str | int | None,
    ) -> httpx.Response:
        headers = self._headers(
            authenticated=authenticated, account_required=account_required, account=account
        )
        try:
            return self._client.request(
                method,
                join_url(self.config.base_url, path),
                params=serialize_query(params),
                json=json_body(json),
                headers=headers,
            )
        except httpx.TransportError as exc:
            raise TossInvestHTTPError(
                f"TossInvest HTTP transport failed for {method} {path}.",
                endpoint=path,
            ) from exc

    def _headers(
        self,
        *,
        authenticated: bool,
        account_required: bool,
        account: str | int | None,
    ) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        account_value = self.config.account_header_value(account)
        if account_required and account_value is None:
            raise TossInvestValidationError(
                "This TossInvest operation requires an account. Pass account=... or set a "
                "default account on the client."
            )
        if authenticated:
            token = self.token_provider.get_token(self._client, self.config.base_url)
            headers["Authorization"] = f"Bearer {token}"
        if account_value is not None:
            headers["X-Tossinvest-Account"] = account_value
        return headers


class AsyncHTTPClient:
    """Internal asynchronous HTTP adapter shared by public resources."""

    def __init__(
        self,
        config: TossInvestConfig,
        token_provider: OAuth2TokenProvider,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.token_provider = token_provider
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=config.timeout)

    @property
    def is_closed(self) -> bool:
        """Return whether the owned or injected async HTTP client is closed."""
        return self._client.is_closed

    async def close(self) -> None:
        """Close the owned async HTTP client, leaving injected clients open."""
        if self._owns_client:
            await self._client.aclose()

    async def get_access_token(self) -> str:
        """Return a valid access token using the async transport."""
        return await self.token_provider.async_get_token(self._client, self.config.base_url)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, object | None] | None = None,
        json: object | None = None,
        authenticated: bool = True,
        account_required: bool = False,
        account: str | int | None = None,
    ) -> object | None:
        """Send an async API request with auth, account headers, retry, and error mapping."""
        method = method.upper()
        attempt = 0
        retried_auth = False
        while True:
            response = await self._send(
                method,
                path,
                params=params,
                json=json,
                authenticated=authenticated,
                account_required=account_required,
                account=account,
            )
            if (
                response.status_code == 401
                and authenticated
                and not retried_auth
                and path != self.token_provider.token_path
            ):
                self.token_provider.invalidate()
                retried_auth = True
                continue
            if response.status_code < 400:
                return parse_success_response(response)
            if _should_retry(method, response.status_code, attempt, self.config.max_retries):
                await _async_sleep_before_retry(response, attempt)
                attempt += 1
                continue
            raise_api_error(response, endpoint=path)

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, object | None] | None,
        json: object | None,
        authenticated: bool,
        account_required: bool,
        account: str | int | None,
    ) -> httpx.Response:
        headers = await self._headers(
            authenticated=authenticated, account_required=account_required, account=account
        )
        try:
            return await self._client.request(
                method,
                join_url(self.config.base_url, path),
                params=serialize_query(params),
                json=json_body(json),
                headers=headers,
            )
        except httpx.TransportError as exc:
            raise TossInvestHTTPError(
                f"TossInvest HTTP transport failed for {method} {path}.",
                endpoint=path,
            ) from exc

    async def _headers(
        self,
        *,
        authenticated: bool,
        account_required: bool,
        account: str | int | None,
    ) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        account_value = self.config.account_header_value(account)
        if account_required and account_value is None:
            raise TossInvestValidationError(
                "This TossInvest operation requires an account. Pass account=... or set a "
                "default account on the client."
            )
        if authenticated:
            token = await self.token_provider.async_get_token(self._client, self.config.base_url)
            headers["Authorization"] = f"Bearer {token}"
        if account_value is not None:
            headers["X-Tossinvest-Account"] = account_value
        return headers


def parse_success_response(response: httpx.Response) -> object | None:
    if not response.content:
        return None
    data = response.json()
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def raise_api_error(response: httpx.Response, *, endpoint: str) -> None:
    body = _safe_response_body(response)
    api_error = body.get("error") if isinstance(body, dict) else None
    api_error = api_error if isinstance(api_error, dict) else {}
    api_code = _string_or_none(api_error.get("code"))
    api_message = _string_or_none(api_error.get("message"))
    request_id = _string_or_none(api_error.get("requestId")) or response.headers.get("x-request-id")
    trace_id = response.headers.get("cf-ray")
    retry_after = response.headers.get("retry-after")
    message = f"TossInvest API request failed with status {response.status_code}."
    if api_code is not None:
        message = (
            f"TossInvest API request failed with status {response.status_code} and code {api_code}."
        )
    error_type: type[TossInvestAPIError]
    if response.status_code == 401:
        error_type = TossInvestAuthError
    elif response.status_code == 429:
        error_type = TossInvestRateLimitError
    else:
        error_type = TossInvestAPIError
    raise error_type(
        message,
        status_code=response.status_code,
        response_body=body,
        request_id=request_id,
        trace_id=trace_id,
        retry_after=retry_after,
        endpoint=endpoint,
        api_code=api_code,
        api_message=api_message,
        response_headers=response.headers,
    )


def _safe_response_body(response: httpx.Response) -> object | None:
    try:
        return response.json()
    except ValueError:
        return response.text


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _should_retry(method: str, status_code: int, attempt: int, max_retries: int) -> bool:
    return (
        method in SAFE_RETRY_METHODS and status_code in RETRYABLE_STATUSES and attempt < max_retries
    )


def _sleep_before_retry(response: httpx.Response, attempt: int) -> None:
    time.sleep(_retry_delay(response, attempt))


async def _async_sleep_before_retry(response: httpx.Response, attempt: int) -> None:
    await asyncio.sleep(_retry_delay(response, attempt))


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    for header in ("retry-after", "x-ratelimit-reset"):
        delay = _retry_header_delay(response.headers.get(header))
        if delay is not None:
            return delay
    return min(MAX_RETRY_DELAY, DEFAULT_RETRY_DELAY * (2**attempt))


def _retry_header_delay(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None
