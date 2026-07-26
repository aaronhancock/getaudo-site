#!/usr/bin/env python3
"""Check or explicitly create Audo's HubSpot deal-attribution properties."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request


API_BASE = os.environ.get("HUBSPOT_API_BASE_URL", "https://api.hubapi.com").rstrip("/")
TOKEN = os.environ.get("HUBSPOT_SERVICE_KEY", "").strip()

PROPERTY_DEFINITIONS = {
    "audo_first_source": "Audo first source",
    "audo_first_landing_url": "Audo first landing URL",
    "audo_first_referring_url": "Audo first referring URL",
    "audo_first_utm_source": "Audo first UTM source",
    "audo_first_utm_medium": "Audo first UTM medium",
    "audo_first_utm_campaign": "Audo first UTM campaign",
    "audo_first_utm_content": "Audo first UTM content",
    "audo_first_campaign_code": "Audo first campaign code",
    "audo_latest_source": "Audo latest source",
    "audo_latest_landing_url": "Audo latest landing URL",
    "audo_latest_referring_url": "Audo latest referring URL",
    "audo_latest_utm_source": "Audo latest UTM source",
    "audo_latest_utm_medium": "Audo latest UTM medium",
    "audo_latest_utm_campaign": "Audo latest UTM campaign",
    "audo_latest_utm_content": "Audo latest UTM content",
    "audo_latest_campaign_code": "Audo latest campaign code",
}


def request(method: str, endpoint: str, payload: dict[str, object] | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        detail = json.loads(raw.decode("utf-8")) if raw else {}
        return exc.code, detail


def property_exists(name: str) -> bool:
    encoded = urllib.parse.quote(name, safe="")
    status, _ = request("GET", f"/crm/v3/properties/deals/{encoded}")
    if status == 200:
        return True
    if status == 404:
        return False
    raise RuntimeError(f"HubSpot property check returned HTTP {status} for {name}")


def create_property(name: str, label: str) -> None:
    status, _ = request(
        "POST",
        "/crm/v3/properties/deals",
        {
            "groupName": "dealinformation",
            "name": name,
            "label": label,
            "description": "First-party Audo discovery attribution; populated from a submitted website inquiry.",
            "type": "string",
            "fieldType": "text",
        },
    )
    if status not in {200, 201, 409}:
        raise RuntimeError(f"HubSpot property creation returned HTTP {status} for {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create missing properties. Without this flag the command is read-only.",
    )
    args = parser.parse_args()
    if not TOKEN:
        raise SystemExit("HUBSPOT_SERVICE_KEY is required.")

    missing = []
    created = []
    for name, label in PROPERTY_DEFINITIONS.items():
        if property_exists(name):
            continue
        missing.append(name)
        if args.apply:
            create_property(name, label)
            created.append(name)

    remaining = [name for name in PROPERTY_DEFINITIONS if not property_exists(name)] if args.apply else missing
    print(
        json.dumps(
            {
                "status": "ready" if not remaining else "missing_properties",
                "checked": len(PROPERTY_DEFINITIONS),
                "created": created,
                "missing": remaining,
            },
            sort_keys=True,
        )
    )
    return 0 if not remaining else 2


if __name__ == "__main__":
    raise SystemExit(main())
