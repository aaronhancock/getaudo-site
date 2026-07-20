#!/bin/sh
set -eu

container=$(docker ps --filter name=p1788q58ir5nebku23ml3bjh --format '{{.Names}}' | head -1)
[ -n "$container" ]

docker exec "$container" python /app/scripts/backup_audo_data.py \
  --data-dir /data/audo \
  --backup-dir /data/audo/backups \
  --retention 14

latest=$(docker exec "$container" sh -lc \
  'find /data/audo/backups -mindepth 1 -maxdepth 1 -type d | sort | tail -1')
docker exec "$container" python /app/scripts/verify_audo_backup.py "$latest"

stamp=$(basename "$latest")
target="/data/backups/audo/$stamp"
mkdir -p "$target"
docker cp "$container:$latest/." "$target/"

# This is a second copy on the same host, not an off-site backup.
find /data/backups/audo -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +
