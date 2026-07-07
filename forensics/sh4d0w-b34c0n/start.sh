#!/bin/bash
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

export FLAG="$FLAG_VALUE"

python /app/src/gen_challenge.py "seed-$(echo $FLAG_VALUE | md5sum | cut -c1-8)" /app/beacon_capture.pcap

exec gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 --chdir /app/src serve:app 2>/dev/null || exec python /app/src/serve.py
