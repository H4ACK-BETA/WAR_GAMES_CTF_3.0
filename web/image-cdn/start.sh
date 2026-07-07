#!/bin/bash
set -e

# Read flag from GZCTF or FLAG env var
FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  echo "WARNING: No flag provided via env, using fallback" >&2
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

# Write to /flag
echo "$FLAG_VALUE" > /flag
chmod 444 /flag

echo "[*] Flag configured"

# Start internal metadata service (background)
echo "[*] Starting metadata service on 127.0.0.1:8888..."
python /app/metadata-service/server.py &

# Start the Flask app via gunicorn
echo "[*] Starting Image CDN on 0.0.0.0:8080..."
exec gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 60 --chdir /app/src app:app
