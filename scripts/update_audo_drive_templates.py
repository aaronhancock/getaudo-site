#!/usr/bin/env python3
"""Apply controlled wording corrections to existing business-owned template Docs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from setup_audo_drive import DOC_MIME, FOLDER_MIME, DriveSetup


ONBOARDING_BASE = "Confirm billing contact and approved estimate or agreement."
ONBOARDING_EXTRA = (
    "☐ Record the engagement type, billing cadence, start condition, and cancellation terms in HubSpot.\n"
    "☐ Create or match the reviewed Stripe customer and link approved billing records.\n"
    "☐ Verify the signed agreement and required deposit or first-invoice condition before activation."
)
ONBOARDING_CURRENT = f"{ONBOARDING_BASE}\n{ONBOARDING_EXTRA}"

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "Estimate and Invoice Links": [
        (
            "Wave is the source of truth for estimates, invoices, payments, and balances. "
            "Record links here; do not duplicate the accounting ledger.",
            "Stripe is the source of truth for invoices, charges, payments, refunds, and balances. "
            "Wave is the accounting ledger. Record links here; do not duplicate either system.",
        ),
        ("Wave link", "Stripe or Drive link"),
    ],
    "Project Closeout": [
        (
            "Final invoice and payment status were reviewed in Wave.",
            "Final invoice and payment status were verified in Stripe and reconciled into Wave.",
        ),
    ],
    "Change Request Log": [
        (
            "Effect on scope, timing, or price",
            "Effect on scope, timing, price, billing, and access",
        ),
        ("Decision", "Written decision, approvers, and effective date"),
    ],
    "Onboarding Checklist": [
        (ONBOARDING_BASE, ONBOARDING_CURRENT),
    ],
}

NORMALIZATIONS: dict[str, list[tuple[str, str]]] = {
    "Onboarding Checklist": [(f"{ONBOARDING_CURRENT}\n{ONBOARDING_EXTRA}", ONBOARDING_CURRENT)],
}


def descendants(drive: DriveSetup, folder_id: str) -> list[dict[str, Any]]:
    data = drive.request(
        "GET",
        "https://www.googleapis.com/drive/v3/files",
        params={
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": "files(id,name,mimeType)",
            "pageSize": 1000,
        },
    )
    result: list[dict[str, Any]] = []
    for item in data.get("files", []):
        if item["mimeType"] == FOLDER_MIME:
            result.extend(descendants(drive, item["id"]))
        elif item["mimeType"] == DOC_MIME:
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credential-file", type=Path, default=Path(".secrets/audo-drive-oauth.json"))
    parser.add_argument("--folders-file", type=Path, default=Path(".secrets/audo-drive-folders.json"))
    args = parser.parse_args()

    folder_data = json.loads(args.folders_file.read_text())
    drive = DriveSetup(args.credential_file)
    docs = {item["name"]: item for item in descendants(drive, folder_data["clientTemplateFolderId"])}
    changed: list[str] = []
    unchanged: list[str] = []
    missing: list[str] = []
    for title, replacements in REPLACEMENTS.items():
        item = docs.get(title)
        if not item:
            missing.append(title)
            continue
        document = drive.request("GET", f"https://docs.googleapis.com/v1/documents/{item['id']}")
        current_text = "".join(
            element.get("textRun", {}).get("content", "")
            for block in document.get("body", {}).get("content", [])
            for element in block.get("paragraph", {}).get("elements", [])
        )
        pending: list[tuple[str, str]] = []
        for old, new in NORMALIZATIONS.get(title, []):
            if old in current_text:
                pending.append((old, new))
                current_text = current_text.replace(old, new)
        for old, new in replacements:
            if new not in current_text and old in current_text:
                pending.append((old, new))
                current_text = current_text.replace(old, new)
        if not pending:
            unchanged.append(title)
            continue
        requests = [
            {"replaceAllText": {"containsText": {"text": old, "matchCase": True}, "replaceText": new}}
            for old, new in pending
        ]
        result = drive.request(
            "POST",
            f"https://docs.googleapis.com/v1/documents/{item['id']}:batchUpdate",
            json={"requests": requests},
        )
        occurrences = sum(
            int(reply.get("replaceAllText", {}).get("occurrencesChanged", 0))
            for reply in result.get("replies", [])
        )
        (changed if occurrences else unchanged).append(title)

    print(json.dumps({
        "status": "ok" if not missing else "attention",
        "updated": changed,
        "alreadyCurrent": unchanged,
        "missing": missing,
    }))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
