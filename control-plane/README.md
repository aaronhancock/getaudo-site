# Audo Control Plane

Backend API for Audo self-service hosting.

## What It Does

- Authenticates users with Firebase ID tokens in production.
- Stores site records in Firestore in production and memory locally.
- Creates free builder sites on `*.getaudo.com`.
- Provisions per-site Cloudflare DNS records through the Cloudflare API.
- Publishes one-page builder output to a local artifact directory.
- Gates custom domains, backups, and GitHub application hosting to paid plans.
- Calls optional Coolify, backup, and Stripe integrations when configured.

## Local Development

```bash
npm install
npm run dev
```

Local defaults use preview auth and in-memory storage. Send `x-audo-preview-user` to simulate a user.

## Test

```bash
npm test
npm run build
```

## Required Production Env

```bash
NODE_ENV=production
AUTH_MODE=firebase
STORE_MODE=firestore
FIREBASE_SERVICE_ACCOUNT_JSON=<service-account-json>
AUDO_FREE_DOMAIN=getaudo.com
CLOUDFLARE_API_TOKEN=<cloudflare-api-token>
CLOUDFLARE_ACCOUNT_ID=<cloudflare-account-id>
CLOUDFLARE_ZONE_NAME=getaudo.com
CLOUDFLARE_FREE_SITE_TARGET=getaudo.com
```

`CLOUDFLARE_ZONE_ID` is optional. If it is not set, the control plane looks up the zone by `CLOUDFLARE_ZONE_NAME` and `CLOUDFLARE_ACCOUNT_ID`.

## API Summary

- `GET /health`
- `GET /api/me`
- `GET /api/dns/cloudflare/status`
- `GET /api/sites`
- `POST /api/sites`
- `GET /api/sites/:siteId`
- `PATCH /api/sites/:siteId`
- `POST /api/sites/:siteId/dns/free-subdomain`
- `POST /api/sites/:siteId/domains`
- `POST /api/sites/:siteId/publish`
- `POST /api/sites/:siteId/github`
- `POST /api/sites/:siteId/backups`
- `POST /api/sites/:siteId/checkout`
- `GET /api/sites/:siteId/events`

## Cloudflare DNS Behavior

For a free site with slug `acme`, the API creates or updates:

```text
CNAME acme.getaudo.com -> getaudo.com
```

If `CLOUDFLARE_ORIGIN_IPV4` is set instead of `CLOUDFLARE_FREE_SITE_TARGET`, it creates an `A` record.

Custom domains return DNS instructions for the user to configure at their own DNS provider. They are not automatically changed unless the domain is inside the managed Cloudflare zone.
