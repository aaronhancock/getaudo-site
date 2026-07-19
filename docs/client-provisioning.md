# Closed Won client provisioning

> Deployment status: the reconciliation code and tests are present, and the
> business-owned Drive source and destination folders exist. Keep the production
> worker disabled until the Notion integration is authorized and shared, the
> activation cutoff is set, and one clearly labeled test deal passes the full
> Drive + Notion + HubSpot verification below.

## Purpose

`scripts/reconcile_closed_won.py` turns **HubSpot Closed Won deals** into an
organized Audo client workspace. It never triggers from a raw contact or a new
website inquiry. The job polls HubSpot, creates one client folder in the Audo
Google Drive from a configurable template, optionally creates one Notion
project, and writes the resulting links back to the HubSpot deal.

The implementation uses existing HubSpot, Google Workspace, and optional
Notion accounts. It does not require a paid automation service.

## Safety and idempotency

- `--dry-run` performs discovery only and makes no HubSpot, Drive, Notion, or
  local database writes.
- HubSpot is queried only for the configured pipeline and Closed Won stage.
- A Drive folder is tagged with the HubSpot deal ID and searched before create.
- A Notion project is searched by HubSpot deal ID before create.
- Resource IDs and URLs are saved locally before HubSpot is updated, allowing a
  retry to resume after a partial provider outage.
- Completed HubSpot deals and completed local jobs are skipped.
- Errors use bounded exponential retry and become operator-review failures
  after the configured attempt count.

## Google authorization

Use a dedicated offline Google OAuth grant owned by `aaron@getaudo.com` with:

```text
https://www.googleapis.com/auth/drive
```

Do not reuse the scheduler refresh token unless it has explicitly been
reauthorized with Drive scope. Keep refresh tokens only in runtime secret
storage.

Create a separate Drive-only grant with the bundled OAuth helper:

```bash
python3 scripts/google_calendar_oauth.py \
  --client-file .secrets/audo-drive-oauth-client.json \
  --output .secrets/audo-drive-oauth.json \
  --scope https://www.googleapis.com/auth/drive
```

The `.secrets` directory is ignored by Git. Both credential files must remain
mode `0600` and must never be copied into Drive, Notion, HubSpot, or deployment
documentation.

## Required environment

```bash
HUBSPOT_SERVICE_KEY=<private-app-token>
HUBSPOT_PORTAL_ID=<numeric-account-id>
HUBSPOT_PIPELINE=default
HUBSPOT_CLOSED_WON_STAGE=closedwon
CLIENT_PROVISIONING_ACTIVATION_AFTER=2026-07-19T00:00:00Z

PROVISIONING_GOOGLE_CLIENT_ID=<oauth-client-id>
PROVISIONING_GOOGLE_CLIENT_SECRET=<oauth-client-secret-if-required>
PROVISIONING_GOOGLE_REFRESH_TOKEN=<offline-token-with-drive-scope>
DRIVE_CLIENTS_PARENT_FOLDER_ID=<business-clients-folder-id>
DRIVE_CLIENT_TEMPLATE_FOLDER_ID=<client-template-folder-id>
```

The HubSpot private app needs read/write access to deals and deal properties.
The Google identity needs access to both Drive folders.

`CLIENT_PROVISIONING_ACTIVATION_AFTER` is required for writes and limits the
worker to deals closed at or after that timestamp. This prevents an activation
from unexpectedly provisioning every historical Closed Won deal. A deliberate
backfill can instead set `CLIENT_PROVISIONING_ALLOW_HISTORICAL=true`, but only
after a dry-run count has been reviewed.

## HubSpot link properties

By default, the first non-dry run creates these deal properties if missing:

- `audo_provisioning_status`
- `audo_drive_folder_url`
- `audo_notion_project_url`
- `audo_provisioned_at`

Set `HUBSPOT_ENSURE_PROVISIONING_PROPERTIES=false` when an administrator will
create and manage the properties manually. Every property name is configurable:

```bash
HUBSPOT_PROVISIONING_STATUS_PROPERTY=audo_provisioning_status
HUBSPOT_DRIVE_FOLDER_URL_PROPERTY=audo_drive_folder_url
HUBSPOT_NOTION_PROJECT_URL_PROPERTY=audo_notion_project_url
HUBSPOT_PROVISIONED_AT_PROPERTY=audo_provisioned_at
```

## Optional Notion project

The Notion integration must be shared with the target projects database. The
database needs these property types: title, rich text, URL, URL, and select.
New Closed Won projects are created in the `Planning` stage.

The live Audo Projects database also includes `Client`, `Engagement Type`,
`Health`, and `Next Milestone` for owner review. The automated minimum is the
deal ID/link, client folder link, title, and stage; Aaron fills the business
context during the onboarding review rather than guessing from a deal name.

```bash
NOTION_PROVISIONING_ENABLED=true
NOTION_API_TOKEN=<integration-secret>
NOTION_PROJECTS_DATABASE_ID=<database-id>
NOTION_PROJECT_TITLE_PROPERTY=Name
NOTION_HUBSPOT_DEAL_ID_PROPERTY=HubSpot Deal ID
NOTION_DRIVE_FOLDER_PROPERTY=Client Folder
NOTION_HUBSPOT_DEAL_URL_PROPERTY=HubSpot Deal
NOTION_PROJECT_STATUS_PROPERTY=Stage
```

If Audo keeps project delivery in Google Workspace only, leave
`NOTION_PROVISIONING_ENABLED=false`.

## Local state and retry settings

```bash
CLIENT_PROVISIONING_DATABASE_PATH=/data/audo/client-provisioning.sqlite3
CLIENT_PROVISIONING_MAX_ATTEMPTS=6
CLIENT_PROVISIONING_RETRY_BASE_SECONDS=60
CLIENT_PROVISIONING_ENABLED=false
CLIENT_PROVISIONING_POLL_SECONDS=300
DRIVE_CLIENT_FOLDER_SUFFIX=" — Audo Client"
```

Keep the database on the same backed-up persistent volume as the inquiry
database. It contains provider IDs, URLs, status, timestamps, and errors, but no
provider secrets.

The reconciler uses a non-blocking file lock. Never run the embedded worker and
a manual reconciliation at the same time; a second process exits instead of
creating duplicate resources.

## Runbook

Start with a read-only pass:

```bash
python3 scripts/reconcile_closed_won.py --dry-run
```

Run one production reconciliation pass:

```bash
python3 scripts/reconcile_closed_won.py
```

Run as a supervised polling worker:

```bash
python3 scripts/reconcile_closed_won.py --forever --poll-seconds 300
```

Before enabling the worker, close a sandbox/test deal, inspect the dry-run
count, set the activation cutoff, run one real pass, verify the copied Drive
contents, the Notion project, and both HubSpot links, then run a second pass to
prove it creates nothing else. Archive the test workspace afterward. Monitor
the worker's JSON output and review
terminal `failed` rows in `client_provisioning_jobs`. After correcting the
underlying configuration or provider issue, explicitly replay one failed deal:

```bash
python3 scripts/reconcile_closed_won.py --retry-failed <hubspot-deal-id>
```
