#!/usr/bin/env python3
"""Report Audo operational queue health without exposing client data."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone()
    return bool(row)


def grouped_counts(connection: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    if not table_exists(connection, table):
        return {}
    rows = connection.execute(
        f'SELECT COALESCE("{column}", "unset"), COUNT(*) FROM "{table}" GROUP BY "{column}"'
    ).fetchall()
    return {str(status): int(count) for status, count in rows}


def consultation_health(database_path: Path) -> dict[str, object]:
    if not database_path.exists():
        return {"present": False, "email": {}, "hubspot": {}, "bookings": {}}
    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        return {
            "present": True,
            "email": grouped_counts(connection, "consultation_requests", "email_status"),
            "hubspot": grouped_counts(connection, "consultation_requests", "hubspot_status"),
            "bookings": grouped_counts(connection, "consultation_bookings", "status"),
        }


def provisioning_health(database_path: Path) -> dict[str, object]:
    if not database_path.exists():
        return {"present": False, "jobs": {}}
    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        return {
            "present": True,
            "jobs": grouped_counts(connection, "client_provisioning_jobs", "status"),
        }


def terminal_failures(report: dict[str, object]) -> int:
    consultations = report["consultations"]
    provisioning = report["provisioning"]
    assert isinstance(consultations, dict)
    assert isinstance(provisioning, dict)
    email = consultations.get("email") or {}
    hubspot = consultations.get("hubspot") or {}
    bookings = consultations.get("bookings") or {}
    jobs = provisioning.get("jobs") or {}
    failures = sum(
        int(counts.get(status, 0))
        for counts, statuses in (
            (email, ("failed", "not_configured")),
            (hubspot, ("failed", "not_configured")),
            (bookings, ("failed",)),
            (jobs, ("failed",)),
        )
        for status in statuses
    )
    if not consultations.get("present"):
        failures += 1
    if provisioning.get("expected") and not provisioning.get("present"):
        failures += 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("/data/audo"))
    parser.add_argument("--consultations-db", type=Path)
    parser.add_argument("--provisioning-db", type=Path)
    parser.add_argument(
        "--expect-provisioning",
        action="store_true",
        help="Treat a missing client-provisioning database as an operational failure.",
    )
    args = parser.parse_args()
    report: dict[str, object] = {
        "consultations": consultation_health(
            args.consultations_db or args.data_dir / "consultations.sqlite3"
        ),
        "provisioning": {
            **provisioning_health(
                args.provisioning_db or args.data_dir / "client-provisioning.sqlite3"
            ),
            "expected": args.expect_provisioning,
        },
    }
    failures = terminal_failures(report)
    report["terminal_failures"] = failures
    report["status"] = "attention_required" if failures else "ok"
    print(json.dumps(report, sort_keys=True))
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
