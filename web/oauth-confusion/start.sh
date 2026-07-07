#!/bin/bash
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

echo "$FLAG_VALUE" > /flag
chmod 444 /flag

exec python -m src.main
