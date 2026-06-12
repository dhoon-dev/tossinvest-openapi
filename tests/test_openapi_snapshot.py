from __future__ import annotations

import json
from pathlib import Path

from tossinvest.resources import IMPLEMENTED_OPERATIONS


def test_implemented_operations_match_snapshot() -> None:
    snapshot_path = Path(__file__).with_name("openapi_operations_snapshot.json")
    snapshot = json.loads(snapshot_path.read_text())
    implemented = {
        operation_id: {
            "method": method,
            "path": path,
            "account_required": account_required,
        }
        for operation_id, (method, path, account_required) in IMPLEMENTED_OPERATIONS.items()
    }
    expected = {
        operation_id: {
            "method": details["method"],
            "path": details["path"],
            "account_required": details["account_required"],
        }
        for operation_id, details in snapshot.items()
        if operation_id != "issueOAuth2Token"
    }

    assert implemented == expected


def test_snapshot_records_required_parameters() -> None:
    snapshot_path = Path(__file__).with_name("openapi_operations_snapshot.json")
    snapshot = json.loads(snapshot_path.read_text())

    assert snapshot["getPrices"]["required_query"] == ["symbols"]
    assert snapshot["getCandles"]["required_query"] == ["symbol", "interval"]
    assert snapshot["getOrders"]["required_query"] == ["status"]
    assert snapshot["getBuyingPower"]["required_query"] == ["currency"]
