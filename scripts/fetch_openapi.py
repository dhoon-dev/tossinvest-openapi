from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen

DEFAULT_OPENAPI_URL = "https://openapi.tossinvest.com/openapi-docs/latest/openapi.json"
DEFAULT_OUTPUT = Path("openapi/openapi.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the official TossInvest OpenAPI JSON.")
    parser.add_argument("--url", default=DEFAULT_OPENAPI_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with urlopen(args.url, timeout=30) as response:
        payload = response.read()
    document = json.loads(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")

    paths = document.get("paths", {})
    operations = sum(
        1
        for path_item in paths.values()
        if isinstance(path_item, dict)
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    )
    info = document.get("info", {})
    print(
        "Fetched TossInvest OpenAPI "
        f"{info.get('version', 'unknown')} with {len(paths)} paths and {operations} operations."
    )
    print(f"Saved to {args.output}.")


if __name__ == "__main__":
    main()
