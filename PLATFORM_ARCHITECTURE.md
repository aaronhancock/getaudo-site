# Audo Hosting Platform Architecture

## Product Rules

- Free sites publish as `<site>.getaudo.com`.
- Free DIY sites are managed WordPress installs on a generated Audo subdomain and include Audo ad placement.
- Paid WordPress sites can use custom domains, backups, restore points, and no Audo ad placement.
- Done-for-you websites are paid project records that Audo plans, builds, and launches manually.
- Custom app hosting is a paid GitHub/Coolify lane for full apps, databases, workers, and operational support.
- Every website is modeled as its own site record, even when the underlying deployment is static.
- Subdomains that point to unique deployments are unique sites. Hostnames that point to the same deployment are aliases on one site.

## Frontend

The current console is a static SPA served by Nginx from this repo.

- `app.html`: Firebase Auth entry, site list, WordPress setup, project intake, domains, integrations, backups UI.
- `index.html`: public marketing site for `getaudo.com`.
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

Free DIY WordPress site:

1. Create Firestore site record.
2. Reserve `<slug>.getaudo.com`.
3. Add/confirm Cloudflare DNS record.
4. Create Coolify WordPress + MariaDB service from the Audo WordPress template.
5. Start service and let Traefik/Cloudflare terminate the public route.
6. Add event: `wordpress.provisioned`.

Paid WordPress custom-domain site:

1. Create domain record in Firestore.
2. Show required DNS records.
3. Verify CNAME/A record and certificate readiness.
4. Attach domain to the WordPress service.
5. Remove Audo ad banner.
6. Enable backup policy.

GitHub application site:

1. Create paid `github-app` site record.
2. User installs/connects the Audo GitHub App.
2. API receives installation ID and selected repo.
3. API creates Coolify app from repo, branch, build command, output directory, and environment.
4. GitHub webhook triggers deployments.
5. Deployment events write back to Firestore.

Done-for-you website:

1. Create paid `concierge` site record with a generated Audo subdomain.
2. Audo scopes the one-page site, full website, WordPress build, or custom implementation.
3. Audo provisions hosting manually, then attaches domains, backups, and monitoring.

## Backups

The existing server backup model should become site-aware for all Audo-created sites.

Backup policy by plan:

- Free: no customer restore points; platform keeps internal disaster recovery.
- Paid WordPress: WordPress files, database, domain config, deployment metadata, and selected restore points.
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
4. Managed WordPress provisioning through the Coolify template.
5. Stripe checkout for paid plan upgrades.
