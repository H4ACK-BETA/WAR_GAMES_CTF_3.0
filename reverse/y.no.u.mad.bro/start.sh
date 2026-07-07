#!/bin/bash
set -e
FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"
if [ -z "$FLAG_VALUE" ]; then
  echo "ERROR: No flag provided" >&2
  FLAG_VALUE="flag{fallback_error}"
fi
echo "$FLAG_VALUE" > /flag
chmod 440 /flag
chown root:ctf /flag
exec /usr/sbin/xinetd -dontfork -f /etc/xinetd.conf
