#!/usr/bin/env python3
"""Create an online, checksummed backup of Audo SQLite operational data."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_backup(source: Path, destination: Path) -> None:
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as source_db:
        with sqlite3.connect(destination) as destination_db:
            source_db.backup(destination_db)
            result = destination_db.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                raise RuntimeError(f"SQLite integrity check failed for {source.name}: {result}")


def create_backup(data_dir: Path, backup_root: Path, retention: int) -> Path:
    data_dir = data_dir.resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    temporary = backup_root / f".{timestamp}.tmp"
    destination = backup_root / timestamp
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir()

    databases = sorted(
        path for path in data_dir.glob("*.sqlite3") if path.is_file() and backup_root not in path.parents
    )
    if not databases:
        raise RuntimeError(f"No SQLite databases found in {data_dir}")

    files = []
    for source in databases:
        target = temporary / source.name
        sqlite_backup(source, target)
        files.append(
            {
                "name": source.name,
                "source": str(source),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )

    manifest = {
        "format": "audo-sqlite-backup-v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": files,
    }
    (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.rename(destination)

    completed = sorted(path for path in backup_root.iterdir() if path.is_dir() and not path.name.startswith("."))
    for expired in completed[:-max(1, retention)]:
        shutil.rmtree(expired)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("/data/audo"))
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--retention", type=int, default=14)
    args = parser.parse_args()
    backup_dir = args.backup_dir or args.data_dir / "backups"
    destination = create_backup(args.data_dir, backup_dir, max(1, args.retention))
    print(json.dumps({"status": "ok", "backup": str(destination)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
