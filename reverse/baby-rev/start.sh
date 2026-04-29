#!/bin/bash
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"


if [ -z "$FLAG_VALUE" ]; then
  echo "ERROR: No flag provided" >&2
  FLAG_VALUE="WarCTF{fallback_error}"
fi

echo "$FLAG_VALUE" > /flag
chmod 444 /flag
chown root:root /flag

exec /usr/sbin/xinetd -dontfork -f /etc/xinetd.conf
