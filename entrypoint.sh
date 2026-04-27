#!/bin/bash
set -e

mkdir -p /data
ln -sf /usr/share/zoneinfo/Europe/Madrid /etc/localtime
echo "Europe/Madrid" > /etc/timezone

echo "[entrypoint] starting supercronic at $(date)"
echo "[entrypoint] data dir contents:"
ls -la /data || true

exec /usr/local/bin/supercronic -passthrough-logs /app/crontab