#!/bin/sh
set -e

FLAG_VALUE="${GZCTF_FLAG:-$FLAG}"

if [ -z "$FLAG_VALUE" ]; then
    echo "WarCTF{missing_flag_contact_admin}" > /flag.txt
else
    printf '%s\n' "$FLAG_VALUE" > /flag.txt
fi

chmod 400 /flag.txt
chown ctf:ctf /flag.txt

unset GZCTF_FLAG FLAG

exec /usr/sbin/xinetd -dontfork
