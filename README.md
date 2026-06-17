# Audo Site

Static SaaS console MVP for `getaudo.com`.

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

If `firebase-config.json` is absent, the app runs with local preview auth so the console can be developed without blocking on Firebase setup.

## Backend

The frontend can collect setup intent, builder content, domains, and GitHub settings. Real provisioning needs a trusted backend API because DNS, Coolify, GitHub, Stripe, and backups require secrets.

See `PLATFORM_ARCHITECTURE.md` for the proposed control-plane shape.
