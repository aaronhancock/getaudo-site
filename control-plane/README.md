# Audo Control Plane

Backend API for Audo self-service hosting.

## What It Does

- Authenticates users with Firebase ID tokens in production.
- Stores site records in Firestore in production and memory locally.
- Creates free DIY WordPress sites on `*.getaudo.com`.
- Provisions per-site Cloudflare DNS records through the Cloudflare API.
- Keeps the legacy one-page builder renderer available for existing builder records.
- Gates custom domains, backups, done-for-you projects, and GitHub application hosting to paid plans.
- Calls optional Coolify, backup, and Stripe integrations when configured.
- Provisions free or paid WordPress sites as isolated Coolify services from the `wordpress-with-mariadb` Docker template.

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
AUDO_PREVIEW_API_SECRET=<set-this-if-auth-mode-is-preview>
STORE_MODE=firestore
FIREBASE_SERVICE_ACCOUNT_JSON=<service-account-json>
AUDO_FREE_DOMAIN=getaudo.com
CLOUDFLARE_API_TOKEN=<cloudflare-api-token>
CLOUDFLARE_ACCOUNT_ID=<cloudflare-account-id>
CLOUDFLARE_ZONE_NAME=getaudo.com
CLOUDFLARE_FREE_SITE_TARGET=<cloudflare-tunnel-id>.cfargotunnel.com
CLOUDFLARE_TUNNEL_ORIGIN_SERVICE=https://127.0.0.1:443
```

`CLOUDFLARE_ZONE_ID` is optional. If it is not set, the control plane looks up the zone by `CLOUDFLARE_ZONE_NAME` and `CLOUDFLARE_ACCOUNT_ID`. `CLOUDFLARE_TUNNEL_ID` is optional when `CLOUDFLARE_FREE_SITE_TARGET` is the tunnel hostname because the control plane can infer it.

If `AUTH_MODE=preview` is used on a public host, set `AUDO_PREVIEW_API_SECRET`. Requests must include `x-audo-preview-secret` or they will be rejected. Do not expose Cloudflare-write endpoints publicly with unrestricted preview auth.

## Managed WordPress

Free and paid WordPress sites use Coolify's Docker service template named `wordpress-with-mariadb`. Creating a WordPress site provisions DNS, adds an explicit Cloudflare Tunnel ingress rule, creates one Coolify service per Audo site, assigns the site's `https://<slug>.getaudo.com` URL to the `wordpress` container, starts the service, and submits the WordPress install form with Audo-generated admin credentials.

Free WordPress sites use a generated Audo subdomain and remain locked out of customer restore points, custom domains, and GitHub deployment controls. Paid WordPress sites can use custom domains and backup/restore points.

Required Coolify env:

```bash
COOLIFY_BASE_URL=http://coolify:8080
COOLIFY_API_TOKEN=<coolify-token-with-write-and-deploy-access>
COOLIFY_WORDPRESS_SERVICE_TYPE=wordpress-with-mariadb
COOLIFY_WORDPRESS_PROJECT_UUID=<coolify-project-uuid>
COOLIFY_WORDPRESS_ENVIRONMENT_NAME=production
COOLIFY_WORDPRESS_SERVER_UUID=<coolify-server-uuid>
COOLIFY_WORDPRESS_DESTINATION_UUID=<coolify-docker-destination-uuid>
COOLIFY_WORDPRESS_INSTANT_DEPLOY=true
COOLIFY_WORDPRESS_AUTO_INSTALL=true
COOLIFY_WORDPRESS_INSTALL_TIMEOUT_SECONDS=180
```

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
