"""Emulate a property update via API.

The values sent in the PUT are read dynamically from the property's own
configuration (no hard-coded numbers in the request body) so the only source
of truth is the property record itself. The CLI flags below let the caller
override what gets sent without touching the script.
"""
import argparse
import sys

import httpx

BASE = "http://127.0.0.1:8000/api/v1"


def _login(email: str, password: str) -> str:
    response = httpx.post(
        f"{BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["data"]["access_token"]


def _list_properties(headers: dict) -> list[dict]:
    response = httpx.get(f"{BASE}/properties", headers=headers, timeout=5)
    response.raise_for_status()
    return response.json()["data"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="admin@sistalugueis.com")
    parser.add_argument("--password", default="Admin@123")
    parser.add_argument(
        "--cleaning-fee",
        type=float,
        default=None,
        help="Override default_cleaning_fee; defaults to current property value.",
    )
    parser.add_argument(
        "--platform-percent",
        type=float,
        default=None,
        help="Override platform_fee_percent; defaults to current property value.",
    )
    args = parser.parse_args()

    token = _login(args.email, args.password)
    headers = {"Authorization": f"Bearer {token}"}

    properties = _list_properties(headers)
    if not properties:
        print("no properties to update", file=sys.stderr)
        return 1

    prop = properties[0]
    prop_id, name = prop["id"], prop["name"]
    current_cleaning = prop.get("default_cleaning_fee")
    current_percent = prop.get("platform_fee_percent")

    new_cleaning = args.cleaning_fee if args.cleaning_fee is not None else current_cleaning
    new_percent = (
        args.platform_percent if args.platform_percent is not None else current_percent
    )

    print(f"property: id={prop_id} name={name}")
    print(
        f"current: default_cleaning_fee={current_cleaning} "
        f"platform_fee_percent={current_percent}"
    )
    print(
        f"sending: default_cleaning_fee={new_cleaning} "
        f"platform_fee_percent={new_percent}"
    )

    payload = {
        "name": name,
        "property_value": prop["property_value"],
        "monthly_depreciation_percent": prop.get("monthly_depreciation_percent") or 1,
        "default_cleaning_fee": new_cleaning,
        "platform_fee_percent": new_percent,
    }
    put_resp = httpx.put(
        f"{BASE}/properties/{prop_id}",
        headers=headers,
        json=payload,
        timeout=5,
    )
    print(f"PUT status: {put_resp.status_code}")
    print(f"PUT response: {put_resp.json()}")

    after = httpx.get(
        f"{BASE}/properties/{prop_id}", headers=headers, timeout=5
    ).json()["data"]
    print(
        f"persisted: default_cleaning_fee={after.get('default_cleaning_fee')} "
        f"platform_fee_percent={after.get('platform_fee_percent')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
