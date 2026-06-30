from __future__ import annotations

import html
import json
import mimetypes
import os
import re
import smtplib
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data/audo"))
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DATA_DIR / "consultations.sqlite3"))
CONSULTATION_TO = os.environ.get("CONSULTATION_TO", "matthewaaron@gmail.com")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://getaudo.com").rstrip("/")
MAX_BODY_BYTES = int(os.environ.get("MAX_FORM_BODY_BYTES", "131072"))
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_ACTION = "consultation_request"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consultation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                company_name TEXT,
                website TEXT,
                email TEXT NOT NULL,
                phone TEXT,
                service TEXT NOT NULL,
                timeline TEXT NOT NULL,
                preferred_times TEXT,
                message TEXT NOT NULL,
                source TEXT,
                user_agent TEXT,
                referrer TEXT,
                ip_address TEXT,
                recaptcha_score REAL,
                recaptcha_action TEXT,
                recaptcha_hostname TEXT,
                email_status TEXT NOT NULL DEFAULT 'pending',
                email_error TEXT,
                emailed_at TEXT
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(consultation_requests)")}
        migrations = {
            "company_name": "ALTER TABLE consultation_requests ADD COLUMN company_name TEXT",
            "website": "ALTER TABLE consultation_requests ADD COLUMN website TEXT",
            "preferred_times": "ALTER TABLE consultation_requests ADD COLUMN preferred_times TEXT",
            "recaptcha_score": "ALTER TABLE consultation_requests ADD COLUMN recaptcha_score REAL",
            "recaptcha_action": "ALTER TABLE consultation_requests ADD COLUMN recaptcha_action TEXT",
            "recaptcha_hostname": "ALTER TABLE consultation_requests ADD COLUMN recaptcha_hostname TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_consultation_requests_created_at
            ON consultation_requests(created_at)
            """
        )


def clean(value: str | None, max_length: int) -> str:
    value = (value or "").replace("\x00", "").strip()
    return value[:max_length]


def store_request(fields: dict[str, str], request_meta: dict[str, str]) -> int:
    init_db()
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO consultation_requests (
                created_at, name, company_name, website, email, phone, service,
                timeline, preferred_times, message, source, user_agent, referrer,
                ip_address, recaptcha_score, recaptcha_action, recaptcha_hostname,
                email_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                utc_now(),
                fields["name"],
                fields.get("company_name"),
                fields.get("website"),
                fields["email"],
                fields.get("phone"),
                fields["service"],
                fields["timeline"],
                fields.get("preferred_times"),
                fields["message"],
                fields.get("source"),
                request_meta.get("user_agent"),
                request_meta.get("referrer"),
                request_meta.get("ip_address"),
                fields.get("recaptcha_score"),
                fields.get("recaptcha_action"),
                fields.get("recaptcha_hostname"),
            ),
        )
        return int(cursor.lastrowid)


def mark_email_status(request_id: int, status: str, error: str | None = None) -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET email_status = ?, email_error = ?, emailed_at = ?
            WHERE id = ?
            """,
            (status, clean(error, 2000) if error else None, utc_now() if status == "sent" else None, request_id),
        )


def build_email(request_id: int, fields: dict[str, str], request_meta: dict[str, str]) -> EmailMessage:
    message = EmailMessage()
    service = fields.get("service", "Consultation")
    company = fields.get("company_name") or fields["name"]
    message["Subject"] = f"New Audo consultation: {company} - {service}"
    message["From"] = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER") or "Audo <no-reply@getaudo.com>"
    message["To"] = CONSULTATION_TO
    message["Reply-To"] = fields["email"]

    body = f"""A new Audo consultation request was stored in the database first, then emailed.

Request ID: {request_id}
Submitted: {utc_now()}

Name: {fields["name"]}
Company / project: {fields.get("company_name") or "Not provided"}
Website: {fields.get("website") or "Not provided"}
Email: {fields["email"]}
Phone: {fields.get("phone") or "Not provided"}
Urgency: {fields["timeline"]}
Consultation availability:
{fields.get("preferred_times") or "Not provided"}

Help needed: {fields["service"]}

What needs help:
{fields["message"]}

Source: {fields.get("source") or "Not provided"}
reCAPTCHA score: {fields.get("recaptcha_score") if fields.get("recaptcha_score") is not None else "Not checked"}
Referrer: {request_meta.get("referrer") or "Not provided"}
IP address: {request_meta.get("ip_address") or "Not available"}
User agent: {request_meta.get("user_agent") or "Not available"}

Database path on server:
{DATABASE_PATH}
"""
    message.set_content(body)
    return message


def send_email(request_id: int, fields: dict[str, str], request_meta: dict[str, str]) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        mark_email_status(request_id, "not_configured", "SMTP_HOST is not configured")
        print(f"consultation request {request_id} stored; email not configured", file=sys.stderr)
        return

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_secure = os.environ.get("SMTP_SECURE", "").lower()
    use_ssl = smtp_secure == "ssl" or smtp_port == 465
    use_starttls = os.environ.get("SMTP_STARTTLS", "true").lower() not in {"0", "false", "no"}

    message = build_email(request_id, fields, request_meta)
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as smtp:
                if smtp_user and smtp_pass:
                    smtp.login(smtp_user, smtp_pass)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
                if use_starttls:
                    smtp.starttls()
                if smtp_user and smtp_pass:
                    smtp.login(smtp_user, smtp_pass)
                smtp.send_message(message)
        mark_email_status(request_id, "sent")
    except Exception as exc:  # pragma: no cover - depends on live SMTP.
        mark_email_status(request_id, "failed", str(exc))
        print(f"consultation request {request_id} stored; email failed: {exc}", file=sys.stderr)


def verify_recaptcha(fields: dict[str, str], request_meta: dict[str, str]) -> dict[str, object]:
    if not RECAPTCHA_SECRET_KEY:
        return {}

    token = clean(fields.get("recaptcha_token"), 4096)
    if not token:
        raise ValueError("Please refresh the page and try the spam check again.")

    data = urlencode(
        {
            "secret": RECAPTCHA_SECRET_KEY,
            "response": token,
            "remoteip": request_meta.get("ip_address", ""),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://www.google.com/recaptcha/api/siteverify",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("success"):
        raise ValueError("The spam check failed. Please refresh the page and try again.")

    action = result.get("action")
    if action and action != RECAPTCHA_ACTION:
        raise ValueError("The spam check did not match this form. Please refresh the page and try again.")

    score = result.get("score")
    if score is not None and float(score) < RECAPTCHA_MIN_SCORE:
        raise ValueError("The spam check could not verify this request. Please try again.")

    return result


class AudoHandler(BaseHTTPRequestHandler):
    server_version = "AudoConsultationServer/1.0"

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        route_files = {
            "/": "index.html",
            "/app": "app.html",
            "/app/": "app.html",
            "/thank-you": "thank-you.html",
            "/thank-you/": "thank-you.html",
        }
        if path in route_files:
            if route_files[path] == "index.html":
                self.serve_index()
            else:
                self.serve_file(BASE_DIR / route_files[path])
            return

        self.serve_static_or_index(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/consultation":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            fields = self.read_form_fields()
            if clean(fields.get("website_url_confirm"), 255):
                self.redirect("/thank-you")
                return

            request_meta = {
                "user_agent": clean(self.headers.get("User-Agent"), 500),
                "referrer": clean(self.headers.get("Referer"), 500),
                "ip_address": self.client_address[0] if self.client_address else "",
            }
            recaptcha = verify_recaptcha(fields, request_meta)

            payload = {
                "name": clean(fields.get("name"), 120),
                "company_name": clean(fields.get("company_name"), 160),
                "website": clean(fields.get("website"), 260),
                "email": clean(fields.get("email"), 254),
                "phone": clean(fields.get("phone"), 80),
                "timeline": clean(fields.get("timeline"), 80),
                "preferred_times": clean(fields.get("preferred_times"), 1000),
                "service": clean(fields.get("service"), 120),
                "message": clean(fields.get("message"), 5000),
                "source": clean(fields.get("source"), 140),
                "recaptcha_score": recaptcha.get("score"),
                "recaptcha_action": recaptcha.get("action"),
                "recaptcha_hostname": recaptcha.get("hostname"),
            }
            self.validate_payload(payload)

            request_id = store_request(payload, request_meta)
            send_email(request_id, payload, request_meta)
            self.redirect("/thank-you")
        except ValueError as exc:
            self.render_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - defensive runtime guard.
            print(f"consultation form error: {exc}", file=sys.stderr)
            self.render_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Something went wrong saving your request. Please try again in a moment.",
            )

    def read_form_fields(self) -> dict[str, str]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("Please fill out the consultation form before submitting.")
        if content_length > MAX_BODY_BYTES:
            raise ValueError("That message is too long. Please shorten it and try again.")

        content_type = self.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            raise ValueError("Please submit the consultation form from the website.")

        raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        parsed = parse_qs(raw_body, keep_blank_values=True)
        return {key: values[-1] if values else "" for key, values in parsed.items()}

    @staticmethod
    def validate_payload(payload: dict[str, str]) -> None:
        if not payload["name"]:
            raise ValueError("Please include your name.")
        if not payload["company_name"]:
            raise ValueError("Please include your company or project name.")
        if not payload["email"] or not EMAIL_RE.match(payload["email"]):
            raise ValueError("Please include a valid email address.")
        if not payload["timeline"]:
            raise ValueError("Please choose a timing option.")
        if not payload["preferred_times"]:
            raise ValueError("Please share a few day and time options for a consultation.")
        if not payload["service"]:
            raise ValueError("Please choose the kind of help you need.")
        if not payload["message"]:
            raise ValueError("Please describe what needs help.")

    def serve_static_or_index(self, path: str) -> None:
        safe_path = Path(path.lstrip("/"))
        candidate = (BASE_DIR / safe_path).resolve()
        if not str(candidate).startswith(str(BASE_DIR)) or candidate.is_dir():
            self.serve_file(BASE_DIR / "index.html")
            return
        if candidate.exists():
            self.serve_file(candidate)
            return
        self.serve_index()

    def serve_index(self) -> None:
        data = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        data = data.replace("__RECAPTCHA_SITE_KEY__", json.dumps(RECAPTCHA_SITE_KEY))
        encoded = data.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def serve_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if "/assets/" in str(file_path):
            self.send_header("Cache-Control", "public, max-age=2592000, immutable")
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def render_error(self, status: HTTPStatus, message: str) -> None:
        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Audo consultation request</title>
  <style>
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18221d; background: #fbfbf7; }}
    main {{ min-height: 100svh; display: grid; place-items: center; padding: 32px; }}
    section {{ width: min(620px, 100%); }}
    h1 {{ margin: 0 0 14px; font-size: clamp(34px, 8vw, 58px); line-height: 1; }}
    p {{ color: #5f6b62; font-size: 18px; line-height: 1.55; }}
    a {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; border-radius: 8px; padding: 0 18px; color: #1a221c; background: #f0c66f; text-decoration: none; font-weight: 820; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>One quick fix.</h1>
      <p>{html.escape(message)}</p>
      <a href="/#consultation">Back to the form</a>
    </section>
  </main>
</body>
</html>"""
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}", file=sys.stderr)


def main() -> None:
    init_db()
    port = int(os.environ.get("PORT", "80"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AudoHandler)
    print(json.dumps({"status": "listening", "port": port, "database": str(DATABASE_PATH)}))
    server.serve_forever()


if __name__ == "__main__":
    main()
