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
echo "[*] Starting OAuth Confusion challenge..."

# Run both servers via Python
exec python -m src.main
