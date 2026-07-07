#!/bin/bash
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
  FLAG_VALUE="WarCTF{fallback_flag_not_configured}"
fi

export FLAG="$FLAG_VALUE"

# Generate the PCAP with the dynamic flag
python /app/src/gen_challenge.py "seed-$(echo $FLAG_VALUE | md5sum | cut -c1-8)" /app/capture.pcap

# Serve via a simple Flask file server
exec python /app/src/serve.py
