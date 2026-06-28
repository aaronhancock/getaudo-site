# GetAudo Site

Public consulting marketing site for `getaudo.com` plus a separate client portal and trusted control-plane API at `/app`.

The public site now positions GetAudo as a personal consulting company for:

- Life and business automation
- AI coaching, training, and support
- Ongoing website or web application management
- Website or web application creation with ongoing support
- Product consulting, brainstorming, and strategic innovation

The client portal currently includes:

- Firebase Auth wiring with local preview auth fallback
- Self-service site creation
- Free DIY managed WordPress on a generated `*.getaudo.com` subdomain
- Paid managed WordPress with custom-domain and backup gates
- Done-for-you website project records for manual Audo builds
- Custom app/GitHub hosting records for paid application hosting
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

The production Firebase project is `getaudo`. Email/password auth and Google sign-in are enabled.

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

## WordPress Template

The Audo-managed WordPress scaffold lives in `wordpress-template/`. It includes a Coolify-ready WordPress/MariaDB compose file, an always-on Audo MU-plugin for plan/ad controls, and a clean starter theme.
