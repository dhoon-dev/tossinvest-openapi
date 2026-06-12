from __future__ import annotations

import os

from tossinvest import TossInvestClient


def main() -> None:
    with TossInvestClient(
        os.environ["TOSSINVEST_API_KEY"],
        os.environ["TOSSINVEST_SECRET_KEY"],
        account=os.environ["TOSSINVEST_ACCOUNT"],
    ) as client:
        holdings = client.assets.get_holdings()
    print(holdings.model_dump(by_alias=True))


if __name__ == "__main__":
    main()
