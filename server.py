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

from scenarios import SCENARIOS, get_scenario, scenario_cards, scenario_dict


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data/audo"))
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DATA_DIR / "consultations.sqlite3"))
CONSULTATION_TO = os.environ.get("CONSULTATION_TO", "matthewaaron@gmail.com")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://getaudo.com").rstrip("/")
SITEMAP_LASTMOD = os.environ.get("SITEMAP_LASTMOD", "2026-07-01")
MAX_BODY_BYTES = int(os.environ.get("MAX_FORM_BODY_BYTES", "131072"))
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_ACTION = "discovery_request"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("application/xml", ".xml")


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
                interest_context TEXT,
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
            "interest_context": "ALTER TABLE consultation_requests ADD COLUMN interest_context TEXT",
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
                timeline, preferred_times, message, source, interest_context,
                user_agent, referrer, ip_address, recaptcha_score, recaptcha_action, recaptcha_hostname,
                email_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
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
                fields.get("interest_context"),
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
    service = fields.get("service", "Discovery")
    company = fields.get("company_name") or fields["name"]
    message["Subject"] = f"New Audo discovery: {company} - {service}"
    message["From"] = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER") or "Audo <no-reply@getaudo.com>"
    message["To"] = CONSULTATION_TO
    message["Reply-To"] = fields["email"]

    body = f"""A new Audo discovery request was received.

Request ID: {request_id}
Submitted: {utc_now()}

Name: {fields["name"]}
Company / project: {fields.get("company_name") or "Not provided"}
Website: {fields.get("website") or "Not provided"}
Interested in: {fields.get("interest_context") or "General discovery"}
Email: {fields["email"]}
Phone: {fields.get("phone") or "Not provided"}
Urgency: {fields["timeline"]}
Discovery availability:
{fields.get("preferred_times") or "Not provided"}

Help needed: {fields["service"]}

What needs help:
{fields["message"]}
"""
    message.set_content(body)
    return message


def send_email(request_id: int, fields: dict[str, str], request_meta: dict[str, str]) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        mark_email_status(request_id, "not_configured", "SMTP_HOST is not configured")
        print(f"discovery request {request_id} stored; email not configured", file=sys.stderr)
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
        print(f"discovery request {request_id} stored; email failed: {exc}", file=sys.stderr)


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
    server_version = "AudoDiscoveryServer/1.0"

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    def do_HEAD(self) -> None:
        self.handle_get(send_body=False)

    def do_GET(self) -> None:
        self.handle_get(send_body=True)

    def handle_get(self, send_body: bool = True) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if send_body:
                self.wfile.write(b"ok")
            return

        if path == "/assets/scenarios.json":
            self.serve_scenarios_json(send_body=send_body)
            return

        if path == "/sitemap.xml":
            self.serve_sitemap(send_body=send_body)
            return

        if path in {"/scenarios", "/scenarios/"}:
            self.redirect("/#scenarios")
            return

        scenario_match = re.fullmatch(r"/scenarios/([a-z0-9-]+)/?", path)
        if scenario_match:
            scenario = get_scenario(scenario_match.group(1))
            if scenario:
                self.serve_scenario_page(scenario.slug, send_body=send_body)
                return
            self.render_error(HTTPStatus.NOT_FOUND, "That scenario page was not found.")
            return

        route_files = {
            "/": "index.html",
            "/thank-you": "thank-you.html",
            "/thank-you/": "thank-you.html",
        }
        if path in {"/app", "/app/", "/app.html"}:
            self.redirect("/")
            return

        if path in route_files:
            if route_files[path] == "index.html":
                self.serve_index(send_body=send_body)
            else:
                self.serve_file(BASE_DIR / route_files[path], send_body=send_body)
            return

        self.serve_static_or_index(path, send_body=send_body)

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
                "service": clean(fields.get("service"), 120) or "Not sure yet",
                "message": clean(fields.get("message"), 5000),
                "source": clean(fields.get("source"), 140),
                "interest_context": clean(fields.get("interest_context"), 260),
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
            print(f"discovery form error: {exc}", file=sys.stderr)
            self.render_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Something went wrong saving your request. Please try again in a moment.",
            )

    def read_form_fields(self) -> dict[str, str]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("Please fill out the discovery form before submitting.")
        if content_length > MAX_BODY_BYTES:
            raise ValueError("That message is too long. Please shorten it and try again.")

        content_type = self.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            raise ValueError("Please submit the discovery form from the website.")

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
            raise ValueError("Please share a few day and time options for discovery.")
        if not payload["message"]:
            raise ValueError("Please describe what needs help.")

    def serve_scenarios_json(self, send_body: bool = True) -> None:
        data = json.dumps(
            {
                "count": len(SCENARIOS),
                "scenarios": scenario_cards(),
            },
            separators=(",", ":"),
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def serve_sitemap(self, send_body: bool = True) -> None:
        urls = [
            ("https://getaudo.com/", "monthly", "1.0"),
            *[(scenario.canonical_url, "monthly", "0.72") for scenario in SCENARIOS],
        ]
        entries = "\n".join(
            f"""  <url>
    <loc>{html.escape(loc)}</loc>
    <lastmod>{SITEMAP_LASTMOD}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
            for loc, changefreq, priority in urls
        )
        data = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
""".encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def serve_scenario_page(self, slug: str, send_body: bool = True) -> None:
        scenario = get_scenario(slug)
        if not scenario:
            self.render_error(HTTPStatus.NOT_FOUND, "That scenario page was not found.")
            return

        data = scenario_dict(scenario)
        h = lambda value: html.escape(str(value), quote=True)
        social_image = f"{PUBLIC_BASE_URL}/assets/audo-social-card-free-discovery.jpg"
        form_context = f"Scenario: {scenario.title} ({PUBLIC_BASE_URL}{scenario.url})"
        checks_html = "\n".join(f"<li>{h(check)}</li>" for check in data["checks"])
        faqs_html = "\n".join(
            f"""<details>
          <summary>{h(faq["question"])}</summary>
          <p>{h(faq["answer"])}</p>
        </details>"""
            for faq in data["faqs"]
        )
        json_ld = json.dumps(
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "WebPage",
                        "@id": f"{PUBLIC_BASE_URL}{scenario.url}#webpage",
                        "url": f"{PUBLIC_BASE_URL}{scenario.url}",
                        "name": scenario.meta_title,
                        "description": scenario.meta_description,
                        "isPartOf": {"@id": "https://getaudo.com/#website"},
                        "about": {"@id": f"{PUBLIC_BASE_URL}{scenario.url}#service"},
                        "primaryImageOfPage": social_image,
                        "inLanguage": "en-US",
                    },
                    {
                        "@type": "Service",
                        "@id": f"{PUBLIC_BASE_URL}{scenario.url}#service",
                        "name": scenario.title,
                        "serviceType": scenario.category,
                        "description": scenario.summary,
                        "provider": {"@id": "https://getaudo.com/#business"},
                        "areaServed": {"@type": "Country", "name": "United States"},
                        "offers": {
                            "@type": "Offer",
                            "availability": "https://schema.org/InStock",
                            "url": f"{PUBLIC_BASE_URL}{scenario.url}#discovery",
                            "priceSpecification": {
                                "@type": "PriceSpecification",
                                "priceCurrency": "USD",
                                "description": "Free Discovery request before any scoped consulting work.",
                            },
                        },
                    },
                    {
                        "@type": "FAQPage",
                        "@id": f"{PUBLIC_BASE_URL}{scenario.url}#faq",
                        "mainEntity": [
                            {
                                "@type": "Question",
                                "name": faq["question"],
                                "acceptedAnswer": {
                                    "@type": "Answer",
                                    "text": faq["answer"],
                                },
                            }
                            for faq in data["faqs"]
                        ],
                    },
                    {
                        "@type": "BreadcrumbList",
                        "@id": f"{PUBLIC_BASE_URL}{scenario.url}#breadcrumb",
                        "itemListElement": [
                            {
                                "@type": "ListItem",
                                "position": 1,
                                "name": "Audo",
                                "item": "https://getaudo.com/",
                            },
                            {
                                "@type": "ListItem",
                                "position": 2,
                                "name": "Scenarios",
                                "item": "https://getaudo.com/#scenarios",
                            },
                            {
                                "@type": "ListItem",
                                "position": 3,
                                "name": scenario.title,
                                "item": f"{PUBLIC_BASE_URL}{scenario.url}",
                            },
                        ],
                    },
                    {
                        "@type": "Person",
                        "@id": "https://getaudo.com/#aaron-hancock",
                        "name": "Aaron Hancock",
                        "jobTitle": "Senior product, software, website, automation, and AI partner",
                        "url": "https://getaudo.com/",
                        "image": "https://getaudo.com/assets/founder-field-portrait.webp",
                        "knowsAbout": [
                            "Product strategy",
                            "Software engineering",
                            "AI-assisted workflows",
                            "Website operations",
                            "Business automation",
                            "Small business technology",
                        ],
                    },
                    {
                        "@type": ["ProfessionalService", "LocalBusiness"],
                        "@id": "https://getaudo.com/#business",
                        "name": "Audo",
                        "url": "https://getaudo.com/",
                        "logo": "https://getaudo.com/assets/audo-logo-white.png",
                        "image": social_image,
                        "founder": {"@id": "https://getaudo.com/#aaron-hancock"},
                        "description": "Audo provides senior technology consulting for websites, web applications, automation, AI coaching, product strategy, and ongoing support.",
                    },
                ],
            },
            separators=(",", ":"),
        )
        recaptcha_js = self.recaptcha_script()

        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{h(scenario.meta_title)}</title>
  <meta name="description" content="{h(scenario.meta_description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="author" content="Aaron Hancock">
  <meta name="theme-color" content="#101815">
  <link rel="canonical" href="{h(PUBLIC_BASE_URL + scenario.url)}">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="alternate" href="/llms.txt" type="text/plain" title="Audo AI summary">
  <meta property="og:site_name" content="Audo">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="en_US">
  <meta property="og:url" content="{h(PUBLIC_BASE_URL + scenario.url)}">
  <meta property="og:title" content="{h(scenario.title)}">
  <meta property="og:description" content="{h(scenario.summary)}">
  <meta property="og:image" content="{h(social_image)}">
  <meta property="og:image:secure_url" content="{h(social_image)}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Audo social card with Aaron Hancock and a Free Discovery call to action.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{h(scenario.title)}">
  <meta name="twitter:description" content="{h(scenario.summary)}">
  <meta name="twitter:image" content="{h(social_image)}">
  <meta name="twitter:image:alt" content="Audo social card with Aaron Hancock and a Free Discovery call to action.">
  <link rel="icon" href="/favicon.ico?v=20260630-logo-white-a">
  <link rel="icon" href="/assets/favicon.svg?v=20260630-logo-white-a" type="image/svg+xml">
  <link rel="icon" href="/assets/favicon-32.png?v=20260630-logo-white-a" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png?v=20260630-logo-white-a">
  <script type="application/ld+json">{json_ld}</script>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18221d;
      --muted: #5f6b62;
      --soft: #eef2ed;
      --paper: #fbfbf7;
      --white: #ffffff;
      --line: rgba(24, 34, 29, 0.14);
      --evergreen: #1f4739;
      --brass: #c89b4b;
      --charcoal: #101815;
      --shadow: 0 24px 70px rgba(12, 18, 15, 0.16);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    [hidden] {{ display: none !important; }}
    a {{ color: inherit; }}
    img {{ max-width: 100%; display: block; }}
    .skip-link {{
      position: fixed;
      z-index: 50;
      top: 14px;
      left: 14px;
      transform: translateY(-140%);
      border-radius: 8px;
      padding: 12px 16px;
      color: #101815;
      background: #f0c66f;
      box-shadow: 0 16px 36px rgba(0,0,0,0.2);
      text-decoration: none;
      font-weight: 820;
      transition: transform 160ms ease;
    }}
    .skip-link:focus {{ transform: translateY(0); }}
    a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, [tabindex]:focus-visible {{
      outline: 3px solid #f4dca9;
      outline-offset: 3px;
    }}
    .shell {{ width: min(1160px, calc(100% - 36px)); margin: 0 auto; }}
    .site-nav {{
      position: absolute;
      z-index: 5;
      top: 0;
      left: 0;
      width: 100%;
      padding: 22px 0;
      color: var(--white);
    }}
    .nav-inner, footer .shell {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      flex-wrap: wrap;
    }}
    .brand {{ min-height: 44px; display: inline-flex; align-items: center; text-decoration: none; }}
    .brand img {{ width: 142px; height: auto; filter: drop-shadow(0 2px 10px rgba(0,0,0,0.22)); }}
    .nav-links {{ display: flex; align-items: center; gap: 18px; font-size: 14px; font-weight: 720; }}
    .nav-links a {{ min-height: 44px; display: inline-flex; align-items: center; color: var(--white); text-decoration: none; text-shadow: 0 1px 18px rgba(0,0,0,0.46); }}
    .nav-cta {{ border: 1px solid rgba(255,255,255,0.56); border-radius: 8px; padding: 0 14px; background: rgba(255,255,255,0.12); backdrop-filter: blur(10px); }}
    .detail-hero {{
      min-height: 66svh;
      display: grid;
      align-items: center;
      position: relative;
      overflow: hidden;
      isolation: isolate;
      color: var(--white);
      background: #101815;
    }}
    .detail-hero::before {{
      content: "";
      position: absolute;
      inset: 0;
      z-index: -2;
      background: url("/assets/consulting-technology-hero.webp") center / cover no-repeat;
      transform: scale(1.01);
    }}
    .detail-hero::after {{
      content: "";
      position: absolute;
      inset: 0;
      z-index: -1;
      background:
        linear-gradient(90deg, rgba(11,16,14,0.88) 0%, rgba(11,16,14,0.68) 38%, rgba(11,16,14,0.18) 100%),
        linear-gradient(0deg, rgba(11,16,14,0.44), rgba(11,16,14,0.08) 48%, rgba(11,16,14,0.34));
    }}
    .hero-content {{ width: min(780px, 100%); padding: 118px 0 74px; }}
    .eyebrow {{
      margin: 0 0 18px;
      color: #725119;
      font-size: 13px;
      font-weight: 820;
      letter-spacing: 0.09em;
      text-transform: uppercase;
    }}
    .detail-hero .eyebrow {{
      color: #f4dca9;
    }}
    h1, h2, h3, p {{ overflow-wrap: break-word; }}
    h1 {{ margin: 0; max-width: 840px; font-size: clamp(44px, 7.4vw, 86px); line-height: 0.96; letter-spacing: 0; }}
    h2 {{ margin: 0; font-size: clamp(30px, 4vw, 48px); line-height: 1.04; letter-spacing: 0; }}
    h3 {{ margin: 0; font-size: 22px; line-height: 1.18; letter-spacing: 0; }}
    .hero-lead {{ max-width: 760px; margin: 24px 0 0; color: rgba(255,255,255,0.9); font-size: clamp(18px, 2.1vw, 23px); line-height: 1.5; }}
    .button {{
      min-height: 48px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 18px;
      color: var(--ink);
      background: var(--white);
      text-decoration: none;
      font-size: 15px;
      font-weight: 820;
      white-space: nowrap;
      transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }}
    .button:hover {{ transform: translateY(-1px); box-shadow: 0 10px 28px rgba(12,18,15,0.18); }}
    .button:disabled {{ cursor: wait; opacity: 0.74; transform: none; box-shadow: none; }}
    .button.primary {{ border-color: #f0c66f; background: #f0c66f; color: #1a221c; }}
    .hero-actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 32px; }}
    .detail-main {{ padding: clamp(52px, 7vw, 88px) 0; }}
    .detail-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(340px, 420px);
      gap: clamp(34px, 5vw, 70px);
      align-items: start;
    }}
    .detail-content {{ display: grid; gap: 38px; }}
    .story-block {{
      display: grid;
      grid-template-columns: minmax(180px, 0.38fr) minmax(0, 1fr);
      gap: clamp(18px, 4vw, 44px);
      padding-bottom: 34px;
      border-bottom: 1px solid var(--line);
    }}
    .story-block p {{ margin: 0; color: var(--muted); font-size: 18px; line-height: 1.65; }}
    .story-block h2 {{ font-size: clamp(26px, 3vw, 36px); }}
    .check-list {{
      margin: 18px 0 0;
      padding: 0;
      list-style: none;
      display: grid;
      border-top: 1px solid var(--line);
    }}
    .check-list li {{ padding: 15px 0; border-bottom: 1px solid var(--line); color: var(--muted); line-height: 1.55; }}
    .faq-list {{ display: grid; gap: 12px; }}
    details {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--white);
      overflow: hidden;
    }}
    summary {{
      min-height: 56px;
      display: flex;
      align-items: center;
      padding: 16px 18px;
      cursor: pointer;
      font-weight: 820;
      line-height: 1.35;
    }}
    details p {{ margin: 0; padding: 0 18px 18px; color: var(--muted); line-height: 1.6; }}
    .form-panel {{
      position: sticky;
      top: 22px;
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--white);
      box-shadow: var(--shadow);
    }}
    .form-panel h2 {{ font-size: 28px; }}
    .form-panel > p {{ margin: 10px 0 20px; color: var(--muted); line-height: 1.55; }}
    .consultation-form {{ display: grid; gap: 14px; }}
    .form-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; }}
    .form-field {{ display: grid; gap: 7px; }}
    .form-field.full {{ grid-column: 1 / -1; }}
    .form-field label {{ color: var(--ink); font-size: 12px; font-weight: 820; letter-spacing: 0.06em; text-transform: uppercase; }}
    .form-field input, .form-field select, .form-field textarea {{
      width: 100%;
      border: 1px solid rgba(24,34,29,0.18);
      border-radius: 8px;
      padding: 12px;
      color: var(--ink);
      background: var(--white);
      font: inherit;
      line-height: 1.35;
      outline: none;
    }}
    .form-field input:focus, .form-field select:focus, .form-field textarea:focus {{
      border-color: var(--brass);
      box-shadow: 0 0 0 3px rgba(240,198,111,0.24);
    }}
    .form-field textarea {{ min-height: 112px; resize: vertical; }}
    .consultation-form .button {{ width: 100%; border: 0; cursor: pointer; font: inherit; font-weight: 820; }}
    .form-note, .form-status {{ margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .form-status {{ min-height: 18px; }}
    .form-status.is-error {{ color: #7c2d23; }}
    .form-honey {{ position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden; }}
    footer {{ padding: 24px 0; color: rgba(255,255,255,0.72); background: #0c1210; border-top: 1px solid rgba(255,255,255,0.12); font-size: 14px; }}
    footer a {{ color: rgba(255,255,255,0.9); font-weight: 820; text-decoration: none; }}
    .footer-line {{ margin: 0; display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; text-align: center; line-height: 1.45; }}
    footer .shell {{ justify-content: center; }}
    footer strong {{ color: var(--white); }}
    .footer-preferences {{ border: 0; padding: 0; color: rgba(255,255,255,0.9); background: transparent; font: inherit; font-weight: 820; cursor: pointer; }}
    .cookie-consent {{
      position: fixed;
      z-index: 40;
      right: 18px;
      bottom: 18px;
      width: min(620px, calc(100% - 36px));
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: center;
      padding: 18px;
      color: var(--ink);
      background: rgba(251,251,247,0.98);
      border: 1px solid rgba(24,34,29,0.18);
      border-radius: 8px;
      box-shadow: 0 24px 70px rgba(12,18,15,0.22);
    }}
    .cookie-copy h2 {{ margin: 0 0 6px; font-size: 17px; line-height: 1.2; }}
    .cookie-copy p {{ margin: 0; color: var(--muted); font-size: 13px; line-height: 1.45; }}
    .cookie-actions {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
    .cookie-button {{ min-height: 42px; border: 1px solid var(--line); border-radius: 8px; padding: 0 14px; color: var(--ink); background: var(--white); font: inherit; font-size: 13px; font-weight: 820; cursor: pointer; }}
    .cookie-button.primary {{ border-color: #f0c66f; background: #f0c66f; }}
    @media (max-width: 860px) {{
      .nav-links a:not(.nav-cta) {{ display: none; }}
      .detail-hero {{ min-height: auto; }}
      .hero-content {{ padding: 104px 0 48px; }}
      h1 {{ font-size: clamp(40px, 13vw, 58px); }}
      .hero-lead {{ font-size: 17px; line-height: 1.5; }}
      .detail-layout, .story-block, .form-grid {{ grid-template-columns: 1fr; }}
      .form-panel {{ position: static; padding: 20px; box-shadow: none; }}
      .detail-main {{ padding: 48px 0 58px; }}
      .button {{ width: 100%; }}
      .cookie-consent {{ right: 14px; bottom: 14px; width: calc(100% - 28px); grid-template-columns: 1fr; }}
      .cookie-actions {{ justify-content: stretch; }}
      .cookie-button {{ flex: 1 1 150px; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      *, *::before, *::after {{ animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: 0.01ms !important; }}
      .button:hover {{ transform: none; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <nav class="site-nav" aria-label="Primary navigation">
    <div class="shell nav-inner">
      <a class="brand" href="/" aria-label="Audo home">
        <img src="/assets/audo-logo-white.png" alt="Audo">
      </a>
      <div class="nav-links">
        <a href="/#services">Services</a>
        <a href="/#why">Why Audo</a>
        <a href="/#scenarios">Scenarios</a>
        <a class="nav-cta" href="#discovery">Free Discovery</a>
      </div>
    </div>
  </nav>
  <header class="detail-hero">
    <div class="shell">
      <div class="hero-content">
        <p class="eyebrow">{h(scenario.category)}</p>
        <h1>{h(scenario.title)}.</h1>
        <p class="hero-lead">{h(scenario.summary)}</p>
        <div class="hero-actions">
          <a class="button primary" href="#discovery">Request Free Discovery</a>
          <a class="button" href="/#scenarios">Browse scenarios</a>
        </div>
      </div>
    </div>
  </header>
  <main id="main" class="detail-main" tabindex="-1">
    <div class="shell detail-layout">
      <article class="detail-content">
        <section class="story-block" aria-labelledby="problem-heading">
          <h2 id="problem-heading">The problem</h2>
          <p>{h(scenario.pain)}</p>
        </section>
        <section class="story-block" aria-labelledby="solution-heading">
          <h2 id="solution-heading">How I help</h2>
          <p>{h(scenario.solution)}</p>
        </section>
        <section class="story-block" aria-labelledby="result-heading">
          <h2 id="result-heading">Expected result</h2>
          <p>{h(scenario.result)}</p>
        </section>
        <section aria-labelledby="look-heading">
          <p class="eyebrow" id="look-heading">What I look at first</p>
          <h2>A practical review before a bigger commitment.</h2>
          <ul class="check-list">
            {checks_html}
          </ul>
        </section>
        <section id="faq" aria-labelledby="faq-heading">
          <p class="eyebrow">Common questions</p>
          <h2 id="faq-heading">Questions people ask about this kind of help.</h2>
          <div class="faq-list">
            {faqs_html}
          </div>
        </section>
      </article>
      <aside id="discovery" class="form-panel" aria-labelledby="scenario-form-heading">
        <p class="eyebrow">Free Discovery</p>
        <h2 id="scenario-form-heading">Start with this scenario.</h2>
        <p>Share what is happening in plain English. I will review the context and respond with the best next step.</p>
        <form class="consultation-form" action="/api/consultation" method="post" aria-describedby="scenario-form-status scenario-form-note" data-recaptcha-form>
          <div class="form-honey" aria-hidden="true">
            <label for="scenario_website_url_confirm">Confirm website</label>
            <input id="scenario_website_url_confirm" name="website_url_confirm" type="text" tabindex="-1" autocomplete="off">
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label for="scenario_name">Name</label>
              <input id="scenario_name" name="name" type="text" autocomplete="name" required>
            </div>
            <div class="form-field">
              <label for="scenario_company_name">Company / project</label>
              <input id="scenario_company_name" name="company_name" type="text" autocomplete="organization" required>
            </div>
            <div class="form-field">
              <label for="scenario_email">Email</label>
              <input id="scenario_email" name="email" type="email" autocomplete="email" required>
            </div>
            <div class="form-field">
              <label for="scenario_timeline">Urgency</label>
              <select id="scenario_timeline" name="timeline" required>
                <option value="">Choose one</option>
                <option>This week</option>
                <option>Next few weeks</option>
                <option>This month</option>
                <option>No rush yet</option>
              </select>
            </div>
            <div class="form-field full">
              <label for="scenario_website">Website</label>
              <input id="scenario_website" name="website" type="url" inputmode="url" autocomplete="url" placeholder="https://example.com">
            </div>
            <div class="form-field full">
              <label for="scenario_preferred_times">A few good discovery times</label>
              <textarea id="scenario_preferred_times" name="preferred_times" placeholder="Share 2-3 days and time windows that usually work for you." required></textarea>
            </div>
            <div class="form-field full">
              <label for="scenario_message">What should I know?</label>
              <textarea id="scenario_message" name="message" placeholder="A few plain-English sentences are perfect. Include any useful context I should review first." required></textarea>
            </div>
          </div>
          <input type="hidden" name="service" value="{h(scenario.title)}">
          <input type="hidden" name="source" value="getaudo.com scenario page">
          <input type="hidden" name="interest_context" value="{h(form_context)}">
          <input type="hidden" name="recaptcha_token" value="">
          <button class="button primary" type="submit">Request Free Discovery</button>
          <p id="scenario-form-status" class="form-status" role="status" aria-live="polite"></p>
          <p id="scenario-form-note" class="form-note">Your request goes directly to Aaron with this scenario attached.</p>
        </form>
      </aside>
    </div>
  </main>
  <footer>
    <div class="shell">
      <p class="footer-line"><strong>Audo</strong><span>·</span><span>Aaron Hancock</span><span>·</span><span>Senior tech partner for websites, AI, automation, apps, and product strategy</span><span>·</span><a href="#discovery">Free Discovery</a><span>·</span><button class="footer-preferences" type="button" data-cookie-preferences>Cookie preferences</button></p>
    </div>
  </footer>
  <section class="cookie-consent" role="region" aria-labelledby="cookie-title" hidden>
    <div class="cookie-copy">
      <h2 id="cookie-title">Cookie choices</h2>
      <p>Audo uses essential browser storage to remember this choice and Google reCAPTCHA to protect the discovery form. No ad tracking.</p>
    </div>
    <div class="cookie-actions">
      <button class="cookie-button primary" type="button" data-cookie-accept>Accept</button>
      <button class="cookie-button" type="button" data-cookie-necessary>Necessary only</button>
    </div>
  </section>
  {recaptcha_js}
</body>
</html>"""
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if send_body:
            self.wfile.write(encoded)

    @staticmethod
    def recaptcha_script() -> str:
        site_key = json.dumps(RECAPTCHA_SITE_KEY)
        return f"""<script>
    window.AUDO_RECAPTCHA_SITE_KEY = {site_key};

    (function () {{
      var banner = document.querySelector(".cookie-consent");
      var preferences = document.querySelector("[data-cookie-preferences]");
      var accept = document.querySelector("[data-cookie-accept]");
      var necessary = document.querySelector("[data-cookie-necessary]");
      var key = "audo_cookie_choice";

      function getChoice() {{
        try {{
          return window.localStorage.getItem(key);
        }} catch (error) {{
          return "";
        }}
      }}

      function setChoice(value) {{
        try {{
          window.localStorage.setItem(key, value);
        }} catch (error) {{
          return;
        }}
      }}

      function showBanner() {{
        if (banner) {{
          banner.hidden = false;
        }}
      }}

      function hideBanner() {{
        if (banner) {{
          banner.hidden = true;
        }}
      }}

      if (banner && !getChoice()) {{
        showBanner();
      }}

      if (preferences) {{
        preferences.addEventListener("click", showBanner);
      }}

      if (accept) {{
        accept.addEventListener("click", function () {{
          setChoice("accepted");
          hideBanner();
        }});
      }}

      if (necessary) {{
        necessary.addEventListener("click", function () {{
          setChoice("necessary");
          hideBanner();
        }});
      }}
    }}());

    (function () {{
      var forms = Array.prototype.slice.call(document.querySelectorAll("[data-recaptcha-form]"));
      var siteKey = window.AUDO_RECAPTCHA_SITE_KEY;
      if (!forms.length || !siteKey) {{
        return;
      }}

      var recaptchaPromise = null;

      function loadRecaptcha() {{
        if (window.grecaptcha && window.grecaptcha.ready) {{
          return Promise.resolve();
        }}

        if (recaptchaPromise) {{
          return recaptchaPromise;
        }}

        recaptchaPromise = new Promise(function (resolve, reject) {{
          var script = document.createElement("script");
          script.src = "https://www.google.com/recaptcha/api.js?render=" + encodeURIComponent(siteKey);
          script.async = true;
          script.defer = true;
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        }});

        return recaptchaPromise;
      }}

      forms.forEach(function (form) {{
        var button = form.querySelector("button[type='submit']");
        var status = form.querySelector(".form-status");
        var tokenInput = form.querySelector("input[name='recaptcha_token']");
        var buttonLabel = button ? button.textContent : "";

        form.addEventListener("submit", function (event) {{
          if (form.dataset.recaptchaSubmitted === "true") {{
            return;
          }}

          event.preventDefault();
          if (button) {{
            button.disabled = true;
            button.textContent = "Checking request...";
          }}
          form.setAttribute("aria-busy", "true");
          if (status) {{
            status.setAttribute("role", "status");
            status.classList.remove("is-error");
            status.textContent = "Running a quick spam check.";
          }}

          function resetForm(message) {{
            if (button) {{
              button.disabled = false;
              button.textContent = buttonLabel;
            }}
            form.removeAttribute("aria-busy");
            if (status) {{
              status.setAttribute("role", "alert");
              status.classList.add("is-error");
              status.textContent = message;
            }}
          }}

          function runCheck() {{
            if (!window.grecaptcha || !window.grecaptcha.ready) {{
              resetForm("The spam check is still loading. Please try again in a moment.");
              return;
            }}

            window.grecaptcha.ready(function () {{
              window.grecaptcha.execute(siteKey, {{ action: "discovery_request" }})
                .then(function (token) {{
                  tokenInput.value = token;
                  form.dataset.recaptchaSubmitted = "true";
                  form.submit();
                }})
                .catch(function () {{
                  resetForm("The spam check could not complete. Please try again.");
                }});
            }});
          }}

          loadRecaptcha()
            .then(runCheck)
            .catch(function () {{
              resetForm("The spam check could not load. Please try again.");
            }});
        }});
      }});
    }}());
  </script>"""

    def serve_static_or_index(self, path: str, send_body: bool = True) -> None:
        safe_path = Path(path.lstrip("/"))
        candidate = (BASE_DIR / safe_path).resolve()
        if not str(candidate).startswith(str(BASE_DIR)) or candidate.is_dir():
            self.serve_file(BASE_DIR / "index.html", send_body=send_body)
            return
        if candidate.exists():
            self.serve_file(candidate, send_body=send_body)
            return
        self.serve_index(send_body=send_body)

    def serve_index(self, send_body: bool = True) -> None:
        data = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        data = data.replace("__RECAPTCHA_SITE_KEY__", json.dumps(RECAPTCHA_SITE_KEY))
        encoded = data.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if send_body:
            self.wfile.write(encoded)

    def serve_file(self, file_path: Path, send_body: bool = True) -> None:
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
        if send_body:
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
  <title>Audo discovery request</title>
  <style>
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18221d; background: #fbfbf7; }}
    main {{ min-height: 100svh; display: grid; place-items: center; padding: 32px; }}
    section {{ width: min(620px, 100%); }}
    h1 {{ margin: 0 0 14px; font-size: clamp(34px, 8vw, 58px); line-height: 1; }}
    p {{ color: #5f6b62; font-size: 18px; line-height: 1.55; }}
    a {{ min-height: 48px; display: inline-flex; align-items: center; justify-content: center; border-radius: 8px; padding: 0 18px; color: #1a221c; background: #f0c66f; text-decoration: none; font-weight: 820; }}
    a:focus-visible {{ outline: 3px solid #f4dca9; outline-offset: 3px; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>One quick fix.</h1>
      <p>{html.escape(message)}</p>
      <a href="/#discovery">Back to the form</a>
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
