"""Account resource methods."""

from __future__ import annotations

from tossinvest._http import AsyncHTTPClient, SyncHTTPClient
from tossinvest.models import Account, parse_model_list


class AccountsResource:
    """Synchronous account endpoints."""

    def __init__(self, http: SyncHTTPClient) -> None:
        self._http = http

    def list_accounts(self) -> list[Account]:
        """List accounts available to the authenticated OAuth client.

        This endpoint requires OAuth but does not require an account header.
        Rate limit group: ``ACCOUNT``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying account endpoints.

        Raises:
            TossInvestAuthError: Authentication fails.
            TossInvestAPIError: The API returns an error response.

        """
        result = self._http.request("GET", "/api/v1/accounts")
        return parse_model_list(Account, result)

    def get_accounts(self) -> list[Account]:
        """Alias for list_accounts matching the official operation name.

        Rate limit group: ``ACCOUNT``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying account endpoints.
        """
        return self.list_accounts()


class AsyncAccountsResource:
    """Asynchronous account endpoints."""

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def list_accounts(self) -> list[Account]:
        """List accounts available to the authenticated OAuth client.

        This endpoint requires OAuth but does not require an account header.
        Rate limit group: ``ACCOUNT``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying account endpoints.

        Raises:
            TossInvestAuthError: Authentication fails.
            TossInvestAPIError: The API returns an error response.

        """
        result = await self._http.request("GET", "/api/v1/accounts")
        return parse_model_list(Account, result)

    async def get_accounts(self) -> list[Account]:
        """Alias for list_accounts matching the official operation name.

        Rate limit group: ``ACCOUNT``. On ``429``, respect ``Retry-After`` or
        ``X-RateLimit-Reset`` before retrying account endpoints.
        """
        return await self.list_accounts()
