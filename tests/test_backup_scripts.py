import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


backup = load_script("backup_audo_data.py")
verify = load_script("verify_audo_backup.py")


class BackupScriptTests(unittest.TestCase):
    def test_backup_verify_and_restore_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data = root / "data"
            data.mkdir()
            database = data / "consultations.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE checks (value TEXT)")
                connection.execute("INSERT INTO checks VALUES ('verified')")

            snapshot = backup.create_backup(data, root / "backups", retention=2)
            restore = root / "restore"
            result = verify.verify(snapshot, restore)

            self.assertEqual(result["verified"], ["consultations.sqlite3"])
            with sqlite3.connect(restore / "consultations.sqlite3") as connection:
                self.assertEqual(connection.execute("SELECT value FROM checks").fetchone()[0], "verified")

    def test_verify_rejects_an_empty_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot = Path(temp_dir)
            (snapshot / "manifest.json").write_text(
                json.dumps({"format": "audo-sqlite-backup-v1", "files": []}), encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "does not contain any database files"):
                verify.verify(snapshot)


if __name__ == "__main__":
    unittest.main()
