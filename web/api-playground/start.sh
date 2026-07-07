#!/bin/bash
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

echo "$FLAG_VALUE" > /flag
chmod 444 /flag

exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --log-level info
