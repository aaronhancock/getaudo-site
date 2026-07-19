#!/usr/bin/env python3
"""Reconcile HubSpot Closed Won deals into Audo client workspaces."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client_provisioning import ProvisioningConfig, build_provisioner  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Read Closed Won deals and report work without writes.")
    parser.add_argument("--forever", action="store_true", help="Continue polling instead of completing one pass.")
    parser.add_argument("--poll-seconds", type=int, default=300, help="Seconds between passes with --forever.")
    parser.add_argument(
        "--retry-failed",
        metavar="DEAL_ID",
        help="Move one terminal failed deal back to the retry queue before reconciling.",
    )
    args = parser.parse_args()
    if args.dry_run and args.retry_failed:
        parser.error("--dry-run cannot be combined with --retry-failed because replay changes local state")

    config = ProvisioningConfig.from_env()
    provisioner = build_provisioner(config)
    if args.retry_failed:
        reset = provisioner.store.retry_failed(args.retry_failed)
        print(json.dumps({"status": "retry_reset", "deal_id": args.retry_failed, "reset": reset}), flush=True)
    while True:
        try:
            summary = provisioner.run_once(dry_run=args.dry_run)
            print(json.dumps({"status": "ok", "dry_run": args.dry_run, **summary}, sort_keys=True), flush=True)
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True), file=sys.stderr, flush=True)
            if not args.forever:
                raise
        if not args.forever:
            return 0
        time.sleep(max(30, args.poll_seconds))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr, flush=True)
        raise SystemExit(1)
