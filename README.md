# Audo Site

Static SaaS console MVP for `getaudo.com` plus a separate trusted control-plane API.

The app currently includes:

- Firebase Auth wiring with local preview auth fallback
- Self-service site creation
- Free one-page website builder
- Free subdomain model on `*.getaudo.com`
- Paid plan gates for custom domains, backups, GitHub, and full app hosting
- Audo SVG logo asset

## Local run

```bash
docker build -t getaudo-site .
docker run --rm -p 8080:80 getaudo-site
```

Then open `http://127.0.0.1:8080`.

## Firebase Auth

For production, create `firebase-config.json` next to `index.html` using `firebase-config.example.json` as the shape.

The Firebase web config is public client configuration. Do not put Cloudflare, Coolify, GitHub App, Stripe, or backup credentials in this repo.

The production Firebase project is `getaudo`. Email/password auth is enabled. Google sign-in is disabled in `app-config.json` until a Google OAuth client ID and secret are explicitly configured for Firebase Auth.

If `firebase-config.json` and `app-config.json` are absent, the app runs with local preview auth so the console can be developed without blocking on Firebase setup.

## Control Plane API

The console can call a deployed backend when `app-config.json` exists next to `app.html`.

Use `app-config.example.json` as the shape:

```json
{
  "apiBaseUrl": "https://api.getaudo.com"
}
```

Without `app-config.json`, the console stays in local/demo mode. With the checked-in production `app-config.json`, the console calls `https://api.getaudo.com`.

## Backend

The trusted API lives in `control-plane/`. It handles authenticated site records, Cloudflare DNS provisioning, publishing, backups, GitHub/Coolify handoff, and Stripe checkout.

See `control-plane/README.md` for runtime configuration and API routes. See `PLATFORM_ARCHITECTURE.md` for the broader platform plan.
