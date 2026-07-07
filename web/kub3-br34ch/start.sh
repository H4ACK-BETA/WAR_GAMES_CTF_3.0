#!/bin/bash
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

echo "$FLAG_VALUE" > /flag
chmod 444 /flag

export FLAG="$FLAG_VALUE"

# Create fake ServiceAccount mount
mkdir -p /var/run/secrets/kubernetes.io/serviceaccount
python -c "
import json, base64, hashlib, os
seed = 'novacorp-prod'
token = 'eyJhbGciOiJSUzI1NiJ9.' + base64.urlsafe_b64encode(
    json.dumps({'sub': 'system:serviceaccount:production:frontend-sa', 'iss': 'kubernetes/serviceaccount'}).encode()
).decode().rstrip('=') + '.k8s_sig_' + hashlib.md5(seed.encode()).hexdigest()[:16]
with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'w') as f:
    f.write(token)
with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'w') as f:
    f.write('production')
with open('/var/run/secrets/kubernetes.io/serviceaccount/ca.crt', 'w') as f:
    f.write('-----BEGIN CERTIFICATE-----\nMIIC5zCCAc+gAwIBAgIBADANBgkq...(truncated)\n-----END CERTIFICATE-----\n')
"

# Create fake log files
mkdir -p /app/logs
echo "[2026-07-06 14:32:01] INFO: Frontend started on port 8080
[2026-07-06 14:32:02] INFO: Connected to redis-master-0.production.svc
[2026-07-06 14:32:03] INFO: Health check passed
[2026-07-06 14:35:12] WARN: Slow response from backend-api (1200ms)
[2026-07-06 14:40:00] INFO: Serving request from 10.244.0.1" > /app/logs/app.log

echo "[2026-07-06 02:00:01] backup-agent: starting nightly backup
[2026-07-06 02:00:05] backup-agent: secrets enumerated (5 items)
[2026-07-06 02:00:08] backup-agent: completed" > /app/logs/backup.log

# Start simulated K8s API
python /app/fake-k8s/api_server.py &

# Start Flask app
exec gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 60 --chdir /app/src app:app
