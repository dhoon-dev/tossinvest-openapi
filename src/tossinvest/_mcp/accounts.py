"""Account lookup helpers for the MCP server."""

from __future__ import annotations

from collections.abc import Iterable

from tossinvest.errors import TossInvestValidationError
from tossinvest.models import Account


def find_account_by_number(accounts: Iterable[Account], account_no: str) -> Account:
    """Return the account matching ``account_no``.

    Raises:
        TossInvestValidationError: No returned account matches ``account_no``.

    """
    for account in accounts:
        if account.account_no == account_no:
            return account
    raise TossInvestValidationError("No TossInvest account found for the requested accountNo.")
