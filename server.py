from __future__ import annotations

import base64
import html
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import smtplib
import sqlite3
import sys
import threading
import time as time_module
import urllib.error
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from email.message import EmailMessage
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse
from zoneinfo import ZoneInfo

from site_catalog import (
    CATEGORY_ORDER,
    build_llms_full_txt,
    build_llms_txt,
    build_robots_txt,
    build_service_markdown,
    build_services_markdown,
    build_sitemap_xml,
    category_label,
    catalog_entries,
    catalog_lastmod,
    get_catalog_entry,
    grouped_catalog,
)
from services import ARCHIVED_SERVICE_REDIRECTS, SERVICES, get_service, service_cards

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:  # pragma: no cover - Pillow is installed in the deployed image.
    Image = ImageDraw = ImageFont = ImageOps = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data/audo"))
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DATA_DIR / "consultations.sqlite3"))
CONSULTATION_TO = os.environ.get("CONSULTATION_TO", "aaron@getaudo.com")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://getaudo.com").rstrip("/")
SITEMAP_LASTMOD = catalog_lastmod(BASE_DIR)
MAX_BODY_BYTES = int(os.environ.get("MAX_FORM_BODY_BYTES", "131072"))
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_ACTION = "discovery_request"
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", "G-YP5ME1JR6Q")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_GOOGLE_CALENDAR_BOOKING_URL = (
    "https://calendar.google.com/calendar/appointments/schedules/"
    "AcZssZ1Fgfoyrn4ccNy5-oTsC9BjSgQ9gIbRbjwACTqckN2P6Z6AIDs0kj5hDnYCVQ6qq27M4wwDE1MA"
)


def normalize_google_calendar_booking_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    if parsed.scheme != "https":
        return ""
    if parsed.netloc == "calendar.app.google":
        return candidate
    if parsed.netloc == "calendar.google.com" and parsed.path.startswith("/calendar/appointments/schedules/"):
        return candidate
    return ""


GOOGLE_CALENDAR_BOOKING_URL = normalize_google_calendar_booking_url(
    os.environ.get("GOOGLE_CALENDAR_BOOKING_URL", DEFAULT_GOOGLE_CALENDAR_BOOKING_URL)
)
GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary").strip() or "primary"
GOOGLE_CALENDAR_BUSY_IDS = tuple(
    dict.fromkeys(
        calendar_id.strip()
        for calendar_id in os.environ.get("GOOGLE_CALENDAR_BUSY_IDS", GOOGLE_CALENDAR_ID).split(",")
        if calendar_id.strip()
    )
) or (GOOGLE_CALENDAR_ID,)
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
GOOGLE_OAUTH_REFRESH_TOKEN = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
GMAIL_API_SEND_ENABLED = os.environ.get("GMAIL_API_SEND_ENABLED", "").lower() in {"1", "true", "yes"}
HUBSPOT_SERVICE_KEY = os.environ.get("HUBSPOT_SERVICE_KEY", "").strip()
HUBSPOT_API_BASE_URL = os.environ.get("HUBSPOT_API_BASE_URL", "https://api.hubapi.com").rstrip("/")
HUBSPOT_PIPELINE = os.environ.get("HUBSPOT_PIPELINE", "default").strip() or "default"
HUBSPOT_NEW_INQUIRY_STAGE = (
    os.environ.get("HUBSPOT_NEW_INQUIRY_STAGE", "appointmentscheduled").strip() or "appointmentscheduled"
)
HUBSPOT_DISCOVERY_SCHEDULED_STAGE = (
    os.environ.get("HUBSPOT_DISCOVERY_SCHEDULED_STAGE", "qualifiedtobuy").strip() or "qualifiedtobuy"
)
HUBSPOT_SYNC_MAX_ATTEMPTS = max(1, int(os.environ.get("HUBSPOT_SYNC_MAX_ATTEMPTS", "6")))
HUBSPOT_SYNC_RETRY_BASE_SECONDS = max(1, int(os.environ.get("HUBSPOT_SYNC_RETRY_BASE_SECONDS", "30")))
HUBSPOT_SYNC_STALE_SECONDS = max(30, int(os.environ.get("HUBSPOT_SYNC_STALE_SECONDS", "300")))
HUBSPOT_SYNC_POLL_SECONDS = max(1, int(os.environ.get("HUBSPOT_SYNC_POLL_SECONDS", "30")))
HUBSPOT_SYNC_BATCH_SIZE = max(1, min(int(os.environ.get("HUBSPOT_SYNC_BATCH_SIZE", "10")), 100))
HUBSPOT_ATTRIBUTION_PROPERTIES = {
    "first_source": "audo_first_source",
    "first_landing_url": "audo_first_landing_url",
    "first_referring_url": "audo_first_referring_url",
    "first_utm_source": "audo_first_utm_source",
    "first_utm_medium": "audo_first_utm_medium",
    "first_utm_campaign": "audo_first_utm_campaign",
    "first_utm_content": "audo_first_utm_content",
    "first_campaign_code": "audo_first_campaign_code",
    "latest_source": "audo_latest_source",
    "latest_landing_url": "audo_latest_landing_url",
    "latest_referring_url": "audo_latest_referring_url",
    "latest_utm_source": "audo_latest_utm_source",
    "latest_utm_medium": "audo_latest_utm_medium",
    "latest_utm_campaign": "audo_latest_utm_campaign",
    "latest_utm_content": "audo_latest_utm_content",
    "latest_campaign_code": "audo_latest_campaign_code",
}
EMAIL_DELIVERY_MAX_ATTEMPTS = max(1, int(os.environ.get("EMAIL_DELIVERY_MAX_ATTEMPTS", "6")))
EMAIL_DELIVERY_RETRY_BASE_SECONDS = max(1, int(os.environ.get("EMAIL_DELIVERY_RETRY_BASE_SECONDS", "30")))
EMAIL_DELIVERY_STALE_SECONDS = max(30, int(os.environ.get("EMAIL_DELIVERY_STALE_SECONDS", "300")))
EMAIL_DELIVERY_POLL_SECONDS = max(1, int(os.environ.get("EMAIL_DELIVERY_POLL_SECONDS", "30")))
EMAIL_DELIVERY_BATCH_SIZE = max(1, min(int(os.environ.get("EMAIL_DELIVERY_BATCH_SIZE", "10")), 100))
CLIENT_PROVISIONING_ENABLED = os.environ.get("CLIENT_PROVISIONING_ENABLED", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CLIENT_PROVISIONING_POLL_SECONDS = max(30, int(os.environ.get("CLIENT_PROVISIONING_POLL_SECONDS", "300")))
BOOKING_TIMEZONE = os.environ.get("BOOKING_TIMEZONE", "America/Chicago").strip() or "America/Chicago"
BOOKING_ZONE = ZoneInfo(BOOKING_TIMEZONE)
BOOKING_WINDOW_DAYS = max(1, min(int(os.environ.get("BOOKING_WINDOW_DAYS", "30")), 60))
BOOKING_MIN_NOTICE_HOURS = max(1, int(os.environ.get("BOOKING_MIN_NOTICE_HOURS", "24")))
BOOKING_DURATION_MINUTES = max(15, int(os.environ.get("BOOKING_DURATION_MINUTES", "30")))
BOOKING_BUFFER_MINUTES = max(0, int(os.environ.get("BOOKING_BUFFER_MINUTES", "15")))
BOOKING_MAX_PER_DAY = max(1, int(os.environ.get("BOOKING_MAX_PER_DAY", "4")))
BOOKING_START_HOUR = max(0, min(int(os.environ.get("BOOKING_START_HOUR", "8")), 23))
BOOKING_END_HOUR = max(1, min(int(os.environ.get("BOOKING_END_HOUR", "21")), 24))
BOOKING_TOKEN_HOURS = max(1, int(os.environ.get("BOOKING_TOKEN_HOURS", "72")))
BOOKING_INTERNAL_ATTENDEE = os.environ.get("BOOKING_INTERNAL_ATTENDEE", "matthewaaron@gmail.com").strip()
AUDIT_FIXTURES_ENABLED = os.environ.get("AUDIT_FIXTURES_ENABLED", "").lower() in {"1", "true", "yes"}
GOOGLE_TOKEN_CACHE: dict[str, object] = {"access_token": "", "expires_at": 0.0}
GOOGLE_TOKEN_LOCK = threading.Lock()
HUBSPOT_SYNC_WAKE = threading.Event()
HUBSPOT_SYNC_THREAD_LOCK = threading.Lock()
HUBSPOT_SYNC_THREAD: threading.Thread | None = None
EMAIL_DELIVERY_WAKE = threading.Event()
EMAIL_DELIVERY_THREAD_LOCK = threading.Lock()
EMAIL_DELIVERY_THREAD: threading.Thread | None = None
CLIENT_PROVISIONING_THREAD_LOCK = threading.Lock()
CLIENT_PROVISIONING_THREAD: threading.Thread | None = None
SERVICE_SOCIAL_CARD_SIZE = (1200, 630)
SERVICE_SOCIAL_CARD_CACHE_SECONDS = 60 * 60 * 24 * 7
SERVICE_SOCIAL_CARD_VERSION = os.environ.get("SERVICE_SOCIAL_CARD_VERSION", "20260701-v2")
SERVICE_SOCIAL_CARD_CACHE: dict[str, bytes] = {}
REMOVED_SERVICE_REDIRECTS = {
    **ARCHIVED_SERVICE_REDIRECTS,
    "clean-up-hosting-dns-and-domain-confusion": "/#service-list",
    "clean-up-domains-email-and-online-presence": "/#service-list",
    "create-a-client-portal-intake-flow": "/services/build-a-customer-portal-for-requests-and-files",
    "get-personal-admin-out-of-your-head": "/#service-list",
    "organize-household-information-with-ai": "/#service-list",
    "use-ai-to-plan-travel-or-events": "/#service-list",
    "build-a-knowledge-base-for-recurring-decisions": "/#service-list",
    "create-a-better-way-to-track-family-projects": "/#service-list",
    "move-scattered-notes-into-one-operating-system": "/#service-list",
}

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("application/xml", ".xml")


def load_card_font(size: int, bold: bool = False):
    if ImageFont is None:
        return None

    font_names = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    ]
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in font_paths:
        if (bold and "Bold" not in path) or (not bold and "Bold" in path):
            continue
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_width(draw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return int(bbox[2] - bbox[0])


def wrap_card_text(draw, text: str, font, max_width: int, max_lines: int | None = None) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if not current or text_width(draw, trial, font) <= max_width:
            current = trial
            continue

        lines.append(current)
        current = word

    if current:
        lines.append(current)

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last_words = lines[-1].rstrip(".,;:").split()
        while last_words and text_width(draw, f"{' '.join(last_words)}...", font) > max_width:
            last_words.pop()
        if last_words:
            lines[-1] = f"{' '.join(last_words)}..."

    return lines


def draw_wrapped_text(draw, xy: tuple[int, int], lines: list[str], font, fill, line_gap: int) -> int:
    x, y = xy
    for line in lines:
        bbox = draw.textbbox((x, y), line, font=font)
        draw.text((x, y), line, font=font, fill=fill)
        y += int(bbox[3] - bbox[1]) + line_gap
    return y


def make_service_social_card(service) -> bytes | None:
    if not all((Image, ImageDraw, ImageFont, ImageOps)):
        return None

    width, height = SERVICE_SOCIAL_CARD_SIZE
    card = Image.new("RGBA", (width, height), "#101815")

    gradient = Image.new("RGBA", (width, height))
    gradient_pixels = gradient.load()
    for x in range(width):
        t = x / max(width - 1, 1)
        r = int(14 + 14 * t)
        g = int(24 + 36 * t)
        b = int(20 + 26 * t)
        for y in range(height):
            v = int(8 * (1 - y / height))
            gradient_pixels[x, y] = (r + v, g + v, b + v, 255)
    card.alpha_composite(gradient)

    pattern = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    pattern_draw = ImageDraw.Draw(pattern)
    for x in range(-height, width, 22):
        pattern_draw.line((x, 0, x + height, height), fill=(255, 255, 255, 9), width=1)
    card.alpha_composite(pattern)

    photo_path = BASE_DIR / "assets" / "founder-field-portrait.webp"
    photo_width = 430
    if photo_path.exists():
        with Image.open(photo_path) as source:
            photo = ImageOps.fit(source.convert("RGB"), (photo_width, height), method=Image.Resampling.LANCZOS, centering=(0.52, 0.48))
            photo = photo.convert("RGBA")
            card.alpha_composite(photo, (width - photo_width, 0))

        photo_overlay = Image.new("RGBA", (photo_width, height), (0, 0, 0, 0))
        overlay_pixels = photo_overlay.load()
        for x in range(photo_width):
            t = x / max(photo_width - 1, 1)
            alpha = int(110 * (1 - t))
            for y in range(height):
                overlay_pixels[x, y] = (16, 24, 21, alpha)
        card.alpha_composite(photo_overlay, (width - photo_width, 0))

    left_overlay = Image.new("RGBA", (790, height), (16, 24, 21, 205))
    card.alpha_composite(left_overlay, (0, 0))

    draw = ImageDraw.Draw(card)
    logo_path = BASE_DIR / "assets" / "audo-logo-white.png"
    if logo_path.exists():
        with Image.open(logo_path) as logo_source:
            logo = logo_source.convert("RGBA")
            logo_width = 142
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            card.alpha_composite(logo, (64, 56))
    else:
        logo_font = load_card_font(44, bold=False)
        draw.text((64, 56), "Audo", font=logo_font, fill=(255, 255, 255, 255))

    text_left = 64
    text_max_width = 645
    category_font = load_card_font(28, bold=True)
    draw.text(
        (text_left, 156),
        service.category.upper(),
        font=category_font,
        fill=(244, 220, 169, 255),
    )

    title_size = 66
    while title_size > 46:
        title_font = load_card_font(title_size, bold=True)
        title_lines = wrap_card_text(draw, service.title, title_font, text_max_width, max_lines=4)
        if len(title_lines) <= 2 or title_size <= 50:
            break
        title_size -= 4

    title_y = 210
    title_bottom = draw_wrapped_text(
        draw,
        (text_left, title_y),
        title_lines,
        title_font,
        fill=(255, 255, 255, 255),
        line_gap=8,
    )

    button_y = 518
    summary_font_size = 28 if len(title_lines) >= 3 else 30
    summary_font = load_card_font(summary_font_size, bold=False)
    summary_y = title_bottom + 18
    summary_bbox = draw.textbbox((0, 0), "Ag", font=summary_font)
    summary_line_height = int(summary_bbox[3] - summary_bbox[1]) + 8
    available_summary_height = max(button_y - summary_y - 22, summary_line_height)
    max_summary_lines = max(1, min(3, available_summary_height // summary_line_height))
    summary_lines = wrap_card_text(draw, service.summary, summary_font, text_max_width, max_lines=max_summary_lines)
    draw_wrapped_text(
        draw,
        (text_left, summary_y),
        summary_lines,
        summary_font,
        fill=(236, 241, 235, 235),
        line_gap=8,
    )

    draw.rounded_rectangle((text_left, button_y, text_left + 270, button_y + 64), radius=9, fill=(240, 198, 111, 255))
    button_font = load_card_font(25, bold=True)
    draw.text((text_left + 32, button_y + 17), "Free Discovery", font=button_font, fill=(16, 24, 21, 255))

    url_font = load_card_font(25, bold=True)
    draw.text((text_left + 320, button_y + 19), "getaudo.com", font=url_font, fill=(244, 220, 169, 255))

    output = BytesIO()
    card.convert("RGB").save(output, format="JPEG", quality=92, optimize=True, progressive=True)
    return output.getvalue()


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
                promo_code TEXT,
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
                first_touch_json TEXT,
                latest_touch_json TEXT,
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
            "promo_code": "ALTER TABLE consultation_requests ADD COLUMN promo_code TEXT",
            "preferred_times": "ALTER TABLE consultation_requests ADD COLUMN preferred_times TEXT",
            "interest_context": "ALTER TABLE consultation_requests ADD COLUMN interest_context TEXT",
            "recaptcha_score": "ALTER TABLE consultation_requests ADD COLUMN recaptcha_score REAL",
            "recaptcha_action": "ALTER TABLE consultation_requests ADD COLUMN recaptcha_action TEXT",
            "recaptcha_hostname": "ALTER TABLE consultation_requests ADD COLUMN recaptcha_hostname TEXT",
            "first_touch_json": "ALTER TABLE consultation_requests ADD COLUMN first_touch_json TEXT",
            "latest_touch_json": "ALTER TABLE consultation_requests ADD COLUMN latest_touch_json TEXT",
            "booking_token_hash": "ALTER TABLE consultation_requests ADD COLUMN booking_token_hash TEXT",
            "booking_token_expires_at": "ALTER TABLE consultation_requests ADD COLUMN booking_token_expires_at TEXT",
            "hubspot_contact_id": "ALTER TABLE consultation_requests ADD COLUMN hubspot_contact_id TEXT",
            "hubspot_deal_id": "ALTER TABLE consultation_requests ADD COLUMN hubspot_deal_id TEXT",
            "hubspot_status": "ALTER TABLE consultation_requests ADD COLUMN hubspot_status TEXT",
            "hubspot_error": "ALTER TABLE consultation_requests ADD COLUMN hubspot_error TEXT",
            "hubspot_synced_at": "ALTER TABLE consultation_requests ADD COLUMN hubspot_synced_at TEXT",
            "hubspot_attempt_count": (
                "ALTER TABLE consultation_requests ADD COLUMN hubspot_attempt_count INTEGER NOT NULL DEFAULT 0"
            ),
            "hubspot_next_attempt_at": (
                "ALTER TABLE consultation_requests ADD COLUMN hubspot_next_attempt_at TEXT"
            ),
            "hubspot_last_attempt_at": (
                "ALTER TABLE consultation_requests ADD COLUMN hubspot_last_attempt_at TEXT"
            ),
            "email_attempt_count": (
                "ALTER TABLE consultation_requests ADD COLUMN email_attempt_count INTEGER NOT NULL DEFAULT 0"
            ),
            "email_next_attempt_at": (
                "ALTER TABLE consultation_requests ADD COLUMN email_next_attempt_at TEXT"
            ),
            "email_last_attempt_at": (
                "ALTER TABLE consultation_requests ADD COLUMN email_last_attempt_at TEXT"
            ),
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
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_consultation_requests_hubspot_queue
            ON consultation_requests(hubspot_status, hubspot_next_attempt_at, hubspot_last_attempt_at)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_consultation_requests_email_queue
            ON consultation_requests(email_status, email_next_attempt_at, email_last_attempt_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS consultation_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                start_utc TEXT NOT NULL,
                end_utc TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                pending_expires_at TEXT,
                google_event_id TEXT,
                google_event_url TEXT,
                meet_url TEXT,
                error TEXT,
                FOREIGN KEY (request_id) REFERENCES consultation_requests(id)
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_consultation_bookings_active_start
            ON consultation_bookings(start_utc)
            WHERE status IN ('pending', 'confirmed')
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_consultation_bookings_active_request
            ON consultation_bookings(request_id)
            WHERE status IN ('pending', 'confirmed')
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_consultation_bookings_status_start
            ON consultation_bookings(status, start_utc)
            """
        )


def clean(value: str | None, max_length: int) -> str:
    value = (value or "").replace("\x00", "").strip()
    return value[:max_length]


ATTRIBUTION_CAMPAIGN_KEYS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "audo_campaign",
)


def normalize_attribution_url(value: object, *, origin_only: bool = False) -> str:
    candidate = clean(str(value or ""), 2000)
    if not candidate or any(character in candidate for character in "\r\n\t"):
        return ""
    try:
        parsed = urlparse(candidate)
        port = parsed.port
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    if parsed.username or parsed.password:
        return ""
    hostname = parsed.hostname.lower()
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    default_port = (parsed.scheme == "https" and port == 443) or (
        parsed.scheme == "http" and port == 80
    )
    netloc = hostname if not port or default_port else f"{hostname}:{port}"
    path = "/" if origin_only else (parsed.path or "/")
    return clean(f"{parsed.scheme}://{netloc}{path}", 500)


def normalize_landing_url(value: object) -> str:
    normalized = normalize_attribution_url(value)
    if not normalized:
        return ""
    candidate = urlparse(normalized)
    public = urlparse(PUBLIC_BASE_URL)
    candidate_port = candidate.port or (443 if candidate.scheme == "https" else 80)
    public_port = public.port or (443 if public.scheme == "https" else 80)
    if (
        candidate.scheme != public.scheme
        or candidate.hostname != public.hostname
        or candidate_port != public_port
    ):
        return ""
    return normalized


def normalize_attribution(raw: object) -> dict[str, str]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return {}
    if not isinstance(raw, dict):
        return {}

    normalized: dict[str, str] = {}
    captured_at = clean(str(raw.get("captured_at") or ""), 40)
    if captured_at:
        try:
            parse_iso_datetime(captured_at)
        except (TypeError, ValueError):
            captured_at = ""
    if captured_at:
        normalized["captured_at"] = captured_at

    landing_url = normalize_landing_url(raw.get("landing_url"))
    if landing_url:
        normalized["landing_url"] = landing_url
    referring_url = normalize_attribution_url(raw.get("referring_url"), origin_only=True)
    if referring_url:
        normalized["referring_url"] = referring_url

    for key in ATTRIBUTION_CAMPAIGN_KEYS:
        value = clean(str(raw.get(key) or ""), 160)
        value = re.sub(r"[\x00-\x1f\x7f]+", " ", value).strip()
        if value:
            normalized[key] = value
    return normalized


def normalized_attribution_json(raw: object) -> str | None:
    normalized = normalize_attribution(raw)
    return json.dumps(normalized, separators=(",", ":"), sort_keys=True) if normalized else None


def initial_request_attribution(request_target: str, referrer: str = "") -> dict[str, str]:
    """Build a privacy-minimized first touch for direct, non-JavaScript submissions."""
    parsed_target = urlparse(request_target)
    raw: dict[str, str] = {
        "captured_at": utc_now(),
        "landing_url": f"{PUBLIC_BASE_URL}{parsed_target.path or '/'}",
    }
    query = parse_qs(parsed_target.query, keep_blank_values=False)
    for key in ATTRIBUTION_CAMPAIGN_KEYS:
        values = query.get(key) or []
        if values:
            raw[key] = values[0]

    normalized_referrer = normalize_attribution_url(referrer, origin_only=True)
    if normalized_referrer:
        public = urlparse(PUBLIC_BASE_URL)
        referring = urlparse(normalized_referrer)
        if (referring.scheme, referring.hostname, referring.port) != (
            public.scheme,
            public.hostname,
            public.port,
        ):
            raw["referring_url"] = normalized_referrer
    return normalize_attribution(raw)


def attribution_from_row(row: dict[str, object], touch: str) -> dict[str, str]:
    return normalize_attribution(row.get(f"{touch}_touch_json"))


def attribution_lines(label: str, attribution: dict[str, str]) -> list[str]:
    if not attribution:
        return [f"{label}: Direct / unavailable"]
    values = [
        f"{label} landing: {attribution.get('landing_url') or 'Unavailable'}",
        f"{label} referrer: {attribution.get('referring_url') or 'Direct / unavailable'}",
    ]
    campaign = ", ".join(
        f"{key}={attribution[key]}"
        for key in ATTRIBUTION_CAMPAIGN_KEYS
        if attribution.get(key)
    )
    if campaign:
        values.append(f"{label} campaign: {campaign}")
    return values


class GoogleCalendarError(RuntimeError):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


class BookingUnavailable(ValueError):
    pass


def utc_now_datetime() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def calendar_configured() -> bool:
    return AUDIT_FIXTURES_ENABLED or bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_REFRESH_TOKEN)


def issue_booking_token(request_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = (utc_now_datetime() + timedelta(hours=BOOKING_TOKEN_HOURS)).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET booking_token_hash = ?, booking_token_expires_at = ?
            WHERE id = ?
            """,
            (token_hash, expires_at, request_id),
        )
    return token


def get_consultation_for_booking(request_id: int, token: str) -> dict[str, object]:
    init_db()
    supplied_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, name, company_name, website, promo_code, email, phone, service, message,
                   booking_token_hash, booking_token_expires_at
            FROM consultation_requests
            WHERE id = ?
            """,
            (request_id,),
        ).fetchone()

    if not row or not row["booking_token_hash"] or not hmac.compare_digest(row["booking_token_hash"], supplied_hash):
        raise ValueError("This scheduling link is not valid. Please submit the discovery form again.")

    expires_at = row["booking_token_expires_at"]
    if not expires_at or parse_iso_datetime(expires_at) <= utc_now_datetime():
        raise ValueError("This scheduling link has expired. Please submit the discovery form again.")
    return dict(row)


def expire_stale_pending_bookings(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        UPDATE consultation_bookings
        SET status = 'failed', updated_at = ?, error = 'Booking reservation expired before confirmation'
        WHERE status = 'pending' AND pending_expires_at IS NOT NULL AND pending_expires_at <= ?
        """,
        (utc_now(), utc_now()),
    )


def get_active_booking(request_id: int) -> dict[str, object] | None:
    init_db()
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        expire_stale_pending_bookings(conn)
        row = conn.execute(
            """
            SELECT * FROM consultation_bookings
            WHERE request_id = ? AND status IN ('pending', 'confirmed')
            ORDER BY id DESC LIMIT 1
            """,
            (request_id,),
        ).fetchone()
    return dict(row) if row else None


def business_window(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time(BOOKING_START_HOUR, 0), tzinfo=BOOKING_ZONE)
    if BOOKING_END_HOUR == 24:
        end = datetime.combine(day + timedelta(days=1), time(0, 0), tzinfo=BOOKING_ZONE)
    else:
        end = datetime.combine(day, time(BOOKING_END_HOUR, 0), tzinfo=BOOKING_ZONE)
    return start, end


def candidate_slots(now: datetime | None = None) -> list[tuple[datetime, datetime]]:
    current = (now or utc_now_datetime()).astimezone(timezone.utc)
    earliest = current + timedelta(hours=BOOKING_MIN_NOTICE_HOURS)
    local_today = current.astimezone(BOOKING_ZONE).date()
    duration = timedelta(minutes=BOOKING_DURATION_MINUTES)
    cadence = timedelta(minutes=BOOKING_DURATION_MINUTES + BOOKING_BUFFER_MINUTES)
    slots: list[tuple[datetime, datetime]] = []

    for offset in range(BOOKING_WINDOW_DAYS):
        day = local_today + timedelta(days=offset)
        if day.weekday() == 6:
            continue
        cursor, day_end = business_window(day)
        while cursor + duration <= day_end:
            start_utc = cursor.astimezone(timezone.utc)
            end_utc = (cursor + duration).astimezone(timezone.utc)
            if start_utc >= earliest:
                slots.append((start_utc, end_utc))
            cursor += cadence
    return slots


def intervals_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and end_a > start_b


def google_access_token(force_refresh: bool = False) -> str:
    if not calendar_configured():
        raise GoogleCalendarError("Live scheduling is not configured yet.", status=503)

    with GOOGLE_TOKEN_LOCK:
        cached_token = str(GOOGLE_TOKEN_CACHE.get("access_token") or "")
        expires_at = float(GOOGLE_TOKEN_CACHE.get("expires_at") or 0)
        if not force_refresh and cached_token and expires_at > time_module.time() + 60:
            return cached_token

        token_fields = {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "refresh_token": GOOGLE_OAUTH_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        }
        if GOOGLE_OAUTH_CLIENT_SECRET:
            token_fields["client_secret"] = GOOGLE_OAUTH_CLIENT_SECRET
        data = urlencode(token_fields).encode("utf-8")
        request = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise GoogleCalendarError("Google Calendar authorization is temporarily unavailable.", status=503) from exc

        access_token = clean(result.get("access_token"), 4096)
        if not access_token:
            raise GoogleCalendarError("Google Calendar authorization did not return an access token.", status=503)
        GOOGLE_TOKEN_CACHE["access_token"] = access_token
        GOOGLE_TOKEN_CACHE["expires_at"] = time_module.time() + int(result.get("expires_in", 3600))
        return access_token


def google_calendar_request(
    method: str,
    endpoint: str,
    *,
    query: dict[str, object] | None = None,
    payload: dict[str, object] | None = None,
    retry_auth: bool = True,
) -> dict[str, object]:
    url = f"https://www.googleapis.com/calendar/v3{endpoint}"
    if query:
        url = f"{url}?{urlencode(query)}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {google_access_token()}",
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code == 401 and retry_auth:
            google_access_token(force_refresh=True)
            return google_calendar_request(method, endpoint, query=query, payload=payload, retry_auth=False)
        if exc.code == 409:
            raise GoogleCalendarError("That Calendar event already exists.", status=409) from exc
        if exc.code in {403, 429, 500, 502, 503, 504}:
            raise GoogleCalendarError("Google Calendar is temporarily unavailable.", status=503) from exc
        raise GoogleCalendarError("Google Calendar could not complete the request.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GoogleCalendarError("Google Calendar is temporarily unavailable.", status=503) from exc


def google_busy_periods(start_utc: datetime, end_utc: datetime) -> list[tuple[datetime, datetime]]:
    if AUDIT_FIXTURES_ENABLED:
        # A deterministic, non-delivering calendar layer for local UX audits.
        return []
    response = google_calendar_request(
        "POST",
        "/freeBusy",
        payload={
            "timeMin": start_utc.isoformat().replace("+00:00", "Z"),
            "timeMax": end_utc.isoformat().replace("+00:00", "Z"),
            "timeZone": BOOKING_TIMEZONE,
            "items": [{"id": calendar_id} for calendar_id in GOOGLE_CALENDAR_BUSY_IDS],
        },
    )
    calendars = response.get("calendars") or {}
    calendar_results = [result for result in calendars.values() if isinstance(result, dict)]
    if len(calendar_results) < len(GOOGLE_CALENDAR_BUSY_IDS) or any(
        result.get("errors") for result in calendar_results
    ):
        raise GoogleCalendarError("Google Calendar availability could not be read.", status=503)

    busy: list[tuple[datetime, datetime]] = []
    for calendar_result in calendar_results:
        for period in calendar_result.get("busy", []):
            if period.get("start") and period.get("end"):
                busy.append((parse_iso_datetime(period["start"]), parse_iso_datetime(period["end"])))
    return sorted(set(busy))


def database_booking_periods() -> tuple[list[tuple[datetime, datetime]], dict[date, int]]:
    init_db()
    periods: list[tuple[datetime, datetime]] = []
    daily_counts: dict[date, int] = {}
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        expire_stale_pending_bookings(conn)
        rows = conn.execute(
            """
            SELECT start_utc, end_utc FROM consultation_bookings
            WHERE status IN ('pending', 'confirmed')
            """
        ).fetchall()
    for row in rows:
        start = parse_iso_datetime(row["start_utc"])
        end = parse_iso_datetime(row["end_utc"])
        periods.append((start, end))
        local_day = start.astimezone(BOOKING_ZONE).date()
        daily_counts[local_day] = daily_counts.get(local_day, 0) + 1
    return periods, daily_counts


def format_clock(value: datetime) -> str:
    local = value.astimezone(BOOKING_ZONE)
    hour = local.hour % 12 or 12
    return f"{hour}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}"


def booking_json(booking: dict[str, object]) -> dict[str, object]:
    start = parse_iso_datetime(str(booking["start_utc"]))
    end = parse_iso_datetime(str(booking["end_utc"]))
    local = start.astimezone(BOOKING_ZONE)
    return {
        "status": booking.get("status"),
        "start": start.isoformat().replace("+00:00", "Z"),
        "end": end.isoformat().replace("+00:00", "Z"),
        "date_label": local.strftime("%A, %B %d, %Y").replace(" 0", " "),
        "time_label": f"{format_clock(start)}–{format_clock(end)}",
        "timezone": BOOKING_TIMEZONE,
        "timezone_label": "Central Time",
        "meet_url": booking.get("meet_url") or "",
        "event_url": booking.get("google_event_url") or "",
    }


def build_availability(now: datetime | None = None) -> list[dict[str, object]]:
    slots = candidate_slots(now)
    if not slots:
        return []

    buffer = timedelta(minutes=BOOKING_BUFFER_MINUTES)
    query_start = slots[0][0] - buffer
    query_end = slots[-1][1] + buffer
    busy = google_busy_periods(query_start, query_end)
    db_periods, daily_counts = database_booking_periods()
    busy.extend(db_periods)

    days: dict[date, dict[str, object]] = {}
    for start, end in slots:
        local_day = start.astimezone(BOOKING_ZONE).date()
        if daily_counts.get(local_day, 0) >= BOOKING_MAX_PER_DAY:
            continue
        protected_start = start - buffer
        protected_end = end + buffer
        if any(intervals_overlap(protected_start, protected_end, busy_start, busy_end) for busy_start, busy_end in busy):
            continue

        day_entry = days.setdefault(
            local_day,
            {
                "date": local_day.isoformat(),
                "weekday": start.astimezone(BOOKING_ZONE).strftime("%a"),
                "day": str(local_day.day),
                "label": start.astimezone(BOOKING_ZONE).strftime("%A, %B %d").replace(" 0", " "),
                "slots": [],
            },
        )
        day_entry["slots"].append(
            {
                "start": start.isoformat().replace("+00:00", "Z"),
                "end": end.isoformat().replace("+00:00", "Z"),
                "label": format_clock(start),
            }
        )
    return list(days.values())


def reserve_booking(request_id: int, start: datetime, end: datetime) -> tuple[dict[str, object], bool]:
    init_db()
    now = utc_now_datetime()
    local_day = start.astimezone(BOOKING_ZONE).date()
    day_start, day_end = business_window(local_day)
    day_start_utc = day_start.astimezone(timezone.utc).isoformat(timespec="seconds")
    day_end_utc = day_end.astimezone(timezone.utc).isoformat(timespec="seconds")
    created_at = now.isoformat(timespec="seconds")
    pending_expires_at = (now + timedelta(minutes=10)).isoformat(timespec="seconds")
    start_text = start.isoformat(timespec="seconds")
    end_text = end.isoformat(timespec="seconds")

    with sqlite3.connect(DATABASE_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        expire_stale_pending_bookings(conn)
        existing = conn.execute(
            """
            SELECT * FROM consultation_bookings
            WHERE request_id = ? AND status IN ('pending', 'confirmed')
            ORDER BY id DESC LIMIT 1
            """,
            (request_id,),
        ).fetchone()
        if existing:
            return dict(existing), False

        daily_count = conn.execute(
            """
            SELECT COUNT(*) FROM consultation_bookings
            WHERE status IN ('pending', 'confirmed') AND start_utc >= ? AND start_utc < ?
            """,
            (day_start_utc, day_end_utc),
        ).fetchone()[0]
        if daily_count >= BOOKING_MAX_PER_DAY:
            raise BookingUnavailable("That day just filled up. Please choose another available day.")

        try:
            cursor = conn.execute(
                """
                INSERT INTO consultation_bookings (
                    request_id, created_at, updated_at, start_utc, end_utc, status, pending_expires_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (request_id, created_at, created_at, start_text, end_text, pending_expires_at),
            )
        except sqlite3.IntegrityError as exc:
            raise BookingUnavailable("That time was just reserved. Please choose another available time.") from exc
        row = conn.execute("SELECT * FROM consultation_bookings WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row), True


def deterministic_event_id(request_id: int, start: datetime) -> str:
    fingerprint = hashlib.sha256(f"{request_id}:{start.isoformat()}".encode("utf-8")).hexdigest()
    return f"audo{fingerprint[:48]}"


def extract_meet_url(event: dict[str, object]) -> str:
    if event.get("hangoutLink"):
        return str(event["hangoutLink"])
    conference_data = event.get("conferenceData") or {}
    for entry in conference_data.get("entryPoints", []):
        if entry.get("entryPointType") == "video" and entry.get("uri"):
            return str(entry["uri"])
    return ""


def create_calendar_event(
    consultation: dict[str, object],
    start: datetime,
    end: datetime,
    event_id: str,
) -> dict[str, object]:
    if AUDIT_FIXTURES_ENABLED:
        return {
            "id": f"fixture-{event_id}",
            "htmlLink": "https://calendar.google.com/calendar/event?eid=fixture",
            "hangoutLink": "https://meet.google.com/fixture-audo-call",
        }
    description_lines = [
        f"Audo discovery request #{consultation['id']}",
        "",
        f"Name: {consultation['name']}",
        f"Email: {consultation['email']}",
        f"Phone: {consultation.get('phone') or 'Not provided'}",
        f"Business / project: {consultation.get('company_name') or 'Not provided'}",
        f"Website: {consultation.get('website') or 'Not provided'}",
        f"Promo code: {consultation.get('promo_code') or 'Not provided'}",
        f"Service: {consultation.get('service') or 'Small business technology help'}",
        "",
        "What they shared:",
        str(consultation.get("message") or "Not provided"),
    ]
    attendees = [{"email": consultation["email"], "displayName": consultation["name"]}]
    if BOOKING_INTERNAL_ATTENDEE and BOOKING_INTERNAL_ATTENDEE.lower() != str(consultation["email"]).lower():
        attendees.append({"email": BOOKING_INTERNAL_ATTENDEE, "displayName": "Matthew Aaron"})

    payload = {
        "id": event_id,
        "summary": f"Audo Discovery Call — {consultation['name']}",
        "description": "\n".join(description_lines),
        "start": {"dateTime": start.isoformat().replace("+00:00", "Z"), "timeZone": BOOKING_TIMEZONE},
        "end": {"dateTime": end.isoformat().replace("+00:00", "Z"), "timeZone": BOOKING_TIMEZONE},
        "attendees": attendees,
        "guestsCanInviteOthers": False,
        "guestsCanModify": False,
        "transparency": "opaque",
        "conferenceData": {
            "createRequest": {
                "requestId": hashlib.sha256(f"meet:{event_id}".encode("utf-8")).hexdigest()[:32],
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "extendedProperties": {
            "private": {"audoBooking": "true", "consultationRequestId": str(consultation["id"])}
        },
        "reminders": {"useDefault": True},
    }
    endpoint = f"/calendars/{quote(GOOGLE_CALENDAR_ID, safe='')}/events"
    try:
        return google_calendar_request(
            "POST",
            endpoint,
            query={"conferenceDataVersion": 1, "sendUpdates": "all"},
            payload=payload,
        )
    except GoogleCalendarError as exc:
        if exc.status != 409:
            raise
        return google_calendar_request("GET", f"{endpoint}/{quote(event_id, safe='')}")


def finalize_booking(booking_id: int, event: dict[str, object]) -> dict[str, object]:
    meet_url = extract_meet_url(event)
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            UPDATE consultation_bookings
            SET status = 'confirmed', updated_at = ?, pending_expires_at = NULL,
                google_event_id = ?, google_event_url = ?, meet_url = ?, error = NULL
            WHERE id = ?
            """,
            (
                utc_now(),
                clean(event.get("id"), 1024),
                clean(event.get("htmlLink"), 2000),
                clean(meet_url, 2000),
                booking_id,
            ),
        )
        row = conn.execute("SELECT * FROM consultation_bookings WHERE id = ?", (booking_id,)).fetchone()
    return dict(row)


def fail_booking(booking_id: int, error: str) -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_bookings
            SET status = 'failed', updated_at = ?, pending_expires_at = NULL, error = ?
            WHERE id = ? AND status = 'pending'
            """,
            (utc_now(), clean(error, 2000), booking_id),
        )


def store_request(fields: dict[str, str], request_meta: dict[str, str]) -> int:
    init_db()
    first_touch_json = normalized_attribution_json(fields.get("first_touch"))
    latest_touch_json = normalized_attribution_json(fields.get("latest_touch"))
    if AUDIT_FIXTURES_ENABLED:
        hubspot_status = "audit_fixture"
        hubspot_error = "Sync disabled by local audit fixture"
        hubspot_next_attempt_at = None
    elif HUBSPOT_SERVICE_KEY:
        hubspot_status = "queued"
        hubspot_error = None
        hubspot_next_attempt_at = utc_now()
    else:
        hubspot_status = "not_configured"
        hubspot_error = "HubSpot sync is not configured"
        hubspot_next_attempt_at = None
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO consultation_requests (
                created_at, name, company_name, website, promo_code, email, phone, service,
                timeline, preferred_times, message, source, interest_context,
                user_agent, referrer, first_touch_json, latest_touch_json,
                ip_address, recaptcha_score, recaptcha_action, recaptcha_hostname,
                email_status, hubspot_status, hubspot_error, hubspot_next_attempt_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                utc_now(),
                fields["name"],
                fields.get("company_name"),
                fields.get("website"),
                fields.get("promo_code"),
                fields["email"],
                fields.get("phone"),
                fields["service"],
                fields["timeline"],
                fields.get("preferred_times"),
                fields["message"],
                fields.get("source"),
                fields.get("interest_context"),
                request_meta.get("user_agent"),
                normalize_attribution_url(request_meta.get("referrer"), origin_only=True),
                first_touch_json,
                latest_touch_json,
                request_meta.get("ip_address"),
                fields.get("recaptcha_score"),
                fields.get("recaptcha_action"),
                fields.get("recaptcha_hostname"),
                hubspot_status,
                hubspot_error,
                hubspot_next_attempt_at,
            ),
        )
        return int(cursor.lastrowid)


def mark_email_status(request_id: int, status: str, error: str | None = None) -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET email_status = ?, email_error = ?, emailed_at = ?,
                email_next_attempt_at = CASE WHEN ? = 'sent' THEN NULL ELSE email_next_attempt_at END
            WHERE id = ?
            """,
            (
                status,
                clean(error, 2000) if error else None,
                utc_now() if status == "sent" else None,
                status,
                request_id,
            ),
        )


def email_delivery_configured() -> bool:
    return GMAIL_API_SEND_ENABLED or bool(os.environ.get("SMTP_HOST"))


def queue_email_delivery(request_id: int) -> None:
    if AUDIT_FIXTURES_ENABLED:
        mark_email_status(request_id, "audit_fixture", "Delivery disabled by local audit fixture")
        return
    if not email_delivery_configured():
        mark_email_status(request_id, "not_configured", "Email delivery is not configured")
        return
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET email_status = 'queued', email_error = NULL, email_next_attempt_at = ?
            WHERE id = ? AND email_status != 'sent'
            """,
            (utc_now(), request_id),
        )
    EMAIL_DELIVERY_WAKE.set()


def claim_next_email_delivery(request_id: int | None = None) -> dict[str, object] | None:
    init_db()
    now = utc_now_datetime()
    now_text = now.isoformat(timespec="seconds")
    stale_before = (now - timedelta(seconds=EMAIL_DELIVERY_STALE_SECONDS)).isoformat(timespec="seconds")
    request_filter = "AND id = ?" if request_id is not None else ""
    parameters: list[object] = [EMAIL_DELIVERY_MAX_ATTEMPTS, stale_before, now_text]
    if request_id is not None:
        parameters.append(request_id)
    with sqlite3.connect(DATABASE_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            f"""
            SELECT * FROM consultation_requests
            WHERE COALESCE(email_attempt_count, 0) < ?
              AND (
                email_status IN ('queued', 'retry', 'failed')
                OR (email_status = 'sending' AND (email_last_attempt_at IS NULL OR email_last_attempt_at <= ?))
              )
              AND (email_status = 'sending' OR email_next_attempt_at IS NULL OR email_next_attempt_at <= ?)
              {request_filter}
            ORDER BY created_at, id
            LIMIT 1
            """,
            parameters,
        ).fetchone()
        if not row:
            return None
        attempt_count = int(row["email_attempt_count"] or 0) + 1
        conn.execute(
            """
            UPDATE consultation_requests
            SET email_status = 'sending', email_attempt_count = ?, email_last_attempt_at = ?,
                email_next_attempt_at = NULL, email_error = NULL
            WHERE id = ?
            """,
            (attempt_count, now_text, row["id"]),
        )
        claimed = dict(row)
        claimed["email_attempt_count"] = attempt_count
        return claimed


def schedule_email_retry(request_id: int, attempt_count: int, error: str) -> None:
    terminal = attempt_count >= EMAIL_DELIVERY_MAX_ATTEMPTS
    next_attempt_at = None
    if not terminal:
        delay = min(EMAIL_DELIVERY_RETRY_BASE_SECONDS * (2 ** max(attempt_count - 1, 0)), 3600)
        next_attempt_at = (utc_now_datetime() + timedelta(seconds=delay)).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET email_status = ?, email_error = ?, email_next_attempt_at = ?
            WHERE id = ?
            """,
            ("failed" if terminal else "retry", clean(error, 2000), next_attempt_at, request_id),
        )


def mark_hubspot_status(
    request_id: int,
    status: str,
    *,
    contact_id: str | None = None,
    deal_id: str | None = None,
    error: str | None = None,
) -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET hubspot_status = ?, hubspot_contact_id = COALESCE(?, hubspot_contact_id),
                hubspot_deal_id = COALESCE(?, hubspot_deal_id), hubspot_error = ?,
                hubspot_synced_at = ?,
                hubspot_next_attempt_at = CASE WHEN ? = 'synced' THEN NULL ELSE hubspot_next_attempt_at END
            WHERE id = ?
            """,
            (
                status,
                clean(contact_id, 255) if contact_id else None,
                clean(deal_id, 255) if deal_id else None,
                clean(error, 2000) if error else None,
                utc_now() if status == "synced" else None,
                status,
                request_id,
            ),
        )


def queue_hubspot_sync(request_id: int, *, force: bool = False) -> None:
    """Persist a HubSpot job without making a network request."""
    if AUDIT_FIXTURES_ENABLED:
        mark_hubspot_status(request_id, "audit_fixture", error="Sync disabled by local audit fixture")
        return
    if not HUBSPOT_SERVICE_KEY:
        mark_hubspot_status(request_id, "not_configured", error="HubSpot sync is not configured")
        return

    now = utc_now()
    with sqlite3.connect(DATABASE_PATH) as conn:
        if force:
            conn.execute(
                """
                UPDATE consultation_requests
                SET hubspot_status = 'queued', hubspot_error = NULL, hubspot_next_attempt_at = ?,
                    hubspot_attempt_count = 0
                WHERE id = ?
                """,
                (now, request_id),
            )
        else:
            conn.execute(
            """
            UPDATE consultation_requests
            SET hubspot_status = 'queued', hubspot_error = NULL, hubspot_next_attempt_at = ?
            WHERE id = ?
              AND COALESCE(hubspot_status, '') NOT IN ('synced', 'syncing', 'queued', 'retry')
              AND COALESCE(hubspot_attempt_count, 0) < ?
            """,
            (now, request_id, HUBSPOT_SYNC_MAX_ATTEMPTS),
            )
    HUBSPOT_SYNC_WAKE.set()


def claim_next_hubspot_sync(request_id: int | None = None) -> dict[str, object] | None:
    """Atomically claim one due, failed, or stale HubSpot job."""
    init_db()
    now = utc_now_datetime()
    now_text = now.isoformat(timespec="seconds")
    stale_before = (now - timedelta(seconds=HUBSPOT_SYNC_STALE_SECONDS)).isoformat(timespec="seconds")
    request_filter = "AND id = ?" if request_id is not None else ""
    parameters: list[object] = [
        HUBSPOT_SYNC_MAX_ATTEMPTS,
        stale_before,
        now_text,
    ]
    if request_id is not None:
        parameters.append(request_id)

    with sqlite3.connect(DATABASE_PATH, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            f"""
            SELECT *
            FROM consultation_requests
            WHERE COALESCE(hubspot_attempt_count, 0) < ?
              AND (
                hubspot_status IN ('queued', 'retry', 'failed')
                OR (
                  hubspot_status = 'syncing'
                  AND (hubspot_last_attempt_at IS NULL OR hubspot_last_attempt_at <= ?)
                )
              )
              AND (
                hubspot_status = 'syncing'
                OR hubspot_next_attempt_at IS NULL
                OR hubspot_next_attempt_at <= ?
              )
              {request_filter}
            ORDER BY created_at, id
            LIMIT 1
            """,
            parameters,
        ).fetchone()
        if not row:
            return None

        attempt_count = int(row["hubspot_attempt_count"] or 0) + 1
        conn.execute(
            """
            UPDATE consultation_requests
            SET hubspot_status = 'syncing', hubspot_attempt_count = ?,
                hubspot_last_attempt_at = ?, hubspot_next_attempt_at = NULL,
                hubspot_error = NULL
            WHERE id = ?
            """,
            (attempt_count, now_text, row["id"]),
        )
        claimed = dict(row)
        claimed["hubspot_attempt_count"] = attempt_count
        return claimed


def save_hubspot_ids(request_id: int, *, contact_id: str | None = None, deal_id: str | None = None) -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET hubspot_contact_id = COALESCE(?, hubspot_contact_id),
                hubspot_deal_id = COALESCE(?, hubspot_deal_id)
            WHERE id = ?
            """,
            (
                clean(contact_id, 255) if contact_id else None,
                clean(deal_id, 255) if deal_id else None,
                request_id,
            ),
        )


def schedule_hubspot_retry(request_id: int, attempt_count: int, error: str) -> None:
    terminal = attempt_count >= HUBSPOT_SYNC_MAX_ATTEMPTS
    next_attempt_at = None
    if not terminal:
        delay = min(HUBSPOT_SYNC_RETRY_BASE_SECONDS * (2 ** max(attempt_count - 1, 0)), 3600)
        next_attempt_at = (utc_now_datetime() + timedelta(seconds=delay)).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            UPDATE consultation_requests
            SET hubspot_status = ?, hubspot_error = ?, hubspot_next_attempt_at = ?
            WHERE id = ?
            """,
            ("failed" if terminal else "retry", clean(error, 2000), next_attempt_at, request_id),
        )


def hubspot_request(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        f"{HUBSPOT_API_BASE_URL}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {HUBSPOT_SERVICE_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("message", "")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            pass
        suffix = f": {clean(detail, 500)}" if detail else ""
        raise RuntimeError(f"HubSpot returned HTTP {exc.code}{suffix}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("HubSpot is temporarily unavailable") from exc


def split_contact_name(name: str) -> tuple[str, str]:
    parts = name.strip().split(maxsplit=1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


def find_hubspot_contact(email: str) -> str:
    result = hubspot_request(
        "/crm/objects/2026-03/contacts/search",
        {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "EQ", "value": email},
                    ]
                }
            ],
            "limit": 1,
            "properties": ["email"],
        },
    )
    matches = result.get("results") or []
    return str(matches[0].get("id") or "") if matches else ""


def hubspot_deal_name(request_id: int, fields: dict[str, object]) -> str:
    company_or_name = str(fields.get("company_name") or fields["name"])
    service = str(fields.get("service") or "Discovery inquiry")
    suffix = f" · Website request #{request_id}"
    return f"{clean(f'{company_or_name} — {service}', 250 - len(suffix))}{suffix}"


def attribution_source(attribution: dict[str, str]) -> str:
    if attribution.get("utm_source"):
        return attribution["utm_source"]
    if attribution.get("audo_campaign"):
        return f"audo:{attribution['audo_campaign']}"
    referring_url = attribution.get("referring_url")
    if referring_url:
        return urlparse(referring_url).hostname or "referral"
    return "direct"


def hubspot_attribution_properties(claimed: dict[str, object]) -> dict[str, str]:
    properties: dict[str, str] = {}
    value_keys = {
        "landing_url": "landing_url",
        "referring_url": "referring_url",
        "utm_source": "utm_source",
        "utm_medium": "utm_medium",
        "utm_campaign": "utm_campaign",
        "utm_content": "utm_content",
        "campaign_code": "audo_campaign",
    }
    for touch in ("first", "latest"):
        attribution = attribution_from_row(claimed, touch)
        source_property = HUBSPOT_ATTRIBUTION_PROPERTIES.get(f"{touch}_source")
        if source_property:
            properties[source_property] = attribution_source(attribution)
        for property_suffix, attribution_key in value_keys.items():
            value = attribution.get(attribution_key)
            property_name = HUBSPOT_ATTRIBUTION_PROPERTIES.get(f"{touch}_{property_suffix}")
            if value and property_name:
                properties[property_name] = value
    return properties


def find_hubspot_deal(deal_name: str) -> str:
    result = hubspot_request(
        "/crm/objects/2026-03/deals/search",
        {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "dealname", "operator": "EQ", "value": deal_name},
                        {"propertyName": "pipeline", "operator": "EQ", "value": HUBSPOT_PIPELINE},
                    ]
                }
            ],
            "limit": 2,
            "properties": ["dealname", "pipeline"],
            "sorts": ["createdate"],
        },
    )
    matches = result.get("results") or []
    return str(matches[0].get("id") or "") if matches else ""


def hubspot_stage_for_request(request_id: int) -> str:
    with sqlite3.connect(DATABASE_PATH) as conn:
        confirmed = conn.execute(
            """
            SELECT 1 FROM consultation_bookings
            WHERE request_id = ? AND status = 'confirmed'
            LIMIT 1
            """,
            (request_id,),
        ).fetchone()
    return HUBSPOT_DISCOVERY_SCHEDULED_STAGE if confirmed else HUBSPOT_NEW_INQUIRY_STAGE


def sync_claimed_hubspot_request(claimed: dict[str, object]) -> None:
    request_id = int(claimed["id"])
    attempt_count = int(claimed.get("hubspot_attempt_count") or 1)
    try:
        first_name, last_name = split_contact_name(str(claimed["name"]))
        contact_properties = {
            "firstname": first_name,
            "lastname": last_name,
            "phone": claimed.get("phone", ""),
            "company": claimed.get("company_name", ""),
            "website": claimed.get("website", ""),
        }
        contact_id = str(claimed.get("hubspot_contact_id") or "")
        if not contact_id:
            contact_id = find_hubspot_contact(str(claimed["email"]))
        if contact_id:
            hubspot_request(
                "/crm/objects/2026-03/contacts/batch/update",
                {
                    "inputs": [
                        {
                            "id": contact_id,
                            "properties": {
                                key: value for key, value in contact_properties.items() if value
                            },
                        }
                    ]
                },
            )
        else:
            contact = hubspot_request(
                "/crm/objects/2026-03/contacts/batch/upsert",
                {
                    "inputs": [
                        {
                            "id": claimed["email"],
                            "idProperty": "email",
                            "properties": {
                                **{
                                    key: value
                                    for key, value in contact_properties.items()
                                    if value
                                },
                                "lifecyclestage": "lead",
                                "hs_lead_status": "NEW",
                            },
                        }
                    ]
                },
            )
            contact_results = contact.get("results") or []
            if not contact_results or not contact_results[0].get("id"):
                raise RuntimeError("HubSpot did not return a contact ID")
            contact_id = str(contact_results[0]["id"])
        save_hubspot_ids(request_id, contact_id=contact_id)

        first_touch = attribution_from_row(claimed, "first")
        latest_touch = attribution_from_row(claimed, "latest")
        inquiry_details = "\n".join(
            line
            for line in (
                f"Submitted from getaudo.com (request #{request_id})",
                f"Name: {claimed['name']}",
                f"Email: {claimed['email']}",
                f"Phone: {claimed.get('phone') or 'Not provided'}",
                f"Website: {claimed.get('website') or 'Not provided'}",
                f"Interested in: {claimed.get('interest_context') or claimed.get('service') or 'General discovery'}",
                *attribution_lines("First touch", first_touch),
                *attribution_lines("Latest touch", latest_touch),
                "",
                str(claimed.get("message") or ""),
            )
        )
        attribution_properties = hubspot_attribution_properties(claimed)
        desired_stage = hubspot_stage_for_request(request_id)
        deal_id = str(claimed.get("hubspot_deal_id") or "")
        deal_was_existing = bool(deal_id)
        if not deal_id:
            deal_name = hubspot_deal_name(request_id, claimed)
            deal_id = find_hubspot_deal(deal_name)
            deal_was_existing = bool(deal_id)
        if not deal_id:
            trace_id = hashlib.sha256(f"{PUBLIC_BASE_URL}:hubspot-deal:{request_id}".encode("utf-8")).hexdigest()
            deal = hubspot_request(
                "/crm/objects/2026-03/deals",
                {
                    "objectWriteTraceId": trace_id,
                    "properties": {
                        "dealname": hubspot_deal_name(request_id, claimed),
                        "pipeline": HUBSPOT_PIPELINE,
                        "dealstage": desired_stage,
                        "description": inquiry_details,
                        **attribution_properties,
                    },
                    "associations": [
                        {
                            "to": {"id": contact_id},
                            "types": [
                                {
                                    "associationCategory": "HUBSPOT_DEFINED",
                                    "associationTypeId": 3,
                                }
                            ],
                        }
                    ],
                },
            )
            deal_id = str(deal.get("id") or "")
        if not deal_id:
            raise RuntimeError("HubSpot did not return a deal ID")
        if deal_was_existing:
            hubspot_request(
                "/crm/objects/2026-03/deals/batch/update",
                {
                    "inputs": [
                        {
                            "id": deal_id,
                            "properties": {
                                "dealstage": desired_stage,
                                "description": inquiry_details,
                                **attribution_properties,
                            },
                        }
                    ]
                },
            )
        save_hubspot_ids(request_id, deal_id=deal_id)
        mark_hubspot_status(request_id, "synced", contact_id=contact_id, deal_id=deal_id)
    except Exception as exc:  # pragma: no cover - depends on the live HubSpot API.
        schedule_hubspot_retry(request_id, attempt_count, str(exc))
        print(f"discovery request {request_id} stored; HubSpot sync failed: {exc}", file=sys.stderr)


def sync_hubspot(request_id: int, fields: dict[str, str] | None = None) -> None:
    """Synchronously process one request; retained for tests and operator reconciliation."""
    queue_hubspot_sync(request_id)
    claimed = claim_next_hubspot_sync(request_id)
    if claimed:
        sync_claimed_hubspot_request(claimed)


def reconcile_hubspot_syncs(limit: int | None = None) -> int:
    if AUDIT_FIXTURES_ENABLED or not HUBSPOT_SERVICE_KEY:
        return 0
    processed = 0
    for _ in range(limit or HUBSPOT_SYNC_BATCH_SIZE):
        claimed = claim_next_hubspot_sync()
        if not claimed:
            break
        sync_claimed_hubspot_request(claimed)
        processed += 1
    return processed


def hubspot_sync_worker() -> None:
    while True:
        try:
            processed = reconcile_hubspot_syncs()
        except Exception as exc:  # pragma: no cover - defensive worker guard.
            processed = 0
            print(f"HubSpot reconciliation worker error: {exc}", file=sys.stderr)
        if processed >= HUBSPOT_SYNC_BATCH_SIZE:
            continue
        HUBSPOT_SYNC_WAKE.wait(timeout=HUBSPOT_SYNC_POLL_SECONDS)
        HUBSPOT_SYNC_WAKE.clear()


def start_hubspot_sync_worker() -> threading.Thread:
    global HUBSPOT_SYNC_THREAD
    with HUBSPOT_SYNC_THREAD_LOCK:
        if HUBSPOT_SYNC_THREAD and HUBSPOT_SYNC_THREAD.is_alive():
            return HUBSPOT_SYNC_THREAD
        HUBSPOT_SYNC_THREAD = threading.Thread(
            target=hubspot_sync_worker,
            name="audo-hubspot-sync",
            daemon=True,
        )
        HUBSPOT_SYNC_THREAD.start()
        return HUBSPOT_SYNC_THREAD


def build_email(request_id: int, fields: dict[str, str], request_meta: dict[str, str]) -> EmailMessage:
    message = EmailMessage()
    service = fields.get("service", "Discovery")
    company = fields.get("company_name") or fields["name"]
    message["Subject"] = f"New Audo discovery: {company} - {service}"
    message["From"] = (
        os.environ.get("GMAIL_FROM")
        or os.environ.get("SMTP_FROM")
        or os.environ.get("SMTP_USER")
        or CONSULTATION_TO
    )
    message["To"] = CONSULTATION_TO
    message["Reply-To"] = fields["email"]
    # The delivery queue is intentionally at-least-once. A stable Message-ID
    # lets Gmail and downstream mail clients recognize a replay after a worker
    # crash between provider acceptance and the SQLite status update.
    message["Message-ID"] = f"<audo-consultation-{request_id}@getaudo.com>"

    first_touch = normalize_attribution(fields.get("first_touch_json") or fields.get("first_touch"))
    latest_touch = normalize_attribution(fields.get("latest_touch_json") or fields.get("latest_touch"))
    attribution_summary = "\n".join(
        attribution_lines("First touch", first_touch) + attribution_lines("Latest touch", latest_touch)
    )
    body = f"""A new Audo discovery request was received.

Request ID: {request_id}
Submitted: {utc_now()}

Name: {fields["name"]}
Company / project: {fields.get("company_name") or "Not provided"}
Website: {fields.get("website") or "Not provided"}
Promo code: {fields.get("promo_code") or "Not provided"}
Interested in: {fields.get("interest_context") or "General discovery"}
Email: {fields["email"]}
Phone: {fields.get("phone") or "Not provided"}
Scheduling: {fields.get("timeline") or "Choose from Google Calendar after submission"}

Acquisition:
{attribution_summary}

Help needed: {fields["service"]}

What they shared:
{fields["message"]}
"""
    message.set_content(body)
    return message


def send_gmail_api_message(message: EmailMessage, retry_auth: bool = True) -> None:
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")
    request = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw_message}).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {google_access_token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15):
            return
    except urllib.error.HTTPError as exc:
        if exc.code == 401 and retry_auth:
            google_access_token(force_refresh=True)
            send_gmail_api_message(message, retry_auth=False)
            return
        raise RuntimeError(f"Gmail API returned HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Gmail API is temporarily unavailable.") from exc


def deliver_email_message(request_id: int, fields: dict[str, str], request_meta: dict[str, str]) -> None:
    message = build_email(request_id, fields, request_meta)
    if GMAIL_API_SEND_ENABLED:
        send_gmail_api_message(message)
        return

    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        raise RuntimeError("Email delivery is not configured")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_secure = os.environ.get("SMTP_SECURE", "").lower()
    use_ssl = smtp_secure == "ssl" or smtp_port == 465
    use_starttls = os.environ.get("SMTP_STARTTLS", "true").lower() not in {"0", "false", "no"}

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


def sync_claimed_email_delivery(claimed: dict[str, object]) -> None:
    request_id = int(claimed["id"])
    attempt_count = int(claimed.get("email_attempt_count") or 1)
    fields = {
        key: str(claimed.get(key) or "")
        for key in (
            "name",
            "company_name",
            "website",
            "promo_code",
            "email",
            "phone",
            "service",
            "timeline",
            "preferred_times",
            "message",
            "source",
            "interest_context",
            "first_touch_json",
            "latest_touch_json",
        )
    }
    request_meta = {
        "user_agent": str(claimed.get("user_agent") or ""),
        "referrer": str(claimed.get("referrer") or ""),
        "ip_address": str(claimed.get("ip_address") or ""),
    }
    try:
        deliver_email_message(request_id, fields, request_meta)
        mark_email_status(request_id, "sent")
    except Exception as exc:  # pragma: no cover - depends on live email provider.
        schedule_email_retry(request_id, attempt_count, str(exc))
        print(f"discovery request {request_id} stored; email delivery failed: {exc}", file=sys.stderr)


def send_email(request_id: int, fields: dict[str, str], request_meta: dict[str, str]) -> None:
    """Queue and immediately attempt owner email; the worker retries provider failures."""
    queue_email_delivery(request_id)
    claimed = claim_next_email_delivery(request_id)
    if claimed:
        sync_claimed_email_delivery(claimed)


def reconcile_email_deliveries(limit: int | None = None) -> int:
    if AUDIT_FIXTURES_ENABLED or not email_delivery_configured():
        return 0
    processed = 0
    for _ in range(limit or EMAIL_DELIVERY_BATCH_SIZE):
        claimed = claim_next_email_delivery()
        if not claimed:
            break
        sync_claimed_email_delivery(claimed)
        processed += 1
    return processed


def email_delivery_worker() -> None:
    while True:
        try:
            processed = reconcile_email_deliveries()
        except Exception as exc:  # pragma: no cover - defensive worker guard.
            processed = 0
            print(f"Email delivery worker error: {exc}", file=sys.stderr)
        if processed >= EMAIL_DELIVERY_BATCH_SIZE:
            continue
        EMAIL_DELIVERY_WAKE.wait(timeout=EMAIL_DELIVERY_POLL_SECONDS)
        EMAIL_DELIVERY_WAKE.clear()


def start_email_delivery_worker() -> threading.Thread:
    global EMAIL_DELIVERY_THREAD
    with EMAIL_DELIVERY_THREAD_LOCK:
        if EMAIL_DELIVERY_THREAD and EMAIL_DELIVERY_THREAD.is_alive():
            return EMAIL_DELIVERY_THREAD
        EMAIL_DELIVERY_THREAD = threading.Thread(
            target=email_delivery_worker,
            name="audo-email-delivery",
            daemon=True,
        )
        EMAIL_DELIVERY_THREAD.start()
        return EMAIL_DELIVERY_THREAD


def verify_recaptcha(fields: dict[str, str], request_meta: dict[str, str]) -> dict[str, object]:
    if AUDIT_FIXTURES_ENABLED:
        return {}
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

        if path in {"/assets/services.json", "/assets/scenarios.json"}:
            self.serve_services_json(send_body=send_body)
            return

        service_social_match = re.fullmatch(r"/assets/service-social/([a-z0-9-]+)\.jpg", path)
        if service_social_match:
            self.serve_service_social_card(service_social_match.group(1), send_body=send_body)
            return

        if path == "/sitemap.xml":
            self.serve_sitemap(send_body=send_body)
            return

        if path == "/robots.txt":
            self.serve_generated_text(
                build_robots_txt(PUBLIC_BASE_URL),
                "text/plain; charset=utf-8",
                send_body=send_body,
            )
            return

        if path in {"/sitemap", "/sitemap/"}:
            self.serve_user_sitemap(send_body=send_body)
            return

        if path == "/llm.txt":
            self.redirect_permanent("/llms.txt")
            return

        if path == "/llms.txt":
            self.serve_generated_text(
                build_llms_txt(PUBLIC_BASE_URL),
                "text/plain; charset=utf-8",
                send_body=send_body,
            )
            return

        if path == "/llms-full.txt":
            self.serve_generated_text(
                build_llms_full_txt(PUBLIC_BASE_URL),
                "text/plain; charset=utf-8",
                send_body=send_body,
            )
            return

        if path == "/services.md":
            self.serve_generated_text(
                build_services_markdown(PUBLIC_BASE_URL),
                "text/markdown; charset=utf-8",
                send_body=send_body,
            )
            return

        service_markdown_match = re.fullmatch(r"/services/([a-z0-9-]+)\.md", path)
        if service_markdown_match:
            entry = get_catalog_entry(service_markdown_match.group(1))
            if entry:
                self.serve_generated_text(
                    build_service_markdown(entry, PUBLIC_BASE_URL),
                    "text/markdown; charset=utf-8",
                    send_body=send_body,
                )
                return
            self.render_error(HTTPStatus.NOT_FOUND, "That service page was not found.")
            return

        if path in {"/services", "/services/"}:
            self.redirect_permanent("/#service-list")
            return

        if path in {"/scenarios", "/scenarios/"}:
            self.redirect_permanent("/#service-list")
            return

        service_match = re.fullmatch(r"/services/([a-z0-9-]+)/?", path)
        if service_match:
            service_slug = service_match.group(1)
            service = get_service(service_slug)
            if service:
                self.serve_service_page(service.slug, send_body=send_body)
                return
            removed_redirect = REMOVED_SERVICE_REDIRECTS.get(service_slug)
            if removed_redirect:
                self.redirect_permanent(removed_redirect)
                return
            self.render_error(HTTPStatus.NOT_FOUND, "That service page was not found.")
            return

        legacy_service_match = re.fullmatch(r"/scenarios/([a-z0-9-]+)/?", path)
        if legacy_service_match:
            self.redirect_permanent(f"/services/{legacy_service_match.group(1)}")
            return

        route_files = {
            "/": "index.html",
            "/privacy": "privacy.html",
            "/privacy/": "privacy.html",
            "/thank-you": "thank-you.html",
            "/thank-you/": "thank-you.html",
        }
        if path in {"/app", "/app/", "/app.html"}:
            self.redirect_permanent("/")
            return

        if path in route_files:
            if route_files[path] == "index.html":
                self.serve_index(send_body=send_body)
            elif route_files[path] == "thank-you.html":
                self.serve_thank_you(send_body=send_body)
            else:
                self.serve_file(BASE_DIR / route_files[path], send_body=send_body)
            return

        self.serve_static_or_index(path, send_body=send_body)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/consultation":
            self.handle_consultation_post()
            return
        if path == "/api/availability":
            self.handle_availability_post()
            return
        if path == "/api/book":
            self.handle_booking_post()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_consultation_post(self) -> None:
        wants_json = self.wants_json_response()

        try:
            fields = self.read_form_fields()
            if clean(fields.get("website_url_confirm"), 255):
                if wants_json:
                    self.send_json(
                        HTTPStatus.OK,
                        {"ok": True, "calendar_ready": False, "fallback_url": "/thank-you"},
                    )
                else:
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
                "promo_code": clean(fields.get("promo_code"), 80),
                "email": clean(fields.get("email"), 254),
                "phone": clean(fields.get("phone"), 80),
                "timeline": clean(fields.get("timeline"), 80) or "Schedule after request",
                "preferred_times": clean(fields.get("preferred_times"), 1000),
                "service": clean(fields.get("service"), 120) or "Not sure yet",
                "message": clean(fields.get("message"), 5000),
                "source": clean(fields.get("source"), 140),
                "interest_context": clean(fields.get("interest_context"), 260),
                "first_touch": clean(fields.get("first_touch"), 4000),
                "latest_touch": clean(fields.get("latest_touch"), 4000),
                "recaptcha_score": recaptcha.get("score"),
                "recaptcha_action": recaptcha.get("action"),
                "recaptcha_hostname": recaptcha.get("hostname"),
            }
            self.validate_payload(payload)

            request_id = store_request(payload, request_meta)
            booking_token = issue_booking_token(request_id)
            queue_hubspot_sync(request_id)
            send_email(request_id, payload, request_meta)
            if wants_json:
                self.send_json(
                    HTTPStatus.CREATED,
                    {
                        "ok": True,
                        "request_id": request_id,
                        "booking_token": booking_token,
                        "calendar_ready": calendar_configured(),
                        "fallback_url": GOOGLE_CALENDAR_BOOKING_URL or "/thank-you",
                    },
                )
            else:
                self.redirect("/thank-you", note_saved=True)
        except ValueError as exc:
            if wants_json:
                self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            else:
                self.render_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - defensive runtime guard.
            print(f"discovery form error: {exc}", file=sys.stderr)
            message = "Something went wrong saving your request. Please try again in a moment."
            if wants_json:
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": message})
            else:
                self.render_error(HTTPStatus.INTERNAL_SERVER_ERROR, message)

    def handle_availability_post(self) -> None:
        try:
            self.validate_request_origin()
            fields = self.read_json_fields()
            request_id = self.parse_request_id(fields.get("request_id"))
            token = clean(fields.get("booking_token"), 512)
            get_consultation_for_booking(request_id, token)

            existing = get_active_booking(request_id)
            if existing and existing.get("status") == "confirmed":
                self.send_json(
                    HTTPStatus.OK,
                    {"ok": True, "booked": True, "booking": booking_json(existing)},
                )
                return
            if not calendar_configured():
                raise GoogleCalendarError("Live scheduling is not configured yet.", status=503)

            days = build_availability()
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "booked": False,
                    "timezone": BOOKING_TIMEZONE,
                    "timezone_label": "Central Time",
                    "duration_minutes": BOOKING_DURATION_MINUTES,
                    "minimum_notice_hours": BOOKING_MIN_NOTICE_HOURS,
                    "days": days,
                    "fallback_url": GOOGLE_CALENDAR_BOOKING_URL,
                },
            )
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except GoogleCalendarError as exc:
            self.send_json(
                HTTPStatus(exc.status),
                {
                    "ok": False,
                    "error": str(exc),
                    "fallback_url": GOOGLE_CALENDAR_BOOKING_URL,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive runtime guard.
            print(f"availability error: {exc}", file=sys.stderr)
            self.send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": "Available times could not be loaded right now."},
            )

    def handle_booking_post(self) -> None:
        booking: dict[str, object] | None = None
        try:
            self.validate_request_origin()
            fields = self.read_json_fields()
            request_id = self.parse_request_id(fields.get("request_id"))
            token = clean(fields.get("booking_token"), 512)
            consultation = get_consultation_for_booking(request_id, token)

            requested_start = parse_iso_datetime(clean(fields.get("start"), 80))
            slot_map = {start.isoformat(timespec="seconds"): (start, end) for start, end in candidate_slots()}
            selected = slot_map.get(requested_start.isoformat(timespec="seconds"))
            if not selected:
                raise BookingUnavailable(
                    "That time is outside the current booking window. Please refresh the available times."
                )
            start, end = selected

            existing = get_active_booking(request_id)
            if existing and existing.get("status") == "confirmed":
                self.send_json(
                    HTTPStatus.OK,
                    {"ok": True, "already_booked": True, "booking": booking_json(existing)},
                )
                return
            if existing:
                existing_start = parse_iso_datetime(str(existing["start_utc"]))
                if existing_start != start:
                    raise BookingUnavailable("A different time is already being confirmed for this request.")
                booking = existing
                start = existing_start
                end = parse_iso_datetime(str(existing["end_utc"]))
            else:
                buffer = timedelta(minutes=BOOKING_BUFFER_MINUTES)
                busy = google_busy_periods(start - buffer, end + buffer)
                if any(intervals_overlap(start - buffer, end + buffer, busy_start, busy_end) for busy_start, busy_end in busy):
                    raise BookingUnavailable("That time was just taken. Please choose another available time.")
                booking, _ = reserve_booking(request_id, start, end)

            event_id = deterministic_event_id(request_id, start)
            event = create_calendar_event(consultation, start, end, event_id)
            confirmed = finalize_booking(int(booking["id"]), event)
            queue_hubspot_sync(request_id, force=True)
            self.send_json(
                HTTPStatus.CREATED,
                {"ok": True, "already_booked": False, "booking": booking_json(confirmed)},
            )
        except BookingUnavailable as exc:
            self.send_json(
                HTTPStatus.CONFLICT,
                {"ok": False, "error": str(exc), "refresh_availability": True},
            )
        except (ValueError, KeyError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except GoogleCalendarError as exc:
            if booking:
                fail_booking(int(booking["id"]), str(exc))
            self.send_json(
                HTTPStatus(exc.status),
                {
                    "ok": False,
                    "error": "The time could not be confirmed with Google Calendar. Please try again.",
                    "fallback_url": GOOGLE_CALENDAR_BOOKING_URL,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive runtime guard.
            if booking:
                fail_booking(int(booking["id"]), str(exc))
            print(f"booking error: {exc}", file=sys.stderr)
            self.send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": "The appointment could not be booked right now."},
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

    def read_json_fields(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("The scheduling request was empty.")
        if content_length > MAX_BODY_BYTES:
            raise ValueError("The scheduling request was too large.")
        if "application/json" not in self.headers.get("Content-Type", ""):
            raise ValueError("Please use the scheduling form on this website.")
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("The scheduling request was not valid.") from exc
        if not isinstance(payload, dict):
            raise ValueError("The scheduling request was not valid.")
        return payload

    def wants_json_response(self) -> bool:
        return "application/json" in self.headers.get("Accept", "")

    @staticmethod
    def parse_request_id(value: object) -> int:
        try:
            request_id = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("The discovery request could not be found.") from exc
        if request_id <= 0:
            raise ValueError("The discovery request could not be found.")
        return request_id

    def validate_request_origin(self) -> None:
        origin = self.headers.get("Origin")
        if not origin:
            return
        origin_host = urlparse(origin).netloc.lower()
        allowed_hosts = {
            urlparse(PUBLIC_BASE_URL).netloc.lower(),
            clean(self.headers.get("Host"), 255).lower(),
        }
        if origin_host not in allowed_hosts:
            raise ValueError("Please use the scheduling form on this website.")

    def send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    @staticmethod
    def validate_payload(payload: dict[str, str]) -> None:
        if not payload["name"]:
            raise ValueError("Please include your name.")
        if not payload["email"] or not EMAIL_RE.match(payload["email"]):
            raise ValueError("Please include a valid email address.")
        if not payload["message"]:
            raise ValueError("Please tell me what's going on.")

    def serve_services_json(self, send_body: bool = True) -> None:
        cards = service_cards()
        data = json.dumps(
            {
                "count": len(cards),
                "services": cards,
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

    def serve_service_social_card(self, slug: str, send_body: bool = True) -> None:
        service = get_service(slug)
        if not service:
            self.render_error(HTTPStatus.NOT_FOUND, "That service image was not found.")
            return

        data = SERVICE_SOCIAL_CARD_CACHE.get(service.slug)
        if data is None:
            data = make_service_social_card(service)
            if data is not None:
                SERVICE_SOCIAL_CARD_CACHE[service.slug] = data
        if data is None:
            self.serve_file(BASE_DIR / "assets" / "audo-social-card-free-discovery.jpg", send_body=send_body)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Cache-Control", f"public, max-age={SERVICE_SOCIAL_CARD_CACHE_SECONDS}")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def serve_sitemap(self, send_body: bool = True) -> None:
        data = build_sitemap_xml(PUBLIC_BASE_URL, SITEMAP_LASTMOD).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def serve_user_sitemap(self, send_body: bool = True) -> None:
        h = lambda value: html.escape(str(value), quote=True)
        entries = catalog_entries()
        grouped = grouped_catalog(entries)

        main_links = [
            ("/", "Home", "See how Aaron helps small businesses fix websites, automate work, use AI, and build tools."),
            ("/#services", "Find your starting point", "Choose an area and browse common problems Aaron helps solve."),
            ("/#why", "Why Audo", "Learn why working directly with Aaron can be simpler than hiring a large agency."),
            ("/#discovery", "Book free discovery", "Tell Aaron what's going on, then pick a time to talk."),
            ("/privacy", "Privacy Policy", "See what information Audo collects and how it is used and protected."),
        ]

        def link_cards(links: list[tuple[str, str, str]]) -> str:
            return "\n".join(
                f"""          <li>
            <a href="{h(url)}">{h(title)}</a>
            <p>{h(description)}</p>
          </li>"""
                for url, title, description in links
            )

        category_sections = []
        category_jumps = []
        for category in CATEGORY_ORDER:
            category_entries = grouped.get(category, [])
            if not category_entries:
                continue
            anchor = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
            display_category = category_label(category)
            category_jumps.append(f'<a href="#{h(anchor)}">{h(display_category)}</a>')
            service_items = "\n".join(
                f"""          <li>
            <a href="{h(entry.html_path)}">{h(entry.title)}</a>
            <p>{h(entry.summary)}</p>
          </li>"""
                for entry in category_entries
            )
            category_sections.append(
                f"""      <section class="sitemap-group" id="{h(anchor)}" aria-labelledby="{h(anchor)}-heading">
        <div class="group-title">
          <h2 id="{h(anchor)}-heading">{h(display_category)}</h2>
          <span>{len(category_entries)} common situations</span>
        </div>
        <ul class="sitemap-links">
{service_items}
        </ul>
      </section>"""
            )

        item_list = [
            {
                "@type": "ListItem",
                "position": index + 1,
                "url": f"{PUBLIC_BASE_URL}{entry.html_path}",
                "name": entry.title,
            }
            for index, entry in enumerate(entries)
        ]
        json_ld = json.dumps(
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "CollectionPage",
                        "@id": f"{PUBLIC_BASE_URL}/sitemap#webpage",
                        "url": f"{PUBLIC_BASE_URL}/sitemap",
                        "name": "Audo Sitemap",
                        "description": "A user-friendly sitemap for Audo consulting pages and service examples.",
                        "isPartOf": {"@id": "https://getaudo.com/#website"},
                        "inLanguage": "en-US",
                    },
                    {
                        "@type": "ItemList",
                        "@id": f"{PUBLIC_BASE_URL}/sitemap#service-pages",
                        "name": "Audo service pages",
                        "numberOfItems": len(entries),
                        "itemListElement": item_list,
                    },
                    {
                        "@type": "BreadcrumbList",
                        "@id": f"{PUBLIC_BASE_URL}/sitemap#breadcrumb",
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
                                "name": "Sitemap",
                                "item": f"{PUBLIC_BASE_URL}/sitemap",
                            },
                        ],
                    },
                ],
            },
            separators=(",", ":"),
        )

        analytics_js = self.analytics_consent_script()

        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Small Business Technology Help Sitemap | Audo</title>
  <meta name="description" content="Find Audo help for small-business websites, automation, AI, internal tools, software, and everyday technology problems.">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="author" content="Aaron">
  <meta name="theme-color" content="#101815">
  <link rel="canonical" href="{h(PUBLIC_BASE_URL + "/sitemap")}">
  <link rel="alternate" href="/llms.txt" type="text/plain" title="Audo AI summary">
  <link rel="manifest" href="/site.webmanifest">
  <meta property="og:site_name" content="Audo">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="en_US">
  <meta property="og:url" content="{h(PUBLIC_BASE_URL + "/sitemap")}">
  <meta property="og:title" content="Audo Sitemap">
  <meta property="og:description" content="Find the Audo page that matches the problem you want help with.">
  <meta property="og:image" content="{h(PUBLIC_BASE_URL + "/assets/audo-social-card-free-discovery.jpg")}">
  <meta property="og:image:secure_url" content="{h(PUBLIC_BASE_URL + "/assets/audo-social-card-free-discovery.jpg")}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Audo social card with Aaron and Free Discovery call to action.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Audo Sitemap">
  <meta name="twitter:description" content="Find the Audo page that matches the problem you want help with.">
  <meta name="twitter:image" content="{h(PUBLIC_BASE_URL + "/assets/audo-social-card-free-discovery.jpg")}">
  <link rel="icon" href="/favicon.ico?v=20260630-logo-white-a">
  <link rel="icon" href="/assets/favicon.svg?v=20260630-logo-white-a" type="image/svg+xml">
  <link rel="icon" href="/assets/favicon-32.png?v=20260630-logo-white-a" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png?v=20260630-logo-white-a">
  <link rel="stylesheet" href="/assets/site-footer.css?v=20260716-audit1">
  <script type="application/ld+json">{json_ld}</script>
  {analytics_js}
  <style>
    :root {{
      color-scheme: light;
      --ink: #18221d;
      --muted: #5f6b62;
      --paper: #fbfbf7;
      --white: #ffffff;
      --line: rgba(24, 34, 29, 0.14);
      --evergreen: #1f4739;
      --brass: #c89b4b;
      --charcoal: #101815;
      --shadow: 0 24px 70px rgba(12, 18, 15, 0.14);
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
    a {{ color: inherit; }}
    .skip-link {{
      min-height: 44px;
      display: flex;
      align-items: center;
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
    a:focus-visible {{
      outline: 3px solid #f4dca9;
      outline-offset: 3px;
    }}
    .shell {{
      width: min(1160px, calc(100% - 36px));
      margin: 0 auto;
    }}
    header {{
      color: var(--white);
      background:
        linear-gradient(115deg, rgba(12, 18, 16, 0.94), rgba(31, 71, 57, 0.86)),
        url("/assets/consulting-technology-hero.webp") center / cover no-repeat;
      padding: 32px 0 70px;
    }}
    header nav {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 78px;
    }}
    .logo {{
      width: 136px;
      height: auto;
      display: block;
    }}
    header nav a {{
      min-height: 48px;
      display: inline-flex;
      align-items: center;
      color: rgba(255, 255, 255, 0.86);
      font-weight: 820;
      text-decoration: none;
    }}
    header nav a:hover {{ color: #fff; }}
    .header-nav-links {{
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .eyebrow {{
      margin: 0 0 14px;
      color: #f4dca9;
      font-size: 13px;
      font-weight: 820;
      letter-spacing: 0.09em;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 850px;
      margin: 0;
      font-size: clamp(48px, 9vw, 92px);
      line-height: 0.95;
      letter-spacing: 0;
    }}
    .hero-copy {{
      max-width: 700px;
      margin: 24px 0 0;
      color: rgba(255, 255, 255, 0.82);
      font-size: clamp(18px, 2.5vw, 24px);
      line-height: 1.45;
    }}
    main {{
      padding: 64px 0 82px;
    }}
    .section {{
      margin-top: 52px;
    }}
    .section:first-child {{
      margin-top: 0;
    }}
    .section-head {{
      display: grid;
      grid-template-columns: minmax(0, 0.86fr) minmax(280px, 0.54fr);
      gap: 30px;
      align-items: end;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--line);
    }}
    h2 {{
      margin: 0;
      font-size: clamp(34px, 6vw, 58px);
      line-height: 1;
      letter-spacing: 0;
    }}
    .section-head p {{
      margin: 0;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.55;
    }}
    .sitemap-links {{
      list-style: none;
      margin: 24px 0 0;
      padding: 0;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .sitemap-links li {{
      min-height: 150px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: rgba(255, 255, 255, 0.78);
      box-shadow: 0 16px 40px rgba(12, 18, 15, 0.05);
    }}
    .sitemap-links a {{
      min-height: 48px;
      display: flex;
      align-items: center;
      color: var(--ink);
      font-size: 18px;
      font-weight: 860;
      line-height: 1.18;
      text-decoration-color: rgba(200, 155, 75, 0.58);
      text-decoration-thickness: 2px;
      text-underline-offset: 4px;
    }}
    .sitemap-links a:hover {{
      text-decoration-color: var(--brass);
    }}
    .sitemap-links p {{
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.45;
    }}
    .sitemap-group {{
      margin-top: 46px;
      scroll-margin-top: 24px;
    }}
    .category-jumps {{
      margin: 28px 0 8px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #eef4f1;
    }}
    .category-jumps h2 {{
      margin: 0 0 10px;
      font-size: 18px;
      line-height: 1.25;
    }}
    .category-jump-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .category-jump-links a {{
      min-height: 48px;
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 0 14px;
      background: #fff;
      color: var(--ink);
      font-weight: 790;
      text-decoration: none;
    }}
    .category-jump-links a:hover {{
      border-color: rgba(31, 71, 57, 0.42);
      background: #f9fbfa;
      color: var(--evergreen);
    }}
    .group-title {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }}
    .group-title h2 {{
      font-size: clamp(28px, 4.8vw, 46px);
    }}
    .group-title span {{
      color: #725119;
      font-size: 13px;
      font-weight: 820;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .cta {{
      margin-top: 60px;
      padding: 28px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: center;
      color: var(--white);
      background: var(--charcoal);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .cta h2 {{
      font-size: clamp(30px, 4vw, 44px);
    }}
    .cta p {{
      max-width: 720px;
      margin: 12px 0 0;
      color: rgba(255, 255, 255, 0.76);
      font-size: 17px;
      line-height: 1.5;
    }}
    .button {{
      min-height: 52px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #f0c66f;
      border-radius: 8px;
      padding: 0 20px;
      color: #101815;
      background: #f0c66f;
      font-weight: 860;
      text-decoration: none;
      white-space: nowrap;
    }}
    footer {{
      padding: 24px 0;
      color: rgba(255, 255, 255, 0.74);
      background: #0c1210;
      font-size: 14px;
      text-align: center;
    }}
    footer a {{
      color: rgba(255, 255, 255, 0.92);
      font-weight: 820;
      text-decoration: none;
    }}
    @media (max-width: 900px) {{
      .section-head, .cta {{
        grid-template-columns: 1fr;
      }}
      .sitemap-links {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 620px) {{
      header {{
        padding-bottom: 52px;
      }}
      header nav {{
        align-items: flex-start;
        flex-direction: column;
        margin-bottom: 54px;
      }}
      .header-nav-links {{ width: 100%; justify-content: space-between; gap: 12px; }}
      .header-nav-links a:not(.nav-cta) {{ display: none; }}
      .sitemap-links {{
        grid-template-columns: 1fr;
      }}
      .group-title {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .cta {{
        padding: 22px;
      }}
      .button {{
        width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to sitemap content</a>
  <header>
    <div class="shell">
      <nav aria-label="Sitemap navigation">
        <a href="/" aria-label="Audo home">
          <img class="logo" src="/assets/audo-logo-white.png" alt="Audo">
        </a>
        <div class="header-nav-links">
          <a href="/#services">Find your starting point</a>
          <a href="/#why">Why Audo</a>
          <a class="nav-cta" href="/#discovery">Book free discovery</a>
        </div>
      </nav>
      <p class="eyebrow">Sitemap</p>
      <h1>Find the kind of help you need.</h1>
      <p class="hero-copy">Browse website, automation, AI, software, and everyday technology problems Aaron can help with.</p>
    </div>
  </header>
  <main id="main">
    <div class="shell">
      <section class="section" aria-labelledby="main-pages-heading">
        <div class="section-head">
          <h2 id="main-pages-heading">Start here.</h2>
          <p>Use these links to see the overview, browse examples, or book a call.</p>
        </div>
        <ul class="sitemap-links">
{link_cards(main_links)}
        </ul>
      </section>

      <nav class="category-jumps" aria-labelledby="category-jumps-heading">
        <h2 id="category-jumps-heading">Jump to the problem that sounds closest</h2>
        <div class="category-jump-links">{' '.join(category_jumps)}</div>
      </nav>

{chr(10).join(category_sections)}

      <section class="cta" aria-labelledby="sitemap-cta-heading">
        <div>
          <h2 id="sitemap-cta-heading">Not sure which page to choose?</h2>
          <p>Skip the list and tell me what's going on. You don't need to diagnose it first.</p>
        </div>
        <a class="button" href="/#discovery">Book free discovery</a>
      </section>
    </div>
  </main>
  <footer id="site-footer" class="mega-footer">
    <div class="shell footer-shell">
      <section class="footer-cta" aria-labelledby="footer-cta-heading">
        <div class="footer-cta-copy">
          <p class="footer-eyebrow">Free 30-minute discovery call</p>
          <h2 id="footer-cta-heading">Ready to talk it through?</h2>
          <p>Send a short note, then pick a free 30-minute Google Meet time.</p>
        </div>
        <a class="footer-cta-button" href="/#discovery">Book free discovery</a>
      </section>
      <div class="footer-grid">
        <div class="footer-brand">
          <a class="footer-logo" href="/" aria-label="Audo home"><img src="/assets/audo-logo-white.png" alt="Audo"></a>
          <p>Practical, senior help for small businesses—directly from Aaron.</p>
          <a class="footer-email" href="mailto:aaron@getaudo.com">aaron@getaudo.com</a>
        </div>
        <nav class="footer-nav" aria-labelledby="footer-help-heading">
          <h2 id="footer-help-heading">Ways I can help</h2>
          <ul>
            <li><a href="/#services">Find your starting point</a></li>
            <li><a href="/services/fix-a-broken-contact-form">Fix a website problem</a></li>
            <li><a href="/services/reduce-copy-and-paste-between-tools">Cut repetitive work</a></li>
            <li><a href="/services/choose-ai-tools-for-your-business">Use AI with confidence</a></li>
            <li><a href="/services/decide-what-to-build-first">Choose what to do first</a></li>
          </ul>
        </nav>
        <nav class="footer-nav" aria-labelledby="footer-explore-heading">
          <h2 id="footer-explore-heading">Explore Audo</h2>
          <ul>
            <li><a href="/#why">About Aaron and Audo</a></li>
            <li><a href="/#client-work">Client work</a></li>
            <li><a href="/sitemap" aria-current="page">View all pages</a></li>
          </ul>
        </nav>
        <div class="footer-next">
          <h2>What happens next</h2>
          <ol>
            <li><span aria-hidden="true">1</span><p>Tell me what's going on.</p></li>
            <li><span aria-hidden="true">2</span><p>Pick a 30-minute Google Meet time.</p></li>
          </ol>
          <p class="footer-response">I'll review your note before we talk.</p>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 Audo. Aaron, Founder &amp; Senior Tech Partner.</p>
        <nav class="footer-legal" aria-label="Privacy and site information">
          <a href="/privacy">Privacy</a>
          <a href="/sitemap" aria-current="page">Sitemap</a>
          <a href="/privacy#cookies">Cookie information</a>
        </nav>
      </div>
    </div>
  </footer>
  <script src="/assets/attribution.js?v=20260725-attribution1" defer></script>
</body>
</html>"""
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if send_body:
            self.wfile.write(encoded)

    def serve_service_page(self, slug: str, send_body: bool = True) -> None:
        service = get_service(slug)
        if not service:
            self.render_error(HTTPStatus.NOT_FOUND, "That service page was not found.")
            return

        h = lambda value: html.escape(str(value), quote=True)
        initial_attribution = h(
            json.dumps(
                initial_request_attribution(
                    self.path,
                    self.headers.get("Referer") or "",
                ),
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        explorer_card = next(
            (card for card in service_cards() if card["source_title"] == service.title),
            None,
        )
        group_fallbacks = {
            "Website and app care": "website",
            "Automation": "work",
            "AI coaching and support": "ai",
            "Product strategy": "decisions",
            "Small business setup and operations": "decisions",
        }
        group = explorer_card["group"] if explorer_card else group_fallbacks.get(service.category, "website")
        group_label = explorer_card["group_label"] if explorer_card else service.category
        display_title = explorer_card["title"] if explorer_card else service.title
        display_summary = explorer_card["summary"] if explorer_card else service.summary
        display_result = explorer_card["result"] if explorer_card else service.result
        page_meta_title = (
            "Should I buy software or have it built? | Audo"
            if service.slug == "choose-build-vs-buy-for-a-tool"
            else f"{display_title} | Audo"
        )
        page_meta_description = f"{display_summary} Talk directly with Aaron about a practical next step."
        if len(page_meta_description) > 158:
            page_meta_description = display_summary[:155].rstrip(" ,.;") + "..."
        themes = {
            "website": {"accent": "#1f624d", "soft": "#d9ebe2", "ink": "#173e31"},
            "customers": {"accent": "#b56a3e", "soft": "#f2ddd0", "ink": "#63371f"},
            "work": {"accent": "#a77925", "soft": "#f3e3b8", "ink": "#594011"},
            "ai": {"accent": "#77629b", "soft": "#e5dff0", "ink": "#45365f"},
            "decisions": {"accent": "#4f7887", "soft": "#dbe8ed", "ink": "#2c5260"},
        }
        theme = themes[group]
        scenes = {
            "website": """<div class="scene-window"><span></span><span></span><span></span><div class="scene-copy"></div><div class="scene-panel"></div></div><div class="scene-status">✓ Working for customers</div>""",
            "customers": """<div class="scene-messages"><div><span>New message</span><strong>Can you help with this?</strong></div><div><span>Reply sent</span><strong>Here is the next step.</strong></div></div>""",
            "work": """<div class="scene-flow"><span>Request arrives</span><i></i><span>Right person knows</span><i></i><span>Work gets done</span></div>""",
            "ai": """<div class="scene-ai"><div><span>Start here</span>Choose one real job that takes too long.</div><strong>✦</strong><div><span>Next</span>Try AI on that job and see if it helps.</div></div>""",
            "decisions": """<div class="scene-compare"><div><strong>Option A</strong><span>Faster start</span><span>More compromise</span></div><b>or</b><div class="is-best"><small>BETTER FIT</small><strong>Option B</strong><span>Built around the business</span></div></div>""",
        }
        scene_html = scenes[group]
        if group == "ai" and explorer_card:
            scene_html = (
                '<div class="scene-ai"><div><span>'
                + h(explorer_card["scene_before_label"])
                + "</span>"
                + h(explorer_card["scene_before"])
                + "</div><strong>✦</strong><div><span>"
                + h(explorer_card["scene_after_label"])
                + "</span>"
                + h(explorer_card["scene_after"])
                + "</div></div>"
            )
        detail_copy = explorer_card or {
            "problem_heading": service.title,
            "goal_heading": service.result,
            "approach_heading": service.solution,
            "form_heading": f"Tell me what is happening with {service.title.lower()}.",
            "form_prompt": service.summary,
            "faq_heading": f"Questions about {service.title.lower()}.",
            "steps": (service.pain, service.solution, service.result),
            "faq_questions": (
                f"What usually causes {service.title.lower()}?",
                f"How would you approach {service.title.lower()}?",
                f"What should improve after {service.title.lower()}?",
            ),
        }
        detail_steps = tuple(str(step) for step in detail_copy["steps"])
        detail_questions = tuple(str(question) for question in detail_copy["faq_questions"])
        detail_answers = tuple(
            str(answer)
            for answer in detail_copy.get(
                "faq_answers",
                (service.pain, " ".join(detail_steps), service.result),
            )
        )
        seed_message = display_title.rstrip(".!?") + "."
        social_image = f"{PUBLIC_BASE_URL}/assets/service-social/{service.slug}.jpg?v={SERVICE_SOCIAL_CARD_VERSION}"
        social_image_alt = f"Audo social card for {display_title} with Aaron."
        form_context = f"Example: {display_title} ({PUBLIC_BASE_URL}{service.url})"
        checks_html = "\n".join(
            f'<li><span>{index:02d}</span><p>{h(check)}</p></li>'
            for index, check in enumerate(detail_steps, start=1)
        )
        faqs_html = "\n".join(
            f"""<details open>
          <summary>{h(question)}</summary>
          <p>{h(answer)}</p>
        </details>"""
            for question, answer in zip(detail_questions, detail_answers)
        )
        json_ld = json.dumps(
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "WebPage",
                        "@id": f"{PUBLIC_BASE_URL}{service.url}#webpage",
                        "url": f"{PUBLIC_BASE_URL}{service.url}",
                        "name": page_meta_title,
                        "description": page_meta_description,
                        "isPartOf": {"@id": "https://getaudo.com/#website"},
                        "about": {"@id": f"{PUBLIC_BASE_URL}{service.url}#service"},
                        "primaryImageOfPage": social_image,
                        "inLanguage": "en-US",
                    },
                    {
                        "@type": "Service",
                        "@id": f"{PUBLIC_BASE_URL}{service.url}#service",
                        "name": display_title,
                        "serviceType": service.category,
                        "description": display_summary,
                        "provider": {"@id": "https://getaudo.com/#business"},
                        "areaServed": {"@type": "Country", "name": "United States"},
                        "offers": {
                            "@type": "Offer",
                            "availability": "https://schema.org/InStock",
                            "url": f"{PUBLIC_BASE_URL}{service.url}#discovery",
                            "priceSpecification": {
                                "@type": "PriceSpecification",
                                "priceCurrency": "USD",
                                "description": "Free Discovery request before any scoped consulting work.",
                            },
                        },
                    },
                    {
                        "@type": "FAQPage",
                        "@id": f"{PUBLIC_BASE_URL}{service.url}#faq",
                        "mainEntity": [
                            {
                                "@type": "Question",
                                "name": question,
                                "acceptedAnswer": {
                                    "@type": "Answer",
                                    "text": answer,
                                },
                            }
                            for question, answer in zip(detail_questions, detail_answers)
                        ],
                    },
                    {
                        "@type": "BreadcrumbList",
                        "@id": f"{PUBLIC_BASE_URL}{service.url}#breadcrumb",
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
                                "name": "Services",
                                "item": "https://getaudo.com/#services",
                            },
                            {
                                "@type": "ListItem",
                                "position": 3,
                                "name": display_title,
                                "item": f"{PUBLIC_BASE_URL}{service.url}",
                            },
                        ],
                    },
                    {
                        "@type": "Person",
                        "@id": "https://getaudo.com/#aaron",
                        "name": "Aaron",
                        "jobTitle": "Founder and Senior Tech Partner",
                        "url": "https://getaudo.com/",
                        "image": "https://getaudo.com/assets/founder-field-portrait.webp",
                        "description": "Aaron has 30 years of experience building websites and software, leading product and engineering teams, and solving technology problems for businesses large and small.",
                        "knowsAbout": [
                            "Software engineering",
                            "Practical AI workflows",
                            "Website care",
                            "Business automation",
                            "Small business technology",
                            "Technology planning",
                            "Product and engineering leadership",
                        ],
                    },
                    {
                        "@type": ["ProfessionalService", "LocalBusiness"],
                        "@id": "https://getaudo.com/#business",
                        "name": "Audo",
                        "url": "https://getaudo.com/",
                        "logo": "https://getaudo.com/assets/audo-logo-white.png",
                        "image": social_image,
                        "founder": {"@id": "https://getaudo.com/#aaron"},
                        "description": "Audo gives small businesses direct help with websites, automation, AI, internal tools, technology decisions, and ongoing support.",
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
  <title>{h(page_meta_title)}</title>
  <meta name="description" content="{h(page_meta_description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="author" content="Aaron">
  <meta name="theme-color" content="#101815">
  <link rel="canonical" href="{h(PUBLIC_BASE_URL + service.url)}">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="alternate" href="/llms.txt" type="text/plain" title="Audo AI summary">
  <meta property="og:site_name" content="Audo">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="en_US">
  <meta property="og:url" content="{h(PUBLIC_BASE_URL + service.url)}">
  <meta property="og:title" content="{h(display_title)}">
  <meta property="og:description" content="{h(display_summary)}">
  <meta property="og:image" content="{h(social_image)}">
  <meta property="og:image:secure_url" content="{h(social_image)}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{h(social_image_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{h(display_title)}">
  <meta name="twitter:description" content="{h(display_summary)}">
  <meta name="twitter:image" content="{h(social_image)}">
  <meta name="twitter:image:alt" content="{h(social_image_alt)}">
  <link rel="icon" href="/favicon.ico?v=20260630-logo-white-a">
  <link rel="icon" href="/assets/favicon.svg?v=20260630-logo-white-a" type="image/svg+xml">
  <link rel="icon" href="/assets/favicon-32.png?v=20260630-logo-white-a" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png?v=20260630-logo-white-a">
  <link rel="stylesheet" href="/assets/booking.css?v=20260716-audit1">
  <link rel="stylesheet" href="/assets/site-footer.css?v=20260716-audit1">
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
      --theme-accent: {theme["accent"]};
      --theme-soft: {theme["soft"]};
      --theme-ink: {theme["ink"]};
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
      min-height: 44px;
      display: flex;
      align-items: center;
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
    .shell {{ width: min(1280px, calc(100% - 36px)); margin: 0 auto; }}
    .site-nav {{
      position: relative;
      z-index: 5;
      width: 100%;
      padding: 18px 0;
      color: var(--white);
      background: #101815;
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
      padding: clamp(30px, 5vw, 64px) 0 clamp(46px, 7vw, 80px);
      position: relative;
      overflow: hidden;
      isolation: isolate;
      color: var(--ink);
      background: #e8efec;
    }}
    .detail-hero::before {{
      content: "";
      position: absolute;
      inset: 0;
      z-index: -2;
      opacity: 0.38;
      background-image:
        linear-gradient(rgba(31, 98, 77, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31, 98, 77, 0.08) 1px, transparent 1px);
      background-size: 36px 36px;
    }}
    .detail-hero::after {{
      content: "";
      position: absolute;
      width: 460px;
      height: 460px;
      right: -180px;
      top: -210px;
      z-index: -1;
      border-radius: 50%;
      background: color-mix(in srgb, var(--theme-soft) 76%, white);
    }}
    .eyebrow {{
      margin: 0 0 18px;
      color: #725119;
      font-size: 13px;
      font-weight: 820;
      letter-spacing: 0.09em;
      text-transform: uppercase;
    }}
    .detail-hero .eyebrow {{ color: var(--theme-accent); }}
    h1, h2, h3 {{ overflow-wrap: normal; word-break: normal; text-wrap: pretty; }}
    p {{ overflow-wrap: break-word; }}
    h1 {{ margin: 0; max-width: 840px; font-size: clamp(38px, 4.2vw, 56px); line-height: 0.98; letter-spacing: -0.04em; }}
    h2 {{ margin: 0; font-size: clamp(30px, 4vw, 48px); line-height: 1.04; letter-spacing: 0; }}
    h3 {{ margin: 0; font-size: 22px; line-height: 1.18; letter-spacing: 0; }}
    .hero-lead {{ max-width: 680px; margin: 20px 0 0; color: var(--muted); font-size: clamp(18px, 2.1vw, 22px); line-height: 1.5; }}
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
    .button.primary {{ border-color: var(--theme-accent); background: var(--theme-accent); color: var(--white); }}
    .hero-actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 32px; }}
    .hero-call-note {{ margin: 14px 0 0; color: var(--muted); font-size: 13px; font-weight: 720; line-height: 1.5; }}
    .hero-card {{
      min-height: 520px;
      display: grid;
      grid-template-columns: minmax(360px, 0.88fr) minmax(0, 1.12fr);
      overflow: hidden;
      border: 1px solid rgba(24,34,29,0.1);
      border-radius: 30px;
      background: var(--white);
      box-shadow: 0 24px 60px rgba(12,18,15,0.12);
    }}
    .hero-visual {{
      min-height: 420px;
      position: relative;
      display: grid;
      place-items: center;
      overflow: hidden;
      padding: 34px;
      background:
        linear-gradient(rgba(24,34,29,0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(24,34,29,0.055) 1px, transparent 1px),
        color-mix(in srgb, var(--theme-soft) 62%, white);
      background-size: 38px 38px;
    }}
    .hero-visual::before, .hero-visual::after {{
      content: "";
      position: absolute;
      border-radius: 50%;
      background: color-mix(in srgb, var(--theme-accent) 16%, transparent);
    }}
    .hero-visual::before {{ width: 330px; height: 330px; right: -120px; top: -135px; }}
    .hero-visual::after {{ width: 260px; height: 260px; left: -120px; bottom: -135px; }}
    .hero-copy {{
      display: grid;
      align-content: center;
      padding: clamp(36px, 5vw, 68px);
    }}
    .hero-copy h1 {{ max-width: 15ch; }}
    .hero-result {{
      max-width: 620px;
      margin-top: 26px;
      padding: 18px 20px;
      border: 1px solid color-mix(in srgb, var(--theme-accent) 24%, transparent);
      border-radius: 18px;
      color: var(--theme-ink);
      background: color-mix(in srgb, var(--theme-soft) 66%, white);
    }}
    .hero-result span {{ display: block; margin-bottom: 6px; font-size: 11px; font-weight: 850; letter-spacing: 0.09em; text-transform: uppercase; }}
    .hero-result p {{ margin: 0; font-size: 16px; line-height: 1.5; }}
    .scene-window {{
      width: min(390px, 92%);
      min-height: 240px;
      position: relative;
      z-index: 1;
      border: 1px solid rgba(24,34,29,0.12);
      border-radius: 24px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 22px 46px rgba(24,34,29,0.1);
    }}
    .scene-window > span {{ display: inline-block; width: 9px; height: 9px; margin: 18px 0 0 6px; border-radius: 50%; background: rgba(24,34,29,0.12); }}
    .scene-window > span:first-child {{ margin-left: 20px; background: var(--theme-accent); }}
    .scene-copy {{ width: 48%; height: 12px; margin: 44px 0 0 26px; border-radius: 8px; background: rgba(24,34,29,0.14); box-shadow: 0 34px 0 rgba(24,34,29,0.09), 0 68px 0 rgba(24,34,29,0.09); }}
    .scene-panel {{ width: 30%; height: 112px; position: absolute; right: 26px; bottom: 28px; border-radius: 20px; background: color-mix(in srgb, var(--theme-soft) 72%, white); }}
    .scene-status {{ position: absolute; z-index: 2; right: 10%; bottom: 20%; padding: 13px 18px; border-radius: 999px; color: var(--theme-ink); background: white; box-shadow: 0 12px 30px rgba(24,34,29,0.12); font-size: 14px; font-weight: 800; }}
    .scene-messages, .scene-ai {{ width: min(400px, 96%); position: relative; z-index: 1; display: grid; gap: 18px; }}
    .scene-messages div, .scene-ai div {{ padding: 20px; border: 1px solid rgba(24,34,29,0.11); border-radius: 20px; background: rgba(255,255,255,0.94); box-shadow: 0 14px 30px rgba(24,34,29,0.08); }}
    .scene-messages div:last-child {{ margin-left: 48px; border-color: color-mix(in srgb, var(--theme-accent) 32%, transparent); }}
    .scene-messages span {{ display: block; margin-bottom: 7px; color: var(--theme-accent); font-size: 11px; font-weight: 850; letter-spacing: 0.08em; text-transform: uppercase; }}
    .scene-messages strong {{ font-size: 17px; }}
    .scene-flow {{ width: min(430px, 96%); position: relative; z-index: 1; display: grid; grid-template-columns: 1fr 22px 1fr 22px 1fr; align-items: center; }}
    .scene-flow span {{ min-height: 92px; display: grid; place-items: center; padding: 12px; border: 1px solid rgba(24,34,29,0.12); border-radius: 18px; background: white; text-align: center; font-size: 13px; font-weight: 780; }}
    .scene-flow span:last-child {{ color: white; background: var(--theme-accent); }}
    .scene-flow i {{ height: 2px; background: var(--theme-accent); opacity: 0.5; }}
    .scene-ai {{ place-items: center; }}
    .scene-ai strong {{ width: 74px; height: 74px; display: grid; place-items: center; border-radius: 24px; color: white; background: var(--theme-accent); font-size: 34px; box-shadow: 0 16px 30px color-mix(in srgb, var(--theme-accent) 28%, transparent); }}
    .scene-ai div:first-child {{ justify-self: start; }}
    .scene-ai div:last-child {{ justify-self: end; }}
    .scene-ai div > span {{ display: block; margin-bottom: 7px; color: var(--theme-accent); font-size: 11px; font-weight: 850; letter-spacing: 0.08em; text-transform: uppercase; }}
    .scene-compare {{ width: min(430px, 96%); position: relative; z-index: 1; display: grid; grid-template-columns: 1fr auto 1fr; gap: 14px; align-items: center; }}
    .scene-compare > div {{ min-height: 190px; display: grid; align-content: center; gap: 7px; padding: 22px; border: 1px solid rgba(24,34,29,0.12); border-radius: 22px; background: white; }}
    .scene-compare .is-best {{ border-color: var(--theme-accent); box-shadow: 0 16px 34px color-mix(in srgb, var(--theme-accent) 14%, transparent); }}
    .scene-compare strong {{ font-size: 20px; }}
    .scene-compare span {{ color: var(--muted); font-size: 13px; }}
    .scene-compare small {{ color: var(--theme-accent); font-weight: 850; letter-spacing: 0.08em; }}
    .scene-compare b {{ color: var(--muted); font-size: 13px; }}
    .detail-main {{ padding: clamp(52px, 7vw, 88px) 0; }}
    .detail-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(340px, 420px);
      gap: clamp(30px, 4vw, 48px);
      align-items: start;
    }}
    .detail-content {{ display: grid; gap: 34px; }}
    .story-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .story-card {{
      min-height: 230px;
      display: grid;
      align-content: start;
      padding: clamp(26px, 3vw, 34px);
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--white);
      box-shadow: 0 14px 36px rgba(12,18,15,0.06);
    }}
    .story-card.is-result {{
      color: var(--theme-ink);
      border-color: color-mix(in srgb, var(--theme-accent) 22%, transparent);
      background: color-mix(in srgb, var(--theme-soft) 66%, white);
    }}
    .story-card .eyebrow {{ margin-bottom: 12px; color: var(--theme-accent); }}
    .story-card h2 {{ max-width: none; font-size: clamp(27px, 2.6vw, 34px); line-height: 1.08; }}
    .steps-panel {{
      padding: clamp(28px, 3.5vw, 38px);
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--white);
    }}
    .steps-panel > p:not(.eyebrow) {{ max-width: 650px; margin: 14px 0 0; color: var(--muted); font-size: 17px; line-height: 1.6; }}
    .steps-panel h2 {{ max-width: 780px; font-size: clamp(31px, 3.3vw, 44px); line-height: 1.06; }}
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
      margin: 28px 0 0;
      padding: 0;
      list-style: none;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .check-list li {{
      min-height: 164px;
      display: grid;
      align-content: start;
      gap: 22px;
      padding: 20px;
      border: 1px solid rgba(24,34,29,0.1);
      border-radius: 18px;
      color: var(--muted);
      background: #f7f8f4;
      line-height: 1.5;
    }}
    .check-list li span {{ width: 38px; height: 32px; display: grid; place-items: center; border-radius: 10px; color: var(--theme-ink); background: var(--theme-soft); font-size: 12px; font-weight: 850; }}
    .check-list li p {{ margin: 0; }}
    .faq-list {{ display: grid; gap: 12px; margin-top: clamp(22px, 3vw, 34px); }}
    #faq h2 {{ max-width: 780px; font-size: clamp(30px, 3.5vw, 42px); line-height: 1.08; }}
    details {{
      border: 1px solid var(--line);
      border-radius: 16px;
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
    .faq-list summary::after {{ content: "+"; margin-left: auto; padding-left: 16px; color: var(--theme-accent); font-size: 22px; font-weight: 500; }}
    .faq-list details[open] summary::after {{ content: "−"; }}
    details p {{ margin: 0; padding: 0 18px 18px; color: var(--muted); line-height: 1.6; }}
    .form-panel {{
      position: sticky;
      top: 22px;
      overflow: hidden;
      padding: 0;
      border: 1px solid color-mix(in srgb, var(--theme-accent) 20%, var(--line));
      border-radius: 24px;
      background: var(--white);
      box-shadow: var(--shadow);
    }}
    .form-context {{ padding: 24px 28px; color: var(--theme-ink); background: color-mix(in srgb, var(--theme-soft) 72%, white); border-bottom: 1px solid color-mix(in srgb, var(--theme-accent) 16%, transparent); }}
    .form-context span {{ display: block; margin-bottom: 7px; color: var(--theme-accent); font-size: 11px; font-weight: 850; letter-spacing: 0.09em; text-transform: uppercase; }}
    .form-context strong {{ display: block; font-size: 19px; line-height: 1.3; text-wrap: balance; }}
    .form-intro {{ padding: 28px 28px 0; }}
    .form-panel h2 {{ font-size: 28px; }}
    .consultation-form {{ display: grid; gap: 14px; padding: 24px 28px 28px; }}
    .form-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; }}
    .form-field {{ display: grid; gap: 7px; }}
    .form-field.full {{ grid-column: 1 / -1; }}
    .promo-details {{ grid-column: 1 / -1; border: 1px solid rgba(24,34,29,0.14); border-radius: 14px; background: rgba(24,34,29,0.035); }}
    .promo-details summary {{ min-height: 44px; padding: 10px 12px; color: var(--muted); font-size: 13px; font-weight: 760; line-height: 1.4; list-style: none; }}
    .promo-details summary::-webkit-details-marker {{ display: none; }}
    .promo-details summary::after {{ content: "+"; margin-left: auto; color: var(--ink); font-size: 18px; font-weight: 500; }}
    .promo-details[open] summary::after {{ content: "−"; }}
    .promo-details[open] summary {{ border-bottom: 1px solid rgba(24,34,29,0.12); }}
    .promo-details .form-field {{ padding: 13px; }}
    .form-field label {{ color: var(--ink); font-size: 12px; font-weight: 820; letter-spacing: 0.06em; text-transform: uppercase; }}
    .form-field input, .form-field select, .form-field textarea {{
      width: 100%;
      border: 1px solid rgba(24,34,29,0.18);
      border-radius: 12px;
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
    .form-field [aria-invalid="true"] {{ border-color: #a33c31; box-shadow: 0 0 0 3px rgba(163,60,49,0.14); }}
    .field-error {{ margin: 0; color: #7c2d23; font-size: 12.5px; font-weight: 720; line-height: 1.45; }}
    .consultation-form .button {{ width: 100%; border: 0; cursor: pointer; font: inherit; font-weight: 820; }}
    .form-note, .form-status {{ margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .form-privacy {{ margin: 0; padding: 11px 12px; border-radius: 10px; color: #4e5d55; background: #f2f5f2; font-size: 12.5px; line-height: 1.55; }}
    .form-privacy a {{ min-height: 44px; display: inline-flex; align-items: center; color: var(--theme-ink); font-weight: 800; text-underline-offset: 3px; }}
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
    .cookie-copy a {{ min-height: 44px; display: inline-flex; align-items: center; color: var(--ink); font-weight: 760; }}
    .cookie-actions {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
    .cookie-button {{ min-height: 44px; border: 1px solid var(--line); border-radius: 8px; padding: 0 14px; color: var(--ink); background: var(--white); font: inherit; font-size: 13px; font-weight: 820; cursor: pointer; }}
    .cookie-button.primary {{ border-color: #f0c66f; background: #f0c66f; }}
    @media (max-width: 860px) {{
      .nav-links a:not(.nav-cta) {{ display: none; }}
      .nav-links {{ gap: 10px; font-size: 13px; }}
      .nav-cta {{ padding: 0 11px; }}
      .detail-hero {{ min-height: auto; padding: 22px 0 42px; }}
      .hero-card {{ min-height: 0; grid-template-columns: 1fr; border-radius: 22px; }}
      .hero-copy {{ order: -1; padding: 28px 24px 26px; }}
      .hero-visual {{ min-height: 170px; padding: 16px; border-top: 1px solid var(--line); }}
      .hero-visual > * {{ max-height: 150px; transform: scale(.72); }}
      h1 {{ font-size: clamp(36px, 9.8vw, 42px); }}
      .hero-lead {{ font-size: 17px; line-height: 1.5; }}
      .detail-layout, .story-grid, .form-grid, .check-list {{ grid-template-columns: 1fr; }}
      .story-card {{ min-height: 220px; }}
      .steps-panel h2 {{ font-size: 29px; }}
      .check-list li {{ min-height: 140px; }}
      .form-panel {{ position: static; order: -1; padding: 0; box-shadow: none; }}
      .form-intro {{ padding: 22px 20px 0; }}
      .consultation-form {{ padding: 20px; }}
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
        <a href="/#services">Find your starting point</a>
        <a href="/#why">Why Audo</a>
        <a class="nav-cta" href="#discovery">Book free discovery</a>
      </div>
    </div>
  </nav>
  <header class="detail-hero">
    <div class="shell">
      <div class="hero-card">
        <div class="hero-visual" aria-hidden="true">{scene_html}</div>
        <div class="hero-copy">
          <p class="eyebrow">{h(group_label)}</p>
          <h1>{h(display_title)}</h1>
          <p class="hero-lead">{h(display_summary)}</p>
          <div class="hero-result">
            <span>What gets better</span>
            <p>{h(display_result)}</p>
          </div>
          <div class="hero-actions">
            <a class="button primary" href="#discovery">Book free discovery</a>
            <a class="button" href="/#services">Find another starting point</a>
          </div>
          <p class="hero-call-note">Free 30-minute call. No charge or obligation.</p>
        </div>
      </div>
    </div>
  </header>
  <main id="main" class="detail-main" tabindex="-1">
    <div class="shell detail-layout">
      <article class="detail-content">
        <section class="story-grid" aria-label="What this example means for your business">
          <article class="story-card" aria-labelledby="problem-heading">
            <p class="eyebrow">What's happening</p>
            <h2 id="problem-heading">{h(detail_copy["problem_heading"])}</h2>
          </article>
          <article class="story-card is-result" aria-labelledby="result-heading">
            <p class="eyebrow">What you want</p>
            <h2 id="result-heading">{h(detail_copy["goal_heading"])}</h2>
          </article>
        </section>
        <section class="steps-panel" aria-labelledby="look-heading">
          <p class="eyebrow">How I can help</p>
          <h2 id="look-heading">{h(detail_copy["approach_heading"])}</h2>
          <ul class="check-list">
            {checks_html}
          </ul>
        </section>
        <section id="faq" aria-labelledby="faq-heading">
          <p class="eyebrow">You may be wondering</p>
          <h2 id="faq-heading">{h(detail_copy["faq_heading"])}</h2>
          <div class="faq-list">
            {faqs_html}
          </div>
        </section>
      </article>
      <aside id="discovery" class="form-panel" aria-labelledby="service-form-heading">
        <div class="form-context">
          <span>You want help with</span>
          <strong>{h(display_title)}</strong>
        </div>
        <div class="form-intro">
          <p class="eyebrow">Free 30-minute call</p>
          <h2 id="service-form-heading">{h(detail_copy["form_prompt"])}</h2>
        </div>
        <form class="consultation-form" action="/api/consultation" method="post" aria-describedby="service-form-status service-form-privacy service-form-note" data-recaptcha-form data-inline-booking>
          <div class="form-honey" aria-hidden="true">
            <label for="service_website_url_confirm">Confirm website</label>
            <input id="service_website_url_confirm" name="website_url_confirm" type="text" tabindex="-1" autocomplete="off">
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label for="service_name">Name</label>
              <input id="service_name" name="name" type="text" autocomplete="name" required>
            </div>
            <div class="form-field">
              <label for="service_email">Email</label>
              <input id="service_email" name="email" type="email" autocomplete="email" required>
            </div>
            <div class="form-field full">
              <label for="service_website">Link you want me to review (optional)</label>
              <input id="service_website" name="website" type="url" inputmode="url" autocomplete="url" placeholder="https://example.com">
            </div>
            <div class="form-field full">
              <label for="service_message">What's going on?</label>
              <textarea id="service_message" name="message" required>{h(seed_message)}

</textarea>
            </div>
            <details class="promo-details">
              <summary>Have a promo code?</summary>
              <div class="form-field">
                <label for="service_promo_code">Promo code</label>
                <input id="service_promo_code" name="promo_code" type="text" autocomplete="off">
              </div>
            </details>
          </div>
          <input type="hidden" name="service" value="{h(display_title)}">
          <input type="hidden" name="timeline" value="Schedule after request">
          <input type="hidden" name="source" value="getaudo.com service page">
          <input type="hidden" name="interest_context" value="{h(form_context)}">
          <input type="hidden" name="first_touch" value="{initial_attribution}">
          <input type="hidden" name="latest_touch" value="{initial_attribution}">
          <input type="hidden" name="recaptcha_token" value="">
          <p id="service-form-privacy" class="form-privacy">I’ll use what you share only to prepare for and follow up about your request. If you don’t pick a time, I usually reply within one business day. <a href="/privacy#information">How I handle your information</a></p>
          <button class="button primary" type="submit">Continue to scheduling</button>
          <p id="service-form-status" class="form-status" role="status" aria-live="polite"></p>
          <p id="service-form-note" class="form-note">Step 1 of 2 · After this, you'll pick a time from my calendar.</p>
        </form>
      </aside>
    </div>
  </main>
  <footer id="site-footer" class="mega-footer">
    <div class="shell footer-shell">
      <section class="footer-cta" aria-labelledby="footer-cta-heading">
        <div class="footer-cta-copy">
          <p class="footer-eyebrow">Free 30-minute discovery call</p>
          <h2 id="footer-cta-heading">Ready to talk it through?</h2>
          <p>Send a short note, then pick a free 30-minute Google Meet time.</p>
        </div>
        <a class="footer-cta-button" href="#discovery">Book free discovery</a>
      </section>
      <div class="footer-grid">
        <div class="footer-brand">
          <a class="footer-logo" href="/" aria-label="Audo home"><img src="/assets/audo-logo-white.png" alt="Audo"></a>
          <p>Practical, senior help for small businesses—directly from Aaron.</p>
          <a class="footer-email" href="mailto:aaron@getaudo.com">aaron@getaudo.com</a>
        </div>
        <nav class="footer-nav" aria-labelledby="footer-help-heading">
          <h2 id="footer-help-heading">Ways I can help</h2>
          <ul>
            <li><a href="/#services">Find your starting point</a></li>
            <li><a href="/services/fix-a-broken-contact-form">Fix a website problem</a></li>
            <li><a href="/services/reduce-copy-and-paste-between-tools">Cut repetitive work</a></li>
            <li><a href="/services/choose-ai-tools-for-your-business">Use AI with confidence</a></li>
            <li><a href="/services/decide-what-to-build-first">Choose what to do first</a></li>
          </ul>
        </nav>
        <nav class="footer-nav" aria-labelledby="footer-explore-heading">
          <h2 id="footer-explore-heading">Explore Audo</h2>
          <ul>
            <li><a href="/#why">About Aaron and Audo</a></li>
            <li><a href="/#client-work">Client work</a></li>
            <li><a href="/sitemap">View all pages</a></li>
          </ul>
        </nav>
        <div class="footer-next">
          <h2>What happens next</h2>
          <ol>
            <li><span aria-hidden="true">1</span><p>Tell me what's going on.</p></li>
            <li><span aria-hidden="true">2</span><p>Pick a 30-minute Google Meet time.</p></li>
          </ol>
          <p class="footer-response">I'll review your note before we talk.</p>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 Audo. Aaron, Founder &amp; Senior Tech Partner.</p>
        <nav class="footer-legal" aria-label="Privacy and site information">
          <a href="/privacy">Privacy</a>
          <a href="/sitemap">Sitemap</a>
          <button class="footer-preferences" type="button" data-cookie-preferences>Cookie preferences</button>
        </nav>
      </div>
    </div>
  </footer>
  <section class="cookie-consent" role="region" aria-labelledby="cookie-title" hidden>
    <div class="cookie-copy">
      <h2 id="cookie-title" tabindex="-1">Cookie choices</h2>
      <p>Audo remembers your cookie choice, uses Google reCAPTCHA to protect this form, and loads Google Analytics only if you agree. <a href="/privacy">Read the Privacy Policy.</a></p>
    </div>
    <div class="cookie-actions">
      <button class="cookie-button primary" type="button" data-cookie-accept>Allow analytics</button>
      <button class="cookie-button" type="button" data-cookie-necessary>Necessary only</button>
    </div>
  </section>
  {recaptcha_js}
  <script src="/assets/attribution.js?v=20260725-attribution1" defer></script>
  <script src="/assets/booking.js?v=20260725-attribution1" defer></script>
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
    def analytics_consent_script() -> str:
        ga_id = json.dumps(GOOGLE_ANALYTICS_ID)
        return f"""<script>
    window.AUDO_GA_MEASUREMENT_ID = {ga_id};

    (function () {{
      var analyticsId = window.AUDO_GA_MEASUREMENT_ID || "";
      if (!analyticsId) {{
        return;
      }}

      function analyticsDisableKey(id) {{
        return "ga-disable-" + id;
      }}

      function getChoice() {{
        try {{
          return window.localStorage.getItem("audo_cookie_choice");
        }} catch (error) {{
          return "";
        }}
      }}

      if (getChoice() !== "accepted") {{
        window[analyticsDisableKey(analyticsId)] = true;
        return;
      }}

      window[analyticsDisableKey(analyticsId)] = false;
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function () {{
        window.dataLayer.push(arguments);
      }};
      window.gtag("js", new Date());
      window.gtag("config", analyticsId);

      var script = document.createElement("script");
      script.async = true;
      script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(analyticsId);
      document.head.appendChild(script);
    }}());
  </script>"""

    @staticmethod
    def recaptcha_script() -> str:
        site_key = json.dumps(RECAPTCHA_SITE_KEY)
        ga_id = json.dumps(GOOGLE_ANALYTICS_ID)
        booking_url = json.dumps(GOOGLE_CALENDAR_BOOKING_URL)
        return f"""<script>
    window.AUDO_RECAPTCHA_SITE_KEY = {site_key};
    window.AUDO_GA_MEASUREMENT_ID = {ga_id};
    window.AUDO_GOOGLE_CALENDAR_BOOKING_URL = {booking_url};

    (function () {{
      var banner = document.querySelector(".cookie-consent");
      var preferences = document.querySelector("[data-cookie-preferences]");
      var accept = document.querySelector("[data-cookie-accept]");
      var necessary = document.querySelector("[data-cookie-necessary]");
      var key = "audo_cookie_choice";
      var analyticsId = window.AUDO_GA_MEASUREMENT_ID || "";
      var analyticsLoaded = false;
      var previousFocus = null;

      function analyticsDisableKey(id) {{
        return "ga-disable-" + id;
      }}

      function disableAnalytics() {{
        if (analyticsId) {{
          window[analyticsDisableKey(analyticsId)] = true;
        }}
      }}

      function loadAnalytics() {{
        if (!analyticsId || analyticsLoaded) {{
          return;
        }}

        window[analyticsDisableKey(analyticsId)] = false;
        window.dataLayer = window.dataLayer || [];
        window.gtag = window.gtag || function () {{
          window.dataLayer.push(arguments);
        }};

        window.gtag("js", new Date());
        window.gtag("config", analyticsId);

        var script = document.createElement("script");
        script.async = true;
        script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(analyticsId);
        document.head.appendChild(script);
        analyticsLoaded = true;
      }}

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

      function showBanner(moveFocus) {{
        if (banner) {{
          if (moveFocus) {{
            previousFocus = document.activeElement;
          }}
          banner.hidden = false;
          if (moveFocus) {{
            document.getElementById("cookie-title").focus();
          }}
        }}
      }}

      function hideBanner(restoreFocus) {{
        if (banner) {{
          banner.hidden = true;
        }}
        if (restoreFocus && previousFocus && previousFocus.focus) {{
          previousFocus.focus();
        }} else if (restoreFocus) {{
          var fallbackFocus = document.querySelector(".nav-cta, main a, main button");
          if (fallbackFocus) {{
            fallbackFocus.focus();
          }}
        }}
        previousFocus = null;
      }}

      var savedChoice = getChoice();
      if (savedChoice === "accepted") {{
        loadAnalytics();
      }} else {{
        disableAnalytics();
      }}

      if (banner && !savedChoice) {{
        showBanner(false);
      }}

      if (preferences) {{
        preferences.addEventListener("click", function () {{ showBanner(true); }});
      }}

      if (accept) {{
        accept.addEventListener("click", function () {{
          setChoice("accepted");
          loadAnalytics();
          hideBanner(true);
        }});
      }}

      if (necessary) {{
        necessary.addEventListener("click", function () {{
          setChoice("necessary");
          disableAnalytics();
          hideBanner(true);
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
            self.render_not_found(send_body=send_body)
            return
        if candidate.exists():
            self.serve_file(candidate, send_body=send_body)
            return
        self.render_not_found(send_body=send_body)

    def render_not_found(self, send_body: bool = True) -> None:
        body = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page Not Found | Audo</title>
  <meta name="description" content="That Audo consulting page could not be found. Return home, browse real small-business examples, or book a free discovery call.">
  <meta name="robots" content="noindex,follow">
  <meta name="theme-color" content="#101815">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <style>
    :root { --ink:#18221d; --muted:#5f6b62; --paper:#f7f5ee; --green:#173e31; --gold:#f0c66f; --line:rgba(24,34,29,.16); }
    * { box-sizing:border-box; }
    body { min-height:100svh; margin:0; color:var(--ink); background:linear-gradient(135deg,#eef3ef,var(--paper) 56%); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    a:focus-visible { outline:3px solid #b07817; outline-offset:4px; }
    .top { min-height:80px; display:flex; align-items:center; background:#101815; }
    .shell { width:min(1120px,calc(100% - 36px)); margin:auto; }
    .top .shell { display:flex; align-items:center; justify-content:space-between; gap:18px; }
    .top a { min-height:44px; display:inline-flex; align-items:center; color:#fff; text-decoration:none; font-weight:760; }
    .top img { display:block; width:126px; height:auto; }
    .top nav { display:flex; align-items:center; gap:18px; }
    .top .nav-cta { border:1px solid rgba(255,255,255,.5); border-radius:8px; padding:0 12px; background:rgba(255,255,255,.1); }
    main { min-height:calc(100svh - 80px); display:grid; place-items:center; padding:48px 0; }
    .card { width:min(760px,100%); border:1px solid var(--line); border-radius:28px; padding:clamp(30px,7vw,72px); background:#fff; box-shadow:0 26px 80px rgba(16,24,21,.12); }
    .eyebrow { margin:0 0 12px; color:#815712; font-size:.8rem; font-weight:850; letter-spacing:.12em; text-transform:uppercase; }
    h1 { max-width:12ch; margin:0; font-size:clamp(2.8rem,8vw,6rem); line-height:.92; letter-spacing:-.055em; }
    .lead { max-width:58ch; margin:24px 0 0; color:var(--muted); font-size:clamp(1.05rem,2.2vw,1.25rem); line-height:1.6; }
    .actions { display:flex; flex-wrap:wrap; gap:12px; margin-top:30px; }
    .button { min-height:48px; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--line); border-radius:10px; padding:0 19px; color:var(--ink); background:#fff; text-decoration:none; font-weight:850; }
    .button.primary { border-color:var(--gold); background:var(--gold); }
    .contact { margin:30px 0 0; padding-top:22px; border-top:1px solid var(--line); color:var(--muted); }
    .contact a { min-height:44px; display:inline-flex; align-items:center; color:var(--green); font-weight:800; }
    @media(max-width:760px) { .top nav a:not(.nav-cta) { display:none; } }
    @media(max-width:560px) { .top { min-height:70px; } main { min-height:calc(100svh - 70px); padding:20px 0; } .card { border-radius:20px; padding:28px 22px; } .actions { display:grid; } .button { width:100%; } }
  </style>
</head>
<body>
  <header class="top"><div class="shell"><a href="/" aria-label="Audo home"><img src="/assets/audo-logo-white.png" alt="Audo"></a><nav aria-label="Primary navigation"><a href="/#services">Find your starting point</a><a href="/#why">Why Audo</a><a class="nav-cta" href="/#discovery">Book free discovery</a></nav></div></header>
  <main id="main"><div class="shell"><section class="card" aria-labelledby="missing-title">
    <p class="eyebrow">Page not found</p>
    <h1 id="missing-title">That page isn't here.</h1>
    <p class="lead">The link may be old or the address may have a typo. You can go back to the homepage, browse real problems I help small businesses solve, or tell me what you need.</p>
    <div class="actions">
      <a class="button primary" href="/">Go to the homepage</a>
      <a class="button" href="/#services">Find your starting point</a>
      <a class="button" href="/#discovery">Book free discovery</a>
    </div>
    <p class="contact">Still stuck? Email <a href="mailto:aaron@getaudo.com">aaron@getaudo.com</a>.</p>
  </section></div></main>
  <script src="/assets/attribution.js?v=20260725-attribution1" defer></script>
</body>
</html>"""
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if send_body:
            self.wfile.write(encoded)

    def serve_index(self, send_body: bool = True) -> None:
        data = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        initial_attribution = json.dumps(
            initial_request_attribution(
                self.path,
                self.headers.get("Referer") or "",
            ),
            separators=(",", ":"),
            sort_keys=True,
        )
        data = data.replace("__INITIAL_ATTRIBUTION__", html.escape(initial_attribution, quote=True))
        data = data.replace("__RECAPTCHA_SITE_KEY__", json.dumps(RECAPTCHA_SITE_KEY))
        data = data.replace(
            "__GOOGLE_CALENDAR_BOOKING_URL__",
            json.dumps(GOOGLE_CALENDAR_BOOKING_URL),
        )
        encoded = data.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if send_body:
            self.wfile.write(encoded)

    def serve_thank_you(self, send_body: bool = True) -> None:
        data = (BASE_DIR / "thank-you.html").read_text(encoding="utf-8")
        note_saved = "audo_note_saved=1" in (self.headers.get("Cookie") or "")
        if note_saved:
            content = {
                "__THANK_YOU_EYEBROW__": "Step 2 of 2 · Pick a time",
                "__THANK_YOU_HEADING__": "Your note is saved.",
                "__THANK_YOU_COPY__": "Choose a free 30-minute Google Meet time. I’ll read your note before we talk.",
                "__NOTE_FIRST_HIDDEN__": "hidden",
                "__BOOKING_CONTENT_HIDDEN__": "",
                "__NOTE_SAVED__": "true",
            }
        else:
            content = {
                "__THANK_YOU_EYEBROW__": "Start with a short note",
                "__THANK_YOU_HEADING__": "Tell me what’s going on first.",
                "__THANK_YOU_COPY__": "I’ll read your note before we talk, so you won’t have to start from scratch on the call.",
                "__NOTE_FIRST_HIDDEN__": "",
                "__BOOKING_CONTENT_HIDDEN__": "hidden",
                "__NOTE_SAVED__": "false",
            }
        for placeholder, value in content.items():
            data = data.replace(placeholder, value)
        data = data.replace(
            "__GOOGLE_CALENDAR_BOOKING_URL__",
            json.dumps(GOOGLE_CALENDAR_BOOKING_URL),
        )
        encoded = data.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if send_body:
            self.wfile.write(encoded)

    def serve_generated_text(self, content: str, content_type: str, send_body: bool = True) -> None:
        encoded = content.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=3600")
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

    def redirect(self, location: str, note_saved: bool = False) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        if note_saved:
            secure = "; Secure" if PUBLIC_BASE_URL.startswith("https://") else ""
            self.send_header(
                "Set-Cookie",
                f"audo_note_saved=1; Max-Age=900; Path=/thank-you; HttpOnly; SameSite=Lax{secure}",
            )
        self.end_headers()

    def redirect_permanent(self, location: str) -> None:
        self.send_response(HTTPStatus.MOVED_PERMANENTLY)
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


def client_provisioning_worker() -> None:
    from client_provisioning import ProvisioningConfig, build_provisioner

    provisioner = build_provisioner(ProvisioningConfig.from_env())
    while True:
        try:
            summary = provisioner.run_once()
            print(json.dumps({"worker": "client_provisioning", "status": "ok", **summary}, sort_keys=True))
        except Exception as exc:  # pragma: no cover - depends on external providers.
            print(
                json.dumps({"worker": "client_provisioning", "status": "error", "error": str(exc)}),
                file=sys.stderr,
            )
        time_module.sleep(CLIENT_PROVISIONING_POLL_SECONDS)


def start_client_provisioning_worker() -> threading.Thread | None:
    global CLIENT_PROVISIONING_THREAD
    if not CLIENT_PROVISIONING_ENABLED:
        return None
    with CLIENT_PROVISIONING_THREAD_LOCK:
        if CLIENT_PROVISIONING_THREAD and CLIENT_PROVISIONING_THREAD.is_alive():
            return CLIENT_PROVISIONING_THREAD
        CLIENT_PROVISIONING_THREAD = threading.Thread(
            target=client_provisioning_worker,
            name="audo-client-provisioning",
            daemon=True,
        )
        CLIENT_PROVISIONING_THREAD.start()
        return CLIENT_PROVISIONING_THREAD


def main() -> None:
    init_db()
    start_hubspot_sync_worker()
    start_email_delivery_worker()
    start_client_provisioning_worker()
    port = int(os.environ.get("PORT", "80"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AudoHandler)
    print(json.dumps({"status": "listening", "port": port, "database": str(DATABASE_PATH)}))
    server.serve_forever()


if __name__ == "__main__":
    main()
