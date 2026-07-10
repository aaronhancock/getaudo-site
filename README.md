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

After a request is stored, `/thank-you` offers the live Audo Google Calendar
booking page. The deployed default points to the 30-minute Small Business
Technology Discovery Call owned by `getaudo@gmail.com`. To replace that
schedule, use Google Calendar's **Sharing options → Website embed → Inline
booking page** flow and set the iframe `src` URL in:

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
- `/thank-you` confirms discovery requests.
- `/api/consultation` accepts form submissions.
- `/health` supports container health checks.
- `/app` and `/app.html` redirect to `/`; the old portal/product direction is
  no longer part of the public site.
