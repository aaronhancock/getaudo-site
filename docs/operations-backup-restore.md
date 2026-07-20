# Audo website operations: backup and restore

## What is protected

The persistent `/data/audo` volume is the source of truth for website request,
booking, provider-retry, and client-provisioning state. The backup job copies
every top-level `*.sqlite3` database using SQLite's online backup API, verifies
database integrity, and writes SHA-256 checksums to a manifest.

Secrets are runtime configuration and are deliberately excluded. Keep Google,
HubSpot, and Notion credentials in the deployment secret store, not in the
data volume or backups.

## Daily backup

Production has a host-level `audo-backup.timer` scheduled for 2:15 AM Central
with a randomized delay of up to ten minutes. It runs
`/usr/local/sbin/audo-backup.sh`, which discovers the current Coolify container,
creates and verifies the in-container backup, then copies the verified snapshot
to `/data/backups/audo/<UTC timestamp>/` on the host.

The same reviewed units are versioned in `ops/`. To run the job manually:

```bash
systemctl start audo-backup.service
systemctl status audo-backup.service
systemctl list-timers audo-backup.timer
```

The underlying command inside the live application container is:

```bash
python /app/scripts/backup_audo_data.py --retention 14
```

Backups are stored in `/data/audo/backups/<UTC timestamp>/`. The container keeps
14 successful snapshots; the second same-host copy keeps 30 days. A failed run
never replaces a completed snapshot.

The second host path protects against a container or volume mistake, but both
copies remain on the same host and disk. They do **not** protect against host
loss, theft, or disk failure. Do not describe the control as off-site or
encrypted until a separately owned destination and restore test are in place.

## Verify and perform a restore drill

Use the latest timestamped folder and restore only to a test directory:

```bash
python /app/scripts/verify_audo_backup.py \
  /data/audo/backups/<UTC timestamp> \
  --restore-dir /tmp/audo-restore-drill
```

Success requires matching checksums and `PRAGMA integrity_check = ok` for every
database. Run this drill after deployment and at least quarterly.

## Production recovery

1. Stop or scale down the application so no requests can write to the database.
2. Run the verifier against the selected backup without `--restore-dir`.
3. Copy the current `/data/audo/*.sqlite3` files to a separately timestamped
   emergency folder.
4. Copy the verified backup databases into `/data/audo` with their original
   names and permissions.
5. Start the application and verify `/health`.
6. Submit one internal test request, confirm the owner email, confirm the
   HubSpot record, book a test slot, and then remove the test artifacts.
7. Review `retry` and `failed` rows before resuming normal operations.

The verifier intentionally refuses to restore directly over `/data/audo`.
Production replacement is a deliberate operator action after the application
is stopped; it must never be performed by an unattended job.

## Operational checks

Run the non-PII status summary inside the application container:

```bash
python /app/scripts/check_audo_operations.py

# After Closed Won provisioning is enabled:
python /app/scripts/check_audo_operations.py --expect-provisioning
```

The command exits with status `2` when it finds a terminal provider or
provisioning failure. It reports only grouped status counts; it never prints a
client name, email address, message, appointment, provider ID, or URL.

- `consultation_requests.email_status` should normally be `sent`.
- `consultation_requests.hubspot_status` should normally be `synced`.
- `consultation_bookings.status` should be `confirmed` for completed bookings.
- `client_provisioning_jobs.status` should be `completed` for processed Closed
  Won deals.
- Investigate a terminal `failed` state before replaying it; repeated retries
  without correcting credentials, permissions, or provider availability hide
  the real problem.
- Email delivery is at-least-once. A stable Message-ID is reused on retries so
  Gmail can recognize a replay, but an owner notification can still be
  duplicated if the process stops after provider acceptance and before the
  database status update.
