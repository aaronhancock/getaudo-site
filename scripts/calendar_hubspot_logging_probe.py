#!/usr/bin/env python3
"""Create, inspect, or delete a harmless business-calendar logging probe."""

from __future__ import annotations

import argparse
import json
from urllib.parse import quote

import server


EVENT_ID = "audotest20260721"
START = "2026-07-21T07:00:00-05:00"
END = "2026-07-21T07:15:00-05:00"


def endpoint() -> str:
    calendar_id = quote(server.GOOGLE_CALENDAR_ID, safe="")
    return f"/calendars/{calendar_id}/events/{EVENT_ID}"


def create() -> dict:
    calendar_id = quote(server.GOOGLE_CALENDAR_ID, safe="")
    payload = {
        "id": EVENT_ID,
        "summary": "Audo systems verification — calendar logging test",
        "description": "Internal Audo integration verification. Safe to delete after HubSpot logging is checked.",
        "start": {"dateTime": START, "timeZone": "America/Chicago"},
        "end": {"dateTime": END, "timeZone": "America/Chicago"},
        "attendees": [{"email": "matthewaaron@gmail.com"}],
        "transparency": "transparent",
        "visibility": "private",
        "reminders": {"useDefault": False, "overrides": []},
        "guestsCanModify": False,
    }
    try:
        return server.google_calendar_request(
            "POST",
            f"/calendars/{calendar_id}/events",
            query={"sendUpdates": "all"},
            payload=payload,
        )
    except Exception:
        return server.google_calendar_request("GET", endpoint())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "read", "delete"))
    args = parser.parse_args()
    if not server.calendar_configured():
        print(json.dumps({"status": "error", "message": "Google Calendar is not configured"}))
        return 2
    if args.action == "create":
        result = create()
        print(json.dumps({
            "status": "created",
            "eventId": result.get("id"),
            "start": (result.get("start") or {}).get("dateTime"),
            "organizerSelf": bool((result.get("organizer") or {}).get("self")),
            "attendeeCount": len(result.get("attendees") or []),
        }, sort_keys=True))
        return 0
    if args.action == "read":
        result = server.google_calendar_request("GET", endpoint())
        print(json.dumps({
            "status": result.get("status"),
            "eventId": result.get("id"),
            "start": (result.get("start") or {}).get("dateTime"),
            "organizerSelf": bool((result.get("organizer") or {}).get("self")),
            "attendeeCount": len(result.get("attendees") or []),
        }, sort_keys=True))
        return 0
    server.google_calendar_request("DELETE", endpoint(), query={"sendUpdates": "all"})
    print(json.dumps({"status": "deleted", "eventId": EVENT_ID}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
