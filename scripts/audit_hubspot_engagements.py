#!/usr/bin/env python3
"""Read-only, PII-minimizing audit of HubSpot email and meeting logging."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE = os.environ.get("HUBSPOT_API_BASE_URL", "https://api.hubapi.com").rstrip("/")
TOKEN = os.environ.get("HUBSPOT_SERVICE_KEY", "").strip()


def request(path: str, params: dict[str, str]) -> tuple[int, dict]:
    url = f"{BASE}{path}?{urlencode(params)}"
    req = Request(url, headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        try:
            body = json.load(exc)
        except Exception:
            body = {}
        return exc.code, body
    except URLError as exc:
        return 0, {"category": "network", "message": str(exc.reason)}


def parse_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        if value.isdigit():
            parsed = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (ValueError, TypeError, OSError):
        return None


def audit_object(name: str, properties: list[str], associations: list[str] | None = None) -> dict:
    params = {"limit": "100", "archived": "false", "properties": ",".join(properties)}
    if associations:
        params["associations"] = ",".join(associations)
    status, body = request(
        f"/crm/v3/objects/{name}",
        params,
    )
    if status != 200:
        return {
            "status": status,
            "readable": False,
            "category": body.get("category"),
            "message": body.get("message", "HubSpot did not return records")[:240],
        }
    results = body.get("results") or []
    timestamps: list[str] = []
    sources: dict[str, int] = {}
    associated = {association: 0 for association in associations or []}
    for item in results:
        props = item.get("properties") or {}
        source = props.get("hs_meeting_source") or props.get("hs_activity_type")
        if source:
            sources[source] = sources.get(source, 0) + 1
        for association in associations or []:
            if item.get("associations", {}).get(association, {}).get("results"):
                associated[association] += 1
        for key in ("hs_timestamp", "hs_createdate", "hs_meeting_start_time"):
            parsed = parse_time(props.get(key))
            if parsed:
                timestamps.append(parsed)
                break
    return {
        "status": status,
        "readable": True,
        "recordsReturned": len(results),
        "hasMore": bool(body.get("paging", {}).get("next")),
        "latestTimestampUtc": max(timestamps) if timestamps else None,
        "sourceCounts": sources,
        "recordsWithAssociations": associated,
    }


def main() -> int:
    if not TOKEN:
        print(json.dumps({"status": "error", "message": "HUBSPOT_SERVICE_KEY is not configured"}))
        return 2
    result = {
        "auditedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "emails": audit_object(
            "emails",
            ["hs_timestamp", "hs_createdate", "hs_email_direction", "hs_email_status"],
        ),
        "meetings": audit_object(
            "meetings",
            [
                "hs_timestamp",
                "hs_createdate",
                "hs_meeting_start_time",
                "hs_meeting_end_time",
                "hs_meeting_source",
                "hs_activity_type",
            ],
            ["contacts", "deals"],
        ),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if all(value.get("readable") for key, value in result.items() if key in {"emails", "meetings"}) else 1


if __name__ == "__main__":
    sys.exit(main())
