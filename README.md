# Audo Marketing Site

Public consulting marketing site for `getaudo.com`.

Audo is positioned as a senior technology partner for small businesses that
need help with:

- Website and web application care
- New websites, dashboards, internal tools, and supported launches
- Business and life automation
- Practical AI coaching, training, and support
- Product consulting, brainstorming, and strategic decisions
- Ad-hoc paid services such as ADA accessibility checks, SEO/AI SEO scans, and
  website performance scans. Each starts at $100 and can be included with
  ongoing support and maintenance.

## Local Run

```bash
docker build -t getaudo-site .
docker run --rm -p 8080:80 getaudo-site
```

Then open `http://127.0.0.1:8080`.

For direct Python preview:

```bash
DATA_DIR=/tmp/getaudo-local PORT=8080 python3 server.py
```

For the local website-experience audit, enable the non-delivering calendar
fixture. It stores only synthetic requests in the chosen temporary data
directory, never contacts Google Calendar, and never sends email when SMTP is
unset:

```bash
AUDIT_FIXTURES_ENABLED=true DATA_DIR=/tmp/getaudo-audit PORT=8080 python3 server.py
```

## Discovery and Calendar Booking

The public site posts discovery requests to `/api/consultation`.

Each request is written to SQLite first, then emailed to `aaron@getaudo.com`.
The default database path is `/data/audo/consultations.sqlite3`; keep
`/data/audo` as persistent storage in Coolify so form submissions survive
rebuilds.

Email delivery uses the same Google OAuth connection as the scheduler. The
OAuth grant includes only Calendar event access, Calendar free/busy access,
and permission to send mail as the connected account:

```bash
GMAIL_API_SEND_ENABLED=true
GMAIL_FROM=aaron@getaudo.com
CONSULTATION_TO=aaron@getaudo.com
```

SMTP remains available as a fallback when Gmail API sending is disabled:

```bash
CONSULTATION_TO=aaron@getaudo.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=aaron@getaudo.com
SMTP_PASS=<gmail-app-password>
SMTP_FROM=aaron@getaudo.com
SMTP_STARTTLS=true
```

If SMTP is not configured, the request is still stored and marked
`not_configured` in the database.

Every saved request can also create or update its contact and add a **New
inquiry** deal in Audo's HubSpot sales pipeline. Configure the supported
HubSpot service key in the deployment environment (never in source control):

```bash
HUBSPOT_SERVICE_KEY=<supported-hubspot-service-key>
HUBSPOT_PIPELINE=default
HUBSPOT_NEW_INQUIRY_STAGE=appointmentscheduled
HUBSPOT_DISCOVERY_SCHEDULED_STAGE=qualifiedtobuy
HUBSPOT_SYNC_MAX_ATTEMPTS=6
HUBSPOT_SYNC_RETRY_BASE_SECONDS=30
HUBSPOT_SYNC_STALE_SECONDS=300
HUBSPOT_SYNC_POLL_SECONDS=30
HUBSPOT_SYNC_BATCH_SIZE=10
```

HubSpot sync is deliberately non-blocking. The form stores a persistent queue
record and continues to email delivery without waiting for HubSpot. A background
worker retries transient failures with exponential backoff, reclaims work left
in a stale `syncing` state after a restart, and records a terminal failure after
the configured attempt limit. Each deal name includes the website request ID;
the worker searches that exact name before creating a deal so retrying a request
does not create duplicate deals. Queue state and HubSpot IDs remain in the same
persistent SQLite database as the original request.

When a booking is confirmed, the same durable worker requeues the request and
moves its existing deal to **Discovery Scheduled**. Owner email delivery uses a
separate persistent retry queue with bounded exponential backoff. It is
at-least-once delivery and reuses a stable Message-ID on retries.

### Discovery attribution

The browser records privacy-minimized first- and latest-touch context for the
current tab in `sessionStorage`. It captures the Audo landing origin/path, an
external referring origin, and only these campaign values:

- `utm_source`
- `utm_medium`
- `utm_campaign`
- `utm_content`
- `audo_campaign`

Fragments, arbitrary query parameters, `utm_term`, and advertising click IDs are
not retained. The server validates the untrusted browser values, strips URL
queries and credentials, saves normalized JSON with the inquiry, includes a
readable summary in the owner email and deal description, and writes reportable
values to custom HubSpot **deal** properties. Contact-level analytics properties
are not changed.

Before deploying attribution-enabled sync, create or verify the custom deal
properties with:

```bash
HUBSPOT_SERVICE_KEY=<supported-hubspot-service-key> \
python3 scripts/setup_hubspot_attribution.py --apply

HUBSPOT_SERVICE_KEY=<supported-hubspot-service-key> \
python3 scripts/setup_hubspot_attribution.py
```

The setup is explicit rather than a runtime side effect. Deploying the new
HubSpot payload before the properties exist will leave the local request safe
but cause its HubSpot job to retry and eventually require operator attention.

Example tagged link:

```text
https://getaudo.com/services/fix-a-broken-contact-form?utm_source=linkedin&utm_medium=direct_outreach&utm_campaign=lead_flow_pilot&utm_content=observed_form_issue
```

Closed Won client workspace provisioning is implemented as an independently
gated reconciliation worker. Keep `CLIENT_PROVISIONING_ENABLED=false` until the
Drive and Notion destinations, activation cutoff, and one end-to-end test deal
have been verified. See `docs/client-provisioning.md`.

With JavaScript available, the request form now transitions directly into a
branded second scheduling step. The server reads busy periods from Google
Calendar, enforces the booking rules, creates the event and Google Meet link,
and invites the lead. The event description includes the submitted lead and
request details. The Google Appointment Schedule remains the outage and
non-JavaScript fallback.

The scheduler uses OAuth server credentials. Authorize `aaron@getaudo.com`
once with offline Calendar access, then configure these runtime secrets:

```bash
GOOGLE_OAUTH_CLIENT_ID=<google-oauth-web-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<optional-for-confidential-web-clients>
GOOGLE_OAUTH_REFRESH_TOKEN=<offline-refresh-token-for-aaron@getaudo.com>
GOOGLE_CALENDAR_ID=primary
GOOGLE_CALENDAR_BUSY_IDS=primary,matthewaaron@gmail.com
```

`GOOGLE_CALENDAR_ID` is the Audo calendar where bookings are created.
`GOOGLE_CALENDAR_BUSY_IDS` is the comma-separated list checked for conflicts;
the personal calendar must be shared with `aaron@getaudo.com` as free/busy.

Booking rules can be adjusted without changing code:

```bash
BOOKING_TIMEZONE=America/Chicago
BOOKING_WINDOW_DAYS=30
BOOKING_MIN_NOTICE_HOURS=24
BOOKING_START_HOUR=8
BOOKING_END_HOUR=21
BOOKING_DURATION_MINUTES=30
BOOKING_BUFFER_MINUTES=15
BOOKING_MAX_PER_DAY=4
BOOKING_TOKEN_HOURS=72
BOOKING_INTERNAL_ATTENDEE=matthewaaron@gmail.com
```

The deployed fallback points to the 30-minute Small Business Technology
Discovery Call owned by `aaron@getaudo.com`. To replace that schedule, set:

```bash
GOOGLE_CALENDAR_BOOKING_URL=https://calendar.google.com/calendar/appointments/schedules/...
```

The booking iframe is not loaded until the visitor clicks **Show Available
Times**. A `https://calendar.app.google/...` sharing link is also accepted, but
it opens the Google booking page instead of rendering inline.

Spam protection uses Google reCAPTCHA v3. Configure these runtime variables:

```bash
RECAPTCHA_SITE_KEY=<public-site-key>
RECAPTCHA_SECRET_KEY=<secret-key>
RECAPTCHA_MIN_SCORE=0.5
```

When `RECAPTCHA_SECRET_KEY` is set, `/api/consultation` verifies the token with
Google before storing or emailing the request.

## Public Routes

- `/` serves the marketing site.
- `/privacy` explains Audo's data collection, service providers, retention, and visitor choices.
- `/thank-you` confirms non-JavaScript discovery requests and offers the Google booking fallback.
- `/api/consultation` accepts form submissions.
- `/api/availability` returns protected live availability for a saved request.
- `/api/book` reserves a slot and creates the Google Calendar event and Meet link.
- `/health` supports container health checks.
- `/robots.txt` exposes crawl rules and the canonical XML sitemap.
- `/sitemap.xml` is generated from the same 30-page catalog used by the site.
- `/llms.txt` and `/llms-full.txt` provide short and expanded agent-readable context.
- `/services.md` and `/services/<slug>.md` provide agent-friendly service content tied to canonical HTML pages.
- `/app` and `/app.html` redirect to `/`; the old portal/product direction is
  no longer part of the public site.

## Tests

```bash
python3 -m unittest discover -s tests
node --test tests/test_attribution.js
```

## Reusable Website Audit

Run the packaged SEO, AI-discovery, accessibility-signal, and navigation-consistency audit against any website:

```bash
python3 scripts/website_readiness_audit.py \
  --url https://example.com \
  --output outputs/example-website-audit
```

The audit produces JSON, Markdown, and HTML reports. See
`docs/ux-audit/reusable-website-readiness-service.md` for full scope,
limitations, and the client-service workflow.
