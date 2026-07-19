"""Idempotent client workspace provisioning from HubSpot Closed Won deals.

This module is intentionally independent from the public request path. It is
designed to run as a periodic reconciliation job so a CRM or provider outage
never slows down getaudo.com form submissions or bookings.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import fcntl
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DRIVE_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_text(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat(timespec="seconds")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ProvisioningConfig:
    database_path: Path
    hubspot_token: str
    hubspot_base_url: str
    hubspot_portal_id: str
    hubspot_pipeline: str
    hubspot_closed_won_stage: str
    hubspot_activation_after: str
    hubspot_allow_historical: bool
    hubspot_status_property: str
    hubspot_drive_url_property: str
    hubspot_notion_url_property: str
    hubspot_provisioned_at_property: str
    hubspot_ensure_properties: bool
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    drive_parent_folder_id: str
    drive_template_folder_id: str
    drive_folder_suffix: str
    notion_enabled: bool
    notion_token: str
    notion_database_id: str
    notion_api_version: str
    notion_title_property: str
    notion_deal_id_property: str
    notion_drive_url_property: str
    notion_hubspot_url_property: str
    notion_status_property: str
    max_attempts: int
    retry_base_seconds: int

    @classmethod
    def from_env(cls) -> "ProvisioningConfig":
        data_dir = Path(os.environ.get("DATA_DIR", "/data/audo"))
        return cls(
            database_path=Path(
                os.environ.get("CLIENT_PROVISIONING_DATABASE_PATH", data_dir / "client-provisioning.sqlite3")
            ),
            hubspot_token=os.environ.get("HUBSPOT_SERVICE_KEY", "").strip(),
            hubspot_base_url=os.environ.get("HUBSPOT_API_BASE_URL", "https://api.hubapi.com").rstrip("/"),
            hubspot_portal_id=os.environ.get("HUBSPOT_PORTAL_ID", "").strip(),
            hubspot_pipeline=os.environ.get("HUBSPOT_PIPELINE", "default").strip() or "default",
            hubspot_closed_won_stage=os.environ.get("HUBSPOT_CLOSED_WON_STAGE", "closedwon").strip() or "closedwon",
            hubspot_activation_after=os.environ.get("CLIENT_PROVISIONING_ACTIVATION_AFTER", "").strip(),
            hubspot_allow_historical=env_bool("CLIENT_PROVISIONING_ALLOW_HISTORICAL", False),
            hubspot_status_property=os.environ.get(
                "HUBSPOT_PROVISIONING_STATUS_PROPERTY", "audo_provisioning_status"
            ).strip(),
            hubspot_drive_url_property=os.environ.get(
                "HUBSPOT_DRIVE_FOLDER_URL_PROPERTY", "audo_drive_folder_url"
            ).strip(),
            hubspot_notion_url_property=os.environ.get(
                "HUBSPOT_NOTION_PROJECT_URL_PROPERTY", "audo_notion_project_url"
            ).strip(),
            hubspot_provisioned_at_property=os.environ.get(
                "HUBSPOT_PROVISIONED_AT_PROPERTY", "audo_provisioned_at"
            ).strip(),
            hubspot_ensure_properties=env_bool("HUBSPOT_ENSURE_PROVISIONING_PROPERTIES", True),
            google_client_id=os.environ.get("PROVISIONING_GOOGLE_CLIENT_ID", "").strip(),
            google_client_secret=os.environ.get("PROVISIONING_GOOGLE_CLIENT_SECRET", "").strip(),
            google_refresh_token=os.environ.get("PROVISIONING_GOOGLE_REFRESH_TOKEN", "").strip(),
            drive_parent_folder_id=os.environ.get("DRIVE_CLIENTS_PARENT_FOLDER_ID", "").strip(),
            drive_template_folder_id=os.environ.get("DRIVE_CLIENT_TEMPLATE_FOLDER_ID", "").strip(),
            drive_folder_suffix=os.environ.get("DRIVE_CLIENT_FOLDER_SUFFIX", " — Audo Client").strip(),
            notion_enabled=env_bool("NOTION_PROVISIONING_ENABLED", False),
            notion_token=os.environ.get("NOTION_API_TOKEN", "").strip(),
            notion_database_id=os.environ.get("NOTION_PROJECTS_DATABASE_ID", "").strip(),
            notion_api_version=os.environ.get("NOTION_API_VERSION", "2022-06-28").strip(),
            notion_title_property=os.environ.get("NOTION_PROJECT_TITLE_PROPERTY", "Name").strip(),
            notion_deal_id_property=os.environ.get("NOTION_HUBSPOT_DEAL_ID_PROPERTY", "HubSpot Deal ID").strip(),
            notion_drive_url_property=os.environ.get("NOTION_DRIVE_FOLDER_PROPERTY", "Client Folder").strip(),
            notion_hubspot_url_property=os.environ.get("NOTION_HUBSPOT_DEAL_URL_PROPERTY", "HubSpot Deal").strip(),
            notion_status_property=os.environ.get("NOTION_PROJECT_STATUS_PROPERTY", "Stage").strip(),
            max_attempts=max(1, int(os.environ.get("CLIENT_PROVISIONING_MAX_ATTEMPTS", "6"))),
            retry_base_seconds=max(1, int(os.environ.get("CLIENT_PROVISIONING_RETRY_BASE_SECONDS", "60"))),
        )

    def validate(self, *, dry_run: bool = False) -> None:
        missing = []
        if not self.hubspot_token:
            missing.append("HUBSPOT_SERVICE_KEY")
        if not dry_run and not self.hubspot_activation_after and not self.hubspot_allow_historical:
            missing.append("CLIENT_PROVISIONING_ACTIVATION_AFTER")
        if not dry_run and not self.google_client_id:
            missing.append("PROVISIONING_GOOGLE_CLIENT_ID")
        if not dry_run and not self.google_refresh_token:
            missing.append("PROVISIONING_GOOGLE_REFRESH_TOKEN")
        if not dry_run and not self.drive_parent_folder_id:
            missing.append("DRIVE_CLIENTS_PARENT_FOLDER_ID")
        if not dry_run and not self.drive_template_folder_id:
            missing.append("DRIVE_CLIENT_TEMPLATE_FOLDER_ID")
        if not dry_run and self.notion_enabled and not self.notion_token:
            missing.append("NOTION_API_TOKEN")
        if not dry_run and self.notion_enabled and not self.notion_database_id:
            missing.append("NOTION_PROJECTS_DATABASE_ID")
        if not dry_run and self.notion_enabled and self.notion_hubspot_url_property and not self.hubspot_portal_id:
            missing.append("HUBSPOT_PORTAL_ID")
        if missing:
            mode = "dry-run discovery" if dry_run else "provisioning"
            raise ValueError(f"Missing configuration for {mode}: {', '.join(missing)}")
        if self.hubspot_activation_after:
            try:
                datetime.fromisoformat(self.hubspot_activation_after.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("CLIENT_PROVISIONING_ACTIVATION_AFTER must be an ISO-8601 timestamp") from exc

    def activation_after_millis(self) -> str:
        if not self.hubspot_activation_after:
            return ""
        value = datetime.fromisoformat(self.hubspot_activation_after.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return str(int(value.timestamp() * 1000))


class JsonApi:
    def __init__(self, base_url: str, headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 20,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/json",
                **self.headers,
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("API is temporarily unavailable") from exc


class HubSpotClient:
    PROPERTY_DEFINITIONS = {
        "status": ("Audo provisioning status", "Current state of Audo client workspace provisioning"),
        "drive": ("Audo client folder", "Google Drive client folder created by Audo"),
        "notion": ("Audo project page", "Notion project page created by Audo"),
        "provisioned_at": ("Audo provisioned at", "UTC timestamp when client workspace provisioning completed"),
    }

    def __init__(self, config: ProvisioningConfig):
        self.config = config
        self.api = JsonApi(
            config.hubspot_base_url,
            {"Authorization": f"Bearer {config.hubspot_token}"},
        )

    def ensure_properties(self) -> None:
        definitions = (
            (self.config.hubspot_status_property, *self.PROPERTY_DEFINITIONS["status"]),
            (self.config.hubspot_drive_url_property, *self.PROPERTY_DEFINITIONS["drive"]),
            (self.config.hubspot_notion_url_property, *self.PROPERTY_DEFINITIONS["notion"]),
            (self.config.hubspot_provisioned_at_property, *self.PROPERTY_DEFINITIONS["provisioned_at"]),
        )
        for name, label, description in definitions:
            if not name:
                continue
            try:
                self.api.request(
                    "POST",
                    "/crm/v3/properties/deals",
                    payload={
                        "groupName": "dealinformation",
                        "name": name,
                        "label": label,
                        "description": description,
                        "type": "string",
                        "fieldType": "text",
                    },
                )
            except RuntimeError as exc:
                if "HTTP 409" not in str(exc):
                    raise

    def closed_won_deals(self, *, include_custom_properties: bool = True) -> list[dict[str, Any]]:
        properties = [
            "dealname",
            "pipeline",
            "dealstage",
        ]
        if include_custom_properties:
            properties.extend(
                [
                    self.config.hubspot_status_property,
                    self.config.hubspot_drive_url_property,
                    self.config.hubspot_notion_url_property,
                    self.config.hubspot_provisioned_at_property,
                ]
            )
        deals: list[dict[str, Any]] = []
        after: str | None = None
        while True:
            filters = [
                {"propertyName": "pipeline", "operator": "EQ", "value": self.config.hubspot_pipeline},
                {
                    "propertyName": "dealstage",
                    "operator": "EQ",
                    "value": self.config.hubspot_closed_won_stage,
                },
            ]
            activation_after = self.config.activation_after_millis()
            if activation_after:
                filters.append(
                    {"propertyName": "closedate", "operator": "GTE", "value": activation_after}
                )
            payload: dict[str, Any] = {
                "filterGroups": [
                    {
                        "filters": filters
                    }
                ],
                "properties": [item for item in properties if item],
                "limit": 100,
                "sorts": ["closedate"],
            }
            if after:
                payload["after"] = after
            response = self.api.request("POST", "/crm/v3/objects/deals/search", payload=payload)
            deals.extend(response.get("results") or [])
            after = str((((response.get("paging") or {}).get("next") or {}).get("after") or "")) or None
            if not after:
                return deals

    def update_provisioning(self, deal_id: str, properties: dict[str, str]) -> None:
        self.api.request(
            "PATCH",
            f"/crm/v3/objects/deals/{urllib.parse.quote(deal_id, safe='')}",
            payload={"properties": properties},
        )

    def deal_url(self, deal_id: str) -> str:
        return (
            f"https://app.hubspot.com/contacts/{urllib.parse.quote(self.config.hubspot_portal_id, safe='')}"
            f"/record/0-3/{urllib.parse.quote(deal_id, safe='')}"
        )


class GoogleTokenProvider:
    def __init__(self, config: ProvisioningConfig):
        self.config = config
        self.token = ""
        self.expires_at = 0.0

    def access_token(self) -> str:
        if self.token and self.expires_at > time.time() + 60:
            return self.token
        fields = {
            "client_id": self.config.google_client_id,
            "refresh_token": self.config.google_refresh_token,
            "grant_type": "refresh_token",
        }
        if self.config.google_client_secret:
            fields["client_secret"] = self.config.google_client_secret
        request = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=urllib.parse.urlencode(fields).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("Google authorization is temporarily unavailable") from exc
        self.token = str(payload.get("access_token") or "")
        if not self.token:
            raise RuntimeError("Google did not return an access token")
        self.expires_at = time.time() + int(payload.get("expires_in", 3600))
        return self.token


class DriveClient:
    def __init__(self, config: ProvisioningConfig):
        self.config = config
        self.tokens = GoogleTokenProvider(config)

    def _api(self) -> JsonApi:
        return JsonApi(
            "https://www.googleapis.com",
            {"Authorization": f"Bearer {self.tokens.access_token()}"},
        )

    @staticmethod
    def _escape_query(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def find_client_folder(self, deal_id: str) -> dict[str, Any] | None:
        query = (
            f"'{self._escape_query(self.config.drive_parent_folder_id)}' in parents and trashed = false and "
            f"mimeType = '{DRIVE_FOLDER_MIME_TYPE}' and "
            f"appProperties has {{ key='audoHubSpotDealId' and value='{self._escape_query(deal_id)}' }}"
        )
        response = self._api().request(
            "GET",
            "/drive/v3/files",
            query={
                "q": query,
                "fields": "files(id,name,mimeType,webViewLink,appProperties)",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            },
        )
        matches = response.get("files") or []
        return matches[0] if matches else None

    def create_client_folder(self, deal_id: str, deal_name: str) -> dict[str, Any]:
        existing = self.find_client_folder(deal_id)
        if existing:
            # A prior run may have created the root and stopped midway through
            # template copy. Child-level source tags make this safe to resume.
            self._copy_folder_contents(self.config.drive_template_folder_id, str(existing["id"]), deal_id)
            return existing
        folder_name = re.sub(r"[\x00-\x1f/]+", "-", deal_name).strip()[:180]
        if self.config.drive_folder_suffix and not folder_name.endswith(self.config.drive_folder_suffix):
            folder_name += self.config.drive_folder_suffix
        root = self._api().request(
            "POST",
            "/drive/v3/files",
            query={"supportsAllDrives": "true", "fields": "id,name,mimeType,webViewLink,appProperties"},
            payload={
                "name": folder_name,
                "mimeType": DRIVE_FOLDER_MIME_TYPE,
                "parents": [self.config.drive_parent_folder_id],
                "appProperties": {"audoHubSpotDealId": deal_id, "managedBy": "audo-client-provisioning"},
            },
        )
        self._copy_folder_contents(self.config.drive_template_folder_id, str(root["id"]), deal_id)
        return root

    def _children(self, folder_id: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token = ""
        while True:
            query = {
                "q": f"'{self._escape_query(folder_id)}' in parents and trashed = false",
                "fields": "nextPageToken,files(id,name,mimeType,appProperties)",
                "pageSize": 1000,
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            }
            if page_token:
                query["pageToken"] = page_token
            response = self._api().request("GET", "/drive/v3/files", query=query)
            items.extend(response.get("files") or [])
            page_token = str(response.get("nextPageToken") or "")
            if not page_token:
                return items

    def _copy_folder_contents(self, source_folder_id: str, destination_folder_id: str, deal_id: str) -> None:
        destination_children = self._children(destination_folder_id)
        copied_by_source = {
            str((item.get("appProperties") or {}).get("audoTemplateSourceId")): item
            for item in destination_children
            if (item.get("appProperties") or {}).get("audoTemplateSourceId")
        }
        for item in self._children(source_folder_id):
            source_id = str(item["id"])
            copied = copied_by_source.get(source_id)
            if item.get("mimeType") == DRIVE_FOLDER_MIME_TYPE:
                if copied:
                    new_folder = copied
                else:
                    new_folder = self._api().request(
                        "POST",
                        "/drive/v3/files",
                        query={"supportsAllDrives": "true", "fields": "id,appProperties"},
                        payload={
                            "name": item.get("name") or "Folder",
                            "mimeType": DRIVE_FOLDER_MIME_TYPE,
                            "parents": [destination_folder_id],
                            "appProperties": {
                                "audoTemplateSourceId": source_id,
                                "audoHubSpotDealId": deal_id,
                            },
                        },
                    )
                self._copy_folder_contents(source_id, str(new_folder["id"]), deal_id)
            elif not copied:
                self._api().request(
                    "POST",
                    f"/drive/v3/files/{urllib.parse.quote(source_id, safe='')}/copy",
                    query={"supportsAllDrives": "true", "fields": "id"},
                    payload={
                        "name": item.get("name") or "Client file",
                        "parents": [destination_folder_id],
                        "appProperties": {
                            "audoTemplateSourceId": source_id,
                            "audoHubSpotDealId": deal_id,
                        },
                    },
                )


class NotionClient:
    def __init__(self, config: ProvisioningConfig):
        self.config = config
        self.api = JsonApi(
            "https://api.notion.com",
            {
                "Authorization": f"Bearer {config.notion_token}",
                "Notion-Version": config.notion_api_version,
            },
        )

    def find_project(self, deal_id: str) -> dict[str, Any] | None:
        response = self.api.request(
            "POST",
            f"/v1/databases/{urllib.parse.quote(self.config.notion_database_id, safe='')}/query",
            payload={
                "filter": {
                    "property": self.config.notion_deal_id_property,
                    "rich_text": {"equals": deal_id},
                },
                "page_size": 1,
            },
        )
        matches = response.get("results") or []
        return matches[0] if matches else None

    def create_project(self, deal_id: str, deal_name: str, drive_url: str, hubspot_url: str) -> dict[str, Any]:
        existing = self.find_project(deal_id)
        if existing:
            return existing
        properties: dict[str, Any] = {
            self.config.notion_title_property: {"title": [{"text": {"content": deal_name[:200]}}]},
            self.config.notion_deal_id_property: {"rich_text": [{"text": {"content": deal_id}}]},
        }
        if self.config.notion_drive_url_property:
            properties[self.config.notion_drive_url_property] = {"url": drive_url}
        if self.config.notion_hubspot_url_property:
            properties[self.config.notion_hubspot_url_property] = {"url": hubspot_url}
        if self.config.notion_status_property:
            properties[self.config.notion_status_property] = {"select": {"name": "Planning"}}
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "What the client needs"}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Summarize the problem or opportunity in the client's own words."}}]},
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "What success looks like"}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "List the business results the client will recognize."}}]},
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Current next step"}}]},
            },
            {
                "object": "block",
                "type": "to_do",
                "to_do": {"checked": False, "rich_text": [{"type": "text", "text": {"content": "Assign one owner, one action, and one date."}}]},
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Decisions, risks, and updates"}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Keep the lasting project record here. Store working and final files in the linked client folder."}}]},
            },
        ]
        return self.api.request(
            "POST",
            "/v1/pages",
            payload={
                "parent": {"database_id": self.config.notion_database_id},
                "properties": properties,
                "children": children,
            },
        )


class ProvisioningStore:
    def __init__(self, path: Path):
        self.path = path

    def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS client_provisioning_jobs (
                    hubspot_deal_id TEXT PRIMARY KEY,
                    deal_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    next_attempt_at TEXT,
                    drive_folder_id TEXT,
                    drive_folder_url TEXT,
                    notion_page_id TEXT,
                    notion_page_url TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )

    @contextmanager
    def run_lock(self):
        """Prevent an embedded worker and a manual reconciliation from racing."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = Path(f"{self.path}.lock")
        with lock_path.open("a+") as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("Another client provisioning reconciliation is already running") from exc
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def get(self, deal_id: str) -> dict[str, Any] | None:
        self.init()
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM client_provisioning_jobs WHERE hubspot_deal_id = ?", (deal_id,)
            ).fetchone()
        return dict(row) if row else None

    def start(self, deal_id: str, deal_name: str) -> dict[str, Any]:
        self.init()
        now = utc_text()
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO client_provisioning_jobs (
                    hubspot_deal_id, deal_name, status, attempt_count, created_at, updated_at
                ) VALUES (?, ?, 'provisioning', 1, ?, ?)
                ON CONFLICT(hubspot_deal_id) DO UPDATE SET
                    deal_name = excluded.deal_name,
                    status = 'provisioning',
                    attempt_count = client_provisioning_jobs.attempt_count + 1,
                    next_attempt_at = NULL,
                    last_error = NULL,
                    updated_at = excluded.updated_at
                WHERE client_provisioning_jobs.status != 'completed'
                """,
                (deal_id, deal_name, now, now),
            )
        return self.get(deal_id) or {}

    def save_drive(self, deal_id: str, folder: dict[str, Any]) -> None:
        folder_id = str(folder.get("id") or "")
        folder_url = str(folder.get("webViewLink") or f"https://drive.google.com/drive/folders/{folder_id}")
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """UPDATE client_provisioning_jobs
                   SET drive_folder_id = ?, drive_folder_url = ?, updated_at = ?
                   WHERE hubspot_deal_id = ?""",
                (folder_id, folder_url, utc_text(), deal_id),
            )

    def save_notion(self, deal_id: str, page: dict[str, Any]) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """UPDATE client_provisioning_jobs
                   SET notion_page_id = ?, notion_page_url = ?, updated_at = ?
                   WHERE hubspot_deal_id = ?""",
                (str(page.get("id") or ""), str(page.get("url") or ""), utc_text(), deal_id),
            )

    def complete(self, deal_id: str) -> None:
        now = utc_text()
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """UPDATE client_provisioning_jobs
                   SET status = 'completed', next_attempt_at = NULL, last_error = NULL,
                       updated_at = ?, completed_at = ?
                   WHERE hubspot_deal_id = ?""",
                (now, now, deal_id),
            )

    def fail(self, deal_id: str, error: str, max_attempts: int, retry_base_seconds: int) -> None:
        row = self.get(deal_id) or {}
        attempts = int(row.get("attempt_count") or 1)
        terminal = attempts >= max_attempts
        delay = min(retry_base_seconds * (2 ** max(attempts - 1, 0)), 3600)
        next_attempt = None if terminal else utc_text(utc_now() + timedelta(seconds=delay))
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """UPDATE client_provisioning_jobs
                   SET status = ?, next_attempt_at = ?, last_error = ?, updated_at = ?
                   WHERE hubspot_deal_id = ?""",
                ("failed" if terminal else "retry", next_attempt, error[:2000], utc_text(), deal_id),
            )

    def retry_failed(self, deal_id: str) -> bool:
        self.init()
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                """UPDATE client_provisioning_jobs
                   SET status = 'retry', attempt_count = 0, next_attempt_at = NULL,
                       last_error = NULL, updated_at = ?
                   WHERE hubspot_deal_id = ? AND status = 'failed'""",
                (utc_text(), deal_id),
            )
        return cursor.rowcount == 1

    @staticmethod
    def due(row: dict[str, Any] | None) -> bool:
        if not row:
            return True
        if row.get("status") == "completed" or row.get("status") == "failed":
            return False
        next_attempt = row.get("next_attempt_at")
        return not next_attempt or datetime.fromisoformat(str(next_attempt)) <= utc_now()


class ClientProvisioner:
    def __init__(
        self,
        config: ProvisioningConfig,
        hubspot: HubSpotClient,
        drive: DriveClient,
        store: ProvisioningStore,
        notion: NotionClient | None = None,
    ):
        self.config = config
        self.hubspot = hubspot
        self.drive = drive
        self.store = store
        self.notion = notion

    def run_once(self, *, dry_run: bool = False) -> dict[str, Any]:
        with self.store.run_lock():
            return self._run_once(dry_run=dry_run)

    def _run_once(self, *, dry_run: bool = False) -> dict[str, Any]:
        self.config.validate(dry_run=dry_run)
        if self.config.hubspot_ensure_properties and not dry_run:
            self.hubspot.ensure_properties()
        summary: dict[str, Any] = {"discovered": 0, "planned": 0, "completed": 0, "skipped": 0, "failed": 0}
        for deal in self.hubspot.closed_won_deals(include_custom_properties=not dry_run):
            summary["discovered"] += 1
            deal_id = str(deal.get("id") or "")
            properties = deal.get("properties") or {}
            deal_name = str(properties.get("dealname") or f"HubSpot deal {deal_id}")
            if not deal_id:
                summary["skipped"] += 1
                continue
            notion_done = not self.config.notion_enabled or bool(properties.get(self.config.hubspot_notion_url_property))
            if (
                properties.get(self.config.hubspot_status_property) == "completed"
                and properties.get(self.config.hubspot_drive_url_property)
                and notion_done
            ):
                summary["skipped"] += 1
                continue
            if dry_run:
                summary["planned"] += 1
                continue
            existing = self.store.get(deal_id)
            if existing and existing.get("status") != "completed" and not self.store.due(existing):
                summary["skipped"] += 1
                continue
            try:
                job = self.store.start(deal_id, deal_name)
                drive_url = str(job.get("drive_folder_url") or properties.get(self.config.hubspot_drive_url_property) or "")
                if not drive_url:
                    folder = self.drive.create_client_folder(deal_id, deal_name)
                    self.store.save_drive(deal_id, folder)
                    job = self.store.get(deal_id) or job
                    drive_url = str(job.get("drive_folder_url") or "")

                notion_url = str(job.get("notion_page_url") or properties.get(self.config.hubspot_notion_url_property) or "")
                if self.config.notion_enabled and not notion_url:
                    if not self.notion:
                        raise RuntimeError("Notion provisioning is enabled but no Notion client is configured")
                    page = self.notion.create_project(
                        deal_id,
                        deal_name,
                        drive_url,
                        self.hubspot.deal_url(deal_id),
                    )
                    self.store.save_notion(deal_id, page)
                    job = self.store.get(deal_id) or job
                    notion_url = str(job.get("notion_page_url") or "")

                hubspot_properties = {
                    self.config.hubspot_status_property: "completed",
                    self.config.hubspot_drive_url_property: drive_url,
                    self.config.hubspot_provisioned_at_property: utc_text(),
                }
                if self.config.hubspot_notion_url_property and notion_url:
                    hubspot_properties[self.config.hubspot_notion_url_property] = notion_url
                self.hubspot.update_provisioning(deal_id, hubspot_properties)
                self.store.complete(deal_id)
                summary["completed"] += 1
            except Exception as exc:
                self.store.fail(deal_id, str(exc), self.config.max_attempts, self.config.retry_base_seconds)
                summary["failed"] += 1
        return summary


def build_provisioner(config: ProvisioningConfig) -> ClientProvisioner:
    hubspot = HubSpotClient(config)
    drive = DriveClient(config)
    notion = NotionClient(config) if config.notion_enabled else None
    return ClientProvisioner(config, hubspot, drive, ProvisioningStore(config.database_path), notion)
