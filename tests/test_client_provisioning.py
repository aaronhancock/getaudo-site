import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from client_provisioning import (
    ClientProvisioner,
    DriveClient,
    HubSpotClient,
    NotionClient,
    ProvisioningConfig,
    ProvisioningStore,
)


def config(path: Path, *, notion=False):
    return ProvisioningConfig(
        database_path=path,
        hubspot_token="hubspot-test",
        hubspot_base_url="https://api.hubapi.test",
        hubspot_portal_id="123456",
        hubspot_pipeline="default",
        hubspot_closed_won_stage="closedwon",
        hubspot_activation_after="2026-07-19T00:00:00Z",
        hubspot_allow_historical=False,
        hubspot_status_property="audo_provisioning_status",
        hubspot_drive_url_property="audo_drive_folder_url",
        hubspot_notion_url_property="audo_notion_project_url",
        hubspot_provisioned_at_property="audo_provisioned_at",
        hubspot_ensure_properties=False,
        google_client_id="google-test",
        google_client_secret="",
        google_refresh_token="refresh-test",
        drive_parent_folder_id="clients",
        drive_template_folder_id="template",
        drive_folder_suffix=" — Audo Client",
        notion_enabled=notion,
        notion_token="notion-test" if notion else "",
        notion_database_id="projects" if notion else "",
        notion_api_version="2022-06-28",
        notion_title_property="Name",
        notion_deal_id_property="HubSpot Deal ID",
        notion_drive_url_property="Client Folder",
        notion_hubspot_url_property="HubSpot Deal",
        notion_status_property="Status",
        max_attempts=3,
        retry_base_seconds=1,
    )


class FakeHubSpot:
    def __init__(self, deals):
        self.deals = deals
        self.updates = []
        self.ensure_count = 0
        self.fail_updates = 0

    def ensure_properties(self):
        self.ensure_count += 1

    def closed_won_deals(self, *, include_custom_properties=True):
        return self.deals

    def update_provisioning(self, deal_id, properties):
        if self.fail_updates:
            self.fail_updates -= 1
            raise RuntimeError("HubSpot update failed")
        self.updates.append((deal_id, properties))
        for deal in self.deals:
            if str(deal.get("id")) == str(deal_id):
                deal.setdefault("properties", {}).update(properties)

    @staticmethod
    def deal_url(deal_id):
        return f"https://hubspot.test/deal/{deal_id}"


class FakeDrive:
    def __init__(self):
        self.created = []

    def create_client_folder(self, deal_id, deal_name):
        self.created.append((deal_id, deal_name))
        return {"id": f"folder-{deal_id}", "webViewLink": f"https://drive.test/folder-{deal_id}"}


class FakeNotion:
    def __init__(self):
        self.created = []

    def create_project(self, deal_id, deal_name, drive_url, hubspot_url):
        self.created.append((deal_id, deal_name, drive_url, hubspot_url))
        return {"id": f"page-{deal_id}", "url": f"https://notion.test/page-{deal_id}"}


class ClientProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "provisioning.sqlite3"
        self.deal = {"id": "123", "properties": {"dealname": "Rivera Hardware"}}

    def tearDown(self):
        self.temp.cleanup()

    def provisioner(self, cfg=None, hubspot=None, drive=None, notion=None):
        cfg = cfg or config(self.path)
        return ClientProvisioner(
            cfg,
            hubspot or FakeHubSpot([self.deal]),
            drive or FakeDrive(),
            ProvisioningStore(cfg.database_path),
            notion,
        )

    def test_dry_run_discovers_work_without_creating_or_writing_state(self):
        hubspot = FakeHubSpot([self.deal])
        drive = FakeDrive()
        result = self.provisioner(hubspot=hubspot, drive=drive).run_once(dry_run=True)
        self.assertEqual(result["planned"], 1)
        self.assertEqual(drive.created, [])
        self.assertEqual(hubspot.updates, [])
        self.assertFalse(self.path.exists())

    def test_completed_deal_creates_once_and_is_idempotent(self):
        hubspot = FakeHubSpot([self.deal])
        drive = FakeDrive()
        provisioner = self.provisioner(hubspot=hubspot, drive=drive)
        first = provisioner.run_once()
        second = provisioner.run_once()
        self.assertEqual(first["completed"], 1)
        self.assertEqual(second["skipped"], 1)
        self.assertEqual(len(drive.created), 1)
        self.assertEqual(len(hubspot.updates), 1)
        self.assertEqual(hubspot.updates[0][1]["audo_provisioning_status"], "completed")

    def test_partial_failure_reuses_saved_drive_folder_on_retry(self):
        hubspot = FakeHubSpot([self.deal])
        hubspot.fail_updates = 1
        drive = FakeDrive()
        provisioner = self.provisioner(hubspot=hubspot, drive=drive)
        first = provisioner.run_once()
        self.assertEqual(first["failed"], 1)
        row = ProvisioningStore(self.path).get("123")
        self.assertEqual(row["drive_folder_id"], "folder-123")
        # Make the bounded retry due now without sleeping.
        with __import__("sqlite3").connect(self.path) as conn:
            conn.execute("UPDATE client_provisioning_jobs SET next_attempt_at = NULL WHERE hubspot_deal_id = '123'")
        second = provisioner.run_once()
        self.assertEqual(second["completed"], 1)
        self.assertEqual(len(drive.created), 1)

    def test_optional_notion_project_is_linked_back_to_hubspot(self):
        cfg = config(self.path, notion=True)
        hubspot = FakeHubSpot([self.deal])
        notion = FakeNotion()
        result = self.provisioner(cfg=cfg, hubspot=hubspot, notion=notion).run_once()
        self.assertEqual(result["completed"], 1)
        self.assertEqual(len(notion.created), 1)
        self.assertEqual(
            hubspot.updates[0][1]["audo_notion_project_url"], "https://notion.test/page-123"
        )

    def test_completed_local_job_repairs_missing_hubspot_links(self):
        hubspot = FakeHubSpot([self.deal])
        drive = FakeDrive()
        provisioner = self.provisioner(hubspot=hubspot, drive=drive)
        provisioner.run_once()
        hubspot.updates.clear()
        self.deal["properties"].pop("audo_provisioning_status", None)
        self.deal["properties"].pop("audo_drive_folder_url", None)
        result = provisioner.run_once()
        self.assertEqual(result["completed"], 1)
        self.assertEqual(len(drive.created), 1)
        self.assertEqual(hubspot.updates[0][1]["audo_drive_folder_url"], "https://drive.test/folder-123")

    def test_existing_drive_root_resumes_template_copy(self):
        drive = DriveClient(config(self.path))
        existing = {"id": "folder-123", "webViewLink": "https://drive.test/folder-123"}
        with mock.patch.object(drive, "find_client_folder", return_value=existing), mock.patch.object(
            drive, "_copy_folder_contents"
        ) as copy_contents:
            result = drive.create_client_folder("123", "Rivera Hardware")
        self.assertEqual(result, existing)
        copy_contents.assert_called_once_with("template", "folder-123", "123")

    def test_terminal_failure_requires_explicit_operator_replay(self):
        store = ProvisioningStore(self.path)
        store.start("123", "Rivera Hardware")
        store.fail("123", "bad configuration", max_attempts=1, retry_base_seconds=1)
        self.assertFalse(store.due(store.get("123")))
        self.assertTrue(store.retry_failed("123"))
        self.assertTrue(store.due(store.get("123")))

    def test_hubspot_search_is_explicitly_deal_and_closed_won_based(self):
        cfg = config(self.path)
        client = HubSpotClient(cfg)
        calls = []

        def request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            return {"results": []}

        client.api.request = request
        client.closed_won_deals()
        self.assertEqual(calls[0][1], "/crm/v3/objects/deals/search")
        filters = calls[0][2]["payload"]["filterGroups"][0]["filters"]
        self.assertIn({"propertyName": "dealstage", "operator": "EQ", "value": "closedwon"}, filters)
        self.assertIn(
            {
                "propertyName": "closedate",
                "operator": "GTE",
                "value": str(int(datetime(2026, 7, 19, tzinfo=timezone.utc).timestamp() * 1000)),
            },
            filters,
        )
        self.assertNotIn("contacts", calls[0][1])

    def test_initial_dry_run_requests_only_standard_hubspot_properties(self):
        cfg = config(self.path)
        client = HubSpotClient(cfg)
        calls = []

        def request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            return {"results": []}

        client.api.request = request
        client.closed_won_deals(include_custom_properties=False)
        self.assertEqual(
            calls[0][2]["payload"]["properties"], ["dealname", "pipeline", "dealstage"]
        )

    def test_production_requires_an_activation_cutoff_or_explicit_historical_opt_in(self):
        cfg = config(self.path)
        unsafe = ProvisioningConfig(
            **{**cfg.__dict__, "hubspot_activation_after": "", "hubspot_allow_historical": False}
        )
        with self.assertRaisesRegex(ValueError, "CLIENT_PROVISIONING_ACTIVATION_AFTER"):
            unsafe.validate()
        unsafe.validate(dry_run=True)

    def test_run_lock_rejects_overlapping_reconciliation(self):
        store = ProvisioningStore(self.path)
        with store.run_lock():
            with self.assertRaisesRegex(RuntimeError, "already running"):
                with ProvisioningStore(self.path).run_lock():
                    pass

    def test_notion_project_uses_live_audo_stage_and_has_a_useful_starting_page(self):
        cfg = config(self.path, notion=True)
        cfg = ProvisioningConfig(**{**cfg.__dict__, "notion_status_property": "Stage"})
        client = NotionClient(cfg)
        calls = []

        def request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            if path.endswith("/query"):
                return {"results": []}
            return {"id": "page-123", "url": "https://notion.test/page-123"}

        client.api.request = request
        client.create_project("123", "Rivera Hardware", "https://drive.test/123", "https://hubspot.test/123")
        payload = calls[-1][2]["payload"]
        self.assertEqual(payload["properties"]["Stage"], {"select": {"name": "Planning"}})
        self.assertGreaterEqual(len(payload["children"]), 6)
        self.assertEqual(payload["children"][0]["heading_2"]["rich_text"][0]["text"]["content"], "What the client needs")


if __name__ == "__main__":
    unittest.main()
