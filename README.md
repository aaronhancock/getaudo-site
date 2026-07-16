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

Each request is written to SQLite first, then emailed to `getaudo@gmail.com`.
The default database path is `/data/audo/consultations.sqlite3`; keep
`/data/audo` as persistent storage in Coolify so form submissions survive
rebuilds.

Email delivery uses SMTP environment variables:

```bash
CONSULTATION_TO=getaudo@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=getaudo@gmail.com
SMTP_PASS=<gmail-app-password>
SMTP_FROM=getaudo@gmail.com
SMTP_STARTTLS=true
```

If SMTP is not configured, the request is still stored and marked
`not_configured` in the database.

With JavaScript available, the request form now transitions directly into a
branded second scheduling step. The server reads busy periods from Google
Calendar, enforces the booking rules, creates the event and Google Meet link,
and invites the lead. The event description includes the submitted lead and
request details. The Google Appointment Schedule remains the outage and
non-JavaScript fallback.

The scheduler uses OAuth server credentials. Authorize `getaudo@gmail.com`
once with offline Calendar access, then configure these runtime secrets:

```bash
GOOGLE_OAUTH_CLIENT_ID=<google-oauth-web-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<optional-for-confidential-web-clients>
GOOGLE_OAUTH_REFRESH_TOKEN=<offline-refresh-token-for-getaudo@gmail.com>
GOOGLE_CALENDAR_ID=primary
```

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
Discovery Call owned by `getaudo@gmail.com`. To replace that schedule, set:

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
- `/app` and `/app.html` redirect to `/`; the old portal/product direction is
  no longer part of the public site.
