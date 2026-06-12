from __future__ import annotations

import os

from tossinvest import TossInvestClient


def main() -> None:
    with TossInvestClient(
        os.environ["TOSSINVEST_API_KEY"],
        os.environ["TOSSINVEST_SECRET_KEY"],
    ) as client:
        token = client.get_access_token()
    print(f"Received an access token with {len(token)} characters.")


if __name__ == "__main__":
    main()
