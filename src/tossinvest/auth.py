"""OAuth 2.0 client-credentials token provider."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from ._serialization import join_url
from .errors import TossInvestAuthError
from .models import OAuth2TokenResponse

DEFAULT_TOKEN_PATH = "/oauth2/token"


@dataclass(slots=True)
class _TokenState:
    access_token: str
    expires_at: float


class OAuth2TokenProvider:
    """Issue, cache, and invalidate OAuth access tokens in memory only.

    The provider implements the official OAuth 2.0 client-credentials flow. It
    never persists secrets or tokens and refreshes cached tokens before their
    reported expiration time.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        token_path: str = DEFAULT_TOKEN_PATH,
        refresh_margin_seconds: int = 60,
    ) -> None:
        self.client_id = client_id
        self._client_secret = client_secret
        self.token_path = token_path
        self.refresh_margin_seconds = refresh_margin_seconds
        self._state: _TokenState | None = None

    def invalidate(self) -> None:
        """Forget the cached token so the next request obtains a fresh one."""
        self._state = None

    def get_token(self, client: httpx.Client, base_url: str) -> str:
        """Return a valid access token for synchronous requests.

        Args:
            client: HTTPX client used to send the token request.
            base_url: API server base URL.

        Raises:
            TossInvestAuthError: Token issuance returns an error response.

        """
        if self._state is None or self._is_expired(self._state):
            self._state = self._request_token(client, base_url)
        return self._state.access_token

    async def async_get_token(self, client: httpx.AsyncClient, base_url: str) -> str:
        """Return a valid access token for asynchronous requests.

        Args:
            client: Async HTTPX client used to send the token request.
            base_url: API server base URL.

        Raises:
            TossInvestAuthError: Token issuance returns an error response.

        """
        if self._state is None or self._is_expired(self._state):
            self._state = await self._async_request_token(client, base_url)
        return self._state.access_token

    def _is_expired(self, state: _TokenState) -> bool:
        return time.monotonic() >= state.expires_at

    def _request_token(self, client: httpx.Client, base_url: str) -> _TokenState:
        response = client.post(
            join_url(base_url, self.token_path),
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self._client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return self._parse_token_response(response)

    async def _async_request_token(self, client: httpx.AsyncClient, base_url: str) -> _TokenState:
        response = await client.post(
            join_url(base_url, self.token_path),
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self._client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return self._parse_token_response(response)

    def _parse_token_response(self, response: httpx.Response) -> _TokenState:
        if response.status_code >= 400:
            raise TossInvestAuthError(
                f"Failed to obtain TossInvest access token with status {response.status_code}.",
                status_code=response.status_code,
                response_body=_safe_json(response),
                request_id=response.headers.get("x-request-id"),
                trace_id=response.headers.get("cf-ray"),
                retry_after=response.headers.get("retry-after"),
                endpoint=self.token_path,
                response_headers=response.headers,
            )
        token = OAuth2TokenResponse.model_validate(response.json())
        expires_at = time.monotonic() + max(0, token.expires_in - self.refresh_margin_seconds)
        return _TokenState(access_token=token.access_token, expires_at=expires_at)


def _safe_json(response: httpx.Response) -> object | None:
    try:
        return response.json()
    except ValueError:
        return response.text
