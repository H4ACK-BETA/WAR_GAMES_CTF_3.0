#!/bin/bash
set -e

# Read flag from GZCTF or FLAG env var
FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  echo "WARNING: No flag provided via env, using fallback" >&2
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

# Write to /flag for the gRPC service to read
echo "$FLAG_VALUE" > /flag
chmod 444 /flag

echo "[*] Flag configured"
echo "[*] Starting API Playground..."

# Launch uvicorn (which also starts gRPC in a thread)
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --log-level info
