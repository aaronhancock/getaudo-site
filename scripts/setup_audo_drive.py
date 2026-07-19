#!/usr/bin/env python3
"""Create and verify the business-owned Audo Drive and client template library."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from pathlib import Path
from typing import Any

import requests


FOLDER_MIME = "application/vnd.google-apps.folder"
DOC_MIME = "application/vnd.google-apps.document"


def markdown_to_html(source: str) -> str:
    """Render the small Markdown subset used by the controlled client templates."""
    lines = source.splitlines()
    body: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    table_lines: list[str] = []

    def inline(value: str) -> str:
        value = html.escape(value.strip())
        value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
        value = re.sub(r"`(.+?)`", r"<code>\1</code>", value)
        return value

    def flush_paragraph() -> None:
        if paragraph:
            body.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            body.append(f"</{list_type}>")
            list_type = None

    def flush_table() -> None:
        if not table_lines:
            return
        rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in table_lines]
        if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
            header, data = rows[0], rows[2:]
        else:
            header, data = [], rows
        body.append("<table style='border-collapse:collapse;width:100%'>")
        if header:
            body.append("<tr>" + "".join(
                f"<th style='border:1px solid #c9cfca;padding:6px;text-align:left;background:#eef3ef'>{inline(cell)}</th>"
                for cell in header
            ) + "</tr>")
        for row in data:
            body.append("<tr>" + "".join(
                f"<td style='border:1px solid #c9cfca;padding:6px;vertical-align:top'>{inline(cell)}</td>"
                for cell in row
            ) + "</tr>")
        body.append("</table>")
        table_lines.clear()

    for raw in lines + [""]:
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            close_list()
            table_lines.append(line)
            continue
        flush_table()
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        bullet = re.match(r"^-\s+(.+)$", line)
        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            body.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif bullet or ordered:
            flush_paragraph()
            wanted = "ul" if bullet else "ol"
            if list_type != wanted:
                close_list()
                body.append(f"<{wanted}>")
                list_type = wanted
            value = (bullet or ordered).group(1)
            checked = re.match(r"^\[([ xX])\]\s+(.+)$", value)
            if checked:
                mark = "☒" if checked.group(1).lower() == "x" else "☐"
                value = f"{mark} {checked.group(2)}"
            body.append(f"<li>{inline(value)}</li>")
        elif not line.strip():
            flush_paragraph()
            close_list()
        else:
            close_list()
            paragraph.append(line.strip())
    return (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "body{font-family:Arial,sans-serif;color:#102018;line-height:1.45}"
        "h1,h2,h3{color:#123c2f}code{background:#f2f3f1;padding:1px 3px}"
        "</style></head><body>" + "\n".join(body) + "</body></html>"
    )


class DriveSetup:
    def __init__(self, credential_file: Path):
        credential = json.loads(credential_file.read_text())
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": credential["clientId"],
                "client_secret": credential.get("clientSecret", ""),
                "refresh_token": credential["refreshToken"],
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        response.raise_for_status()
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})

    def request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        response = self.session.request(method, url, timeout=45, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def find_child(self, parent_id: str, name: str, mime_type: str) -> dict[str, Any] | None:
        safe_name = name.replace("'", "\\'")
        query = (
            f"name = '{safe_name}' and '{parent_id}' in parents and "
            f"mimeType = '{mime_type}' and trashed = false"
        )
        data = self.request(
            "GET",
            "https://www.googleapis.com/drive/v3/files",
            params={"q": query, "fields": "files(id,name,mimeType,webViewLink)", "pageSize": 10},
        )
        return data.get("files", [None])[0] if data.get("files") else None

    def ensure_folder(self, parent_id: str, name: str, role: str) -> tuple[dict[str, Any], bool]:
        existing = self.find_child(parent_id, name, FOLDER_MIME)
        if existing:
            return existing, False
        created = self.request(
            "POST",
            "https://www.googleapis.com/drive/v3/files",
            params={"fields": "id,name,mimeType,webViewLink"},
            json={
                "name": name,
                "mimeType": FOLDER_MIME,
                "parents": [parent_id],
                "appProperties": {"audoRole": role},
            },
        )
        return created, True

    def ensure_doc(self, parent_id: str, title: str, source: str) -> tuple[dict[str, Any], bool]:
        existing = self.find_child(parent_id, title, DOC_MIME)
        if existing:
            return existing, False
        boundary = "audo_client_template_boundary"
        metadata = json.dumps({
            "name": title,
            "mimeType": DOC_MIME,
            "parents": [parent_id],
            "appProperties": {"audoTemplate": "client-v1"},
        })
        content = markdown_to_html(source)
        body = (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{metadata}\r\n"
            f"--{boundary}\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n{content}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")
        created = self.request(
            "POST",
            "https://www.googleapis.com/upload/drive/v3/files",
            params={"uploadType": "multipart", "fields": "id,name,mimeType,webViewLink"},
            data=body,
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )
        return created, True

    def count_children(self, parent_id: str) -> int:
        data = self.request(
            "GET",
            "https://www.googleapis.com/drive/v3/files",
            params={
                "q": f"'{parent_id}' in parents and trashed = false",
                "fields": "files(id)",
                "pageSize": 1000,
            },
        )
        return len(data.get("files", []))

    def ensure_copy(
        self, source_id: str, parent_id: str, name: str, mime_type: str
    ) -> tuple[dict[str, Any], bool]:
        existing = self.find_child(parent_id, name, mime_type)
        if existing:
            return existing, False
        copied = self.request(
            "POST",
            f"https://www.googleapis.com/drive/v3/files/{source_id}/copy",
            params={"fields": "id,name,mimeType,webViewLink,owners(emailAddress)"},
            json={
                "name": name,
                "parents": [parent_id],
                "appProperties": {"audoRole": "finance-planner", "migratedFromPersonalDrive": "true"},
            },
        )
        return copied, True

    def ensure_binary(
        self, parent_id: str, name: str, mime_type: str, content: bytes
    ) -> tuple[dict[str, Any], bool]:
        existing = self.find_child(parent_id, name, mime_type)
        if existing:
            return existing, False
        boundary = "audo_business_asset_boundary"
        metadata = json.dumps({
            "name": name,
            "parents": [parent_id],
            "appProperties": {"audoRole": "brand-logo"},
        })
        body = (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{metadata}\r\n"
            f"--{boundary}\r\nContent-Type: {mime_type}\r\nContent-Transfer-Encoding: binary\r\n\r\n"
        ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
        created = self.request(
            "POST",
            "https://www.googleapis.com/upload/drive/v3/files",
            params={"uploadType": "multipart", "fields": "id,name,mimeType,webViewLink"},
            data=body,
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )
        return created, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credential-file", type=Path, default=Path(".secrets/audo-drive-oauth.json"))
    parser.add_argument(
        "--template-source",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "Audo Consulting Playbook" / "client-template-package",
    )
    parser.add_argument("--output", type=Path, default=Path(".secrets/audo-drive-folders.json"))
    parser.add_argument(
        "--finance-planner-source-id",
        default="11y7_kNNlBqKp3ELc2eeje2N5P0Qf6nI-f5_kMYrWNxY",
        help="Personal-Drive finance planner shared with the business account for one-time migration.",
    )
    parser.add_argument(
        "--logo",
        type=Path,
        default=Path("/Users/matth/Downloads/audo_logo_transparent.png"),
    )
    args = parser.parse_args()

    drive = DriveSetup(args.credential_file)
    root, root_created = drive.ensure_folder("root", "Audo Business", "business-root")
    folders: dict[str, dict[str, Any]] = {"businessRoot": root}
    created_folders = int(root_created)
    for key, name, role in (
        ("clients", "Clients", "clients-root"),
        ("templates", "Templates", "templates-root"),
        ("finance", "Finance", "finance-root"),
        ("operations", "Business Operations", "operations-root"),
        ("brandAssets", "Brand Assets", "brand-assets-root"),
    ):
        folder, created = drive.ensure_folder(root["id"], name, role)
        folders[key] = folder
        created_folders += int(created)
    package, created = drive.ensure_folder(
        folders["templates"]["id"], "Client Template Package", "client-template-package"
    )
    folders["clientTemplatePackage"] = package
    created_folders += int(created)

    created_docs = 0
    existing_docs = 0
    category_ids: dict[str, str] = {}
    for source in sorted(args.template_source.rglob("*.md")):
        relative = source.relative_to(args.template_source)
        parent_id = package["id"]
        if len(relative.parts) > 1:
            category = relative.parts[0]
            if category not in category_ids:
                folder, was_created = drive.ensure_folder(package["id"], category, f"template-category-{category}")
                category_ids[category] = folder["id"]
                created_folders += int(was_created)
            parent_id = category_ids[category]
        title = source.stem if source.name != "README.md" else "Client Template Package Guide"
        _, was_created = drive.ensure_doc(parent_id, title, source.read_text())
        created_docs += int(was_created)
        existing_docs += int(not was_created)

    finance_planner, finance_created = drive.ensure_copy(
        args.finance_planner_source_id,
        folders["finance"]["id"],
        "Audo Business Finance Planner",
        "application/vnd.google-apps.spreadsheet",
    )
    logo: dict[str, Any] | None = None
    logo_created = False
    if args.logo.exists():
        logo, logo_created = drive.ensure_binary(
            folders["brandAssets"]["id"],
            "Audo Logo - Transparent.png",
            "image/png",
            args.logo.read_bytes(),
        )

    output = {
        "businessOwner": "aaron@getaudo.com",
        "businessRootFolderId": root["id"],
        "businessRootFolderUrl": root.get("webViewLink", f"https://drive.google.com/drive/folders/{root['id']}"),
        "clientsFolderId": folders["clients"]["id"],
        "clientsFolderUrl": folders["clients"].get(
            "webViewLink", f"https://drive.google.com/drive/folders/{folders['clients']['id']}"
        ),
        "clientTemplateFolderId": package["id"],
        "clientTemplateFolderUrl": package.get(
            "webViewLink", f"https://drive.google.com/drive/folders/{package['id']}"
        ),
        "financeFolderId": folders["finance"]["id"],
        "operationsFolderId": folders["operations"]["id"],
        "brandAssetsFolderId": folders["brandAssets"]["id"],
        "financePlannerId": finance_planner["id"],
        "financePlannerUrl": finance_planner.get(
            "webViewLink", f"https://docs.google.com/spreadsheets/d/{finance_planner['id']}"
        ),
        "financePlannerOwner": ((finance_planner.get("owners") or [{}])[0]).get("emailAddress"),
        "logoFileId": logo.get("id") if logo else None,
        "logoFileUrl": logo.get("webViewLink") if logo else None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    os.chmod(args.output, 0o600)
    print(json.dumps({
        "status": "ok",
        "createdFolders": created_folders,
        "createdDocs": created_docs,
        "existingDocs": existing_docs,
        "financePlannerCreated": finance_created,
        "logoCreated": logo_created,
        "templateChildren": drive.count_children(package["id"]),
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
