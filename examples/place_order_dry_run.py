from __future__ import annotations

import os

from tossinvest import OrderCreateRequest, TossInvestClient


def main() -> None:
    request = OrderCreateRequest(
        clientOrderId="example-dry-run-001",
        symbol="005930",
        side="BUY",
        orderType="LIMIT",
        quantity="1",
        price="70000",
    )
    if os.getenv("TOSSINVEST_ENABLE_LIVE_ORDER") != "true":
        print("Dry run only. Set TOSSINVEST_ENABLE_LIVE_ORDER=true to submit a live order.")
        print(request.model_dump(by_alias=True, exclude_none=True))
        return

    with TossInvestClient(
        os.environ["TOSSINVEST_API_KEY"],
        os.environ["TOSSINVEST_SECRET_KEY"],
        account=os.environ["TOSSINVEST_ACCOUNT"],
    ) as client:
        response = client.orders.create_order(request)
    print(response.model_dump(by_alias=True))


if __name__ == "__main__":
    main()
