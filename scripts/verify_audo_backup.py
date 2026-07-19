#!/usr/bin/env python3
"""Verify an Audo backup and optionally restore it to a non-production directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(backup_dir: Path, restore_dir: Path | None = None) -> dict[str, object]:
    manifest_path = backup_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "audo-sqlite-backup-v1":
        raise RuntimeError("Unsupported or missing Audo backup format")
    if restore_dir:
        restore_dir.mkdir(parents=True, exist_ok=True)
        if restore_dir.resolve() == Path("/data/audo").resolve():
            raise RuntimeError("Refusing to restore directly over the production data directory")

    files = manifest.get("files") or []
    if not files:
        raise RuntimeError("Backup manifest does not contain any database files")

    verified = []
    for item in files:
        source = backup_dir / item["name"]
        if sha256(source) != item["sha256"]:
            raise RuntimeError(f"Checksum mismatch: {source.name}")
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as database:
            result = database.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                raise RuntimeError(f"SQLite integrity check failed: {source.name}")
        if restore_dir:
            shutil.copy2(source, restore_dir / source.name)
        verified.append(source.name)
    return {"status": "ok", "verified": verified, "restore_dir": str(restore_dir or "")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup_dir", type=Path)
    parser.add_argument("--restore-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.backup_dir, args.restore_dir)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
