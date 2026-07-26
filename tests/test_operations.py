import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_audo_operations.py"
SPEC = importlib.util.spec_from_file_location("check_audo_operations", SCRIPT)
operations = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(operations)


class OperationsHealthTests(unittest.TestCase):
    def test_reports_grouped_counts_without_row_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "consultations.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE consultation_requests (email_status TEXT, hubspot_status TEXT)"
                )
                connection.execute("CREATE TABLE consultation_bookings (status TEXT)")
                connection.executemany(
                    "INSERT INTO consultation_requests VALUES (?, ?)",
                    [("sent", "synced"), ("sent", "failed")],
                )
                connection.executemany(
                    "INSERT INTO consultation_bookings VALUES (?)", [("confirmed",), ("failed",)]
                )

            report = {
                "consultations": operations.consultation_health(database),
                "provisioning": {"present": False, "jobs": {}},
            }
            self.assertEqual(report["consultations"]["email"], {"sent": 2})
            self.assertEqual(report["consultations"]["hubspot"], {"failed": 1, "synced": 1})
            self.assertEqual(report["consultations"]["bookings"], {"confirmed": 1, "failed": 1})
            self.assertEqual(
                report["consultations"]["attribution"],
                {"available": False, "total": 0, "first_touch": 0, "latest_touch": 0},
            )
            self.assertEqual(operations.terminal_failures(report), 2)

    def test_reports_attribution_completeness_without_exposing_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "consultations.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    """
                    CREATE TABLE consultation_requests (
                        email_status TEXT,
                        hubspot_status TEXT,
                        first_touch_json TEXT,
                        latest_touch_json TEXT
                    )
                    """
                )
                connection.execute("CREATE TABLE consultation_bookings (status TEXT)")
                connection.executemany(
                    "INSERT INTO consultation_requests VALUES (?, ?, ?, ?)",
                    [
                        ("sent", "synced", '{"utm_source":"linkedin"}', '{"utm_source":"linkedin"}'),
                        ("sent", "synced", None, None),
                    ],
                )

            report = operations.consultation_health(database)

        self.assertEqual(
            report["attribution"],
            {"available": True, "total": 2, "first_touch": 1, "latest_touch": 1},
        )

    def test_missing_expected_databases_require_attention(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.sqlite3"
            report = {
                "consultations": operations.consultation_health(missing),
                "provisioning": {**operations.provisioning_health(missing), "expected": True},
            }
            self.assertFalse(report["consultations"]["present"])
            self.assertFalse(report["provisioning"]["present"])
            self.assertEqual(operations.terminal_failures(report), 2)


if __name__ == "__main__":
    unittest.main()
