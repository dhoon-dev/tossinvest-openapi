from __future__ import annotations

import os

from tossinvest import TossInvestClient


def main() -> None:
    with TossInvestClient(
        os.environ["TOSSINVEST_API_KEY"],
        os.environ["TOSSINVEST_SECRET_KEY"],
    ) as client:
        accounts = client.accounts.list_accounts()
    for account in accounts:
        print(account.model_dump(by_alias=True))


if __name__ == "__main__":
    main()
