from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from tossinvest import Account, TossInvestClient


@pytest.fixture(scope="module")
def live_client() -> Iterator[TossInvestClient]:
    api_key, secret_key = _read_live_credentials()

    with TossInvestClient(
        api_key,
        secret_key,
        base_url=os.getenv("TOSSINVEST_BASE_URL") or "https://openapi.tossinvest.com",
    ) as client:
        yield client


@pytest.fixture(scope="module")
def live_account(live_accounts: list[Account]) -> str:
    account = os.getenv("TOSSINVEST_ACCOUNT") or None
    if account is not None:
        return account

    return _first_account_seq(live_accounts)


@pytest.fixture(scope="module")
def live_accounts(live_client: TossInvestClient) -> list[Account]:
    return live_client.accounts.list_accounts()


def _first_account_seq(accounts: list[Account]) -> str:
    if not accounts:
        pytest.skip("The live credentials returned no accounts.")
    return str(accounts[0].account_seq)


def _read_live_credentials() -> tuple[str, str]:
    api_key = os.getenv("TOSSINVEST_API_KEY")
    secret_key = os.getenv("TOSSINVEST_SECRET_KEY")
    missing = [
        name
        for name, value in (
            ("TOSSINVEST_API_KEY", api_key),
            ("TOSSINVEST_SECRET_KEY", secret_key),
        )
        if not value
    ]
    if missing:
        pytest.skip("Missing required live test credentials: " + ", ".join(missing))
    assert api_key is not None
    assert secret_key is not None
    return api_key, secret_key


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_dotenv_line(raw_line)
        if parsed is None:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)


def _parse_dotenv_line(raw_line: str) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line.removeprefix("export ").lstrip()
    key, separator, value = line.partition("=")
    if not separator:
        return None
    key = key.strip()
    if not key:
        return None
    return key, _strip_quotes(value.strip())


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


_load_dotenv(Path(__file__).resolve().parents[2] / ".env")
