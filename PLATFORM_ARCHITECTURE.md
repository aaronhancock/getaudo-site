# Audo Hosting Platform Architecture

## Product Rules

- Free sites publish as `<site>.getaudo.com`.
- Free sites are one-page builder sites and include an Audo ad banner.
- Paid sites can use custom domains, backups, GitHub deployments, and full app hosting.
- Every website is modeled as its own site record, even when the underlying deployment is static.
- Subdomains that point to unique deployments are unique sites. Hostnames that point to the same deployment are aliases on one site.

## Frontend

The current console is a static SPA served by Nginx from this repo.

- `index.html`: Firebase Auth entry, site list, builder, domains, integrations, backups UI.
- `assets/audo-logo.svg`: Audo app logo and favicon.
- `firebase-config.json`: optional production Firebase web config, copied into the container when present.

Firebase config is public web-app configuration. Secrets must not be placed in this frontend.

## Firebase

Use Firebase Auth for account identity.

Recommended providers:

- Email/password for basic accounts.
- Google provider for fast onboarding.
- GitHub provider only for identity if desired; GitHub repository access should use a GitHub App.

Recommended Firestore collections:

```text
users/{uid}
teams/{teamId}
teams/{teamId}/members/{uid}
sites/{siteId}
sites/{siteId}/domains/{domainId}
sites/{siteId}/deployments/{deploymentId}
sites/{siteId}/backups/{backupId}
sites/{siteId}/events/{eventId}
```

Recommended custom claims:

```json
{
  "teamIds": ["team_123"],
  "role": "owner",
  "audoAdmin": false
}
```

## Backend API

Provisioning needs a trusted API because it uses Cloudflare, Coolify, GitHub, and backup credentials.

Suggested service name: `audo-control-plane`.

Minimum endpoints:

```text
POST /api/sites
PATCH /api/sites/:siteId
POST /api/sites/:siteId/publish
POST /api/sites/:siteId/domains
POST /api/sites/:siteId/github/installations
POST /api/sites/:siteId/backups
GET /api/sites/:siteId/events
```

Authentication:

- Frontend sends Firebase ID token.
- API verifies the token with Firebase Admin SDK.
- API checks Firestore ownership and plan before every action.

## Provisioning Flow

Free one-page builder site:

1. Create Firestore site record.
2. Reserve `<slug>.getaudo.com`.
3. Render builder JSON to static HTML/CSS.
4. Store rendered artifact in the site deployment store.
5. Create or update a Coolify static app, or route the subdomain to a shared static renderer.
6. Add/confirm Cloudflare DNS wildcard or subdomain record.
7. Add event: `published`.

Paid custom-domain site:

1. Create domain record in Firestore.
2. Show required DNS records.
3. Verify CNAME/A record and certificate readiness.
4. Attach domain to the Coolify app.
5. Remove Audo ad banner.
6. Enable backup policy.

GitHub application site:

1. User installs the Audo GitHub App.
2. API receives installation ID and selected repo.
3. API creates Coolify app from repo, branch, build command, output directory, and environment.
4. GitHub webhook triggers deployments.
5. Deployment events write back to Firestore.

## Backups

The existing server backup model should become site-aware for all Audo-created sites.

Backup policy by plan:

- Free: no customer restore points; platform keeps internal disaster recovery.
- Paid static/builder: rendered artifact, builder JSON, domain config, deployment metadata.
- Paid app: repo metadata, environment metadata, container inspect, app config, volumes, databases when attached.

Backups should write status to both:

- Server-local backup status files for the kiosk dashboard.
- Firestore `sites/{siteId}/backups/{backupId}` for the customer console.

## Required Secrets

Keep these only in the backend environment:

- Cloudflare API token.
- Coolify API token.
- GitHub App private key and webhook secret.
- Firebase Admin service account.
- Stripe secret key.
- Backup storage credentials.

## Next Backend Milestone

Build `audo-control-plane` with:

1. Firebase Admin token verification.
2. Firestore site CRUD.
3. Cloudflare subdomain creation under `getaudo.com`.
4. Builder JSON publishing to a static site container.
5. Stripe checkout for paid plan upgrades.
