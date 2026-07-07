#!/bin/sh
# start.sh - matrix://root_access
#
# GZCTF-standard FLAG handling:
#   1. Capture GZCTF_FLAG into a file the binary can read.
#   2. Unset it from the shell's own environment before exec.
#   3. exec replaces this shell's process image, so /proc/self/environ
#      for the resulting process (xinetd, and every connection it
#      forks) no longer carries the flag at all.
#
# xinetd listens on the challenge port (see /etc/xinetd.d/ctf) and
# forks a fresh instance of the binary per incoming connection,
# running it as the unprivileged `ctf` user. This script itself runs
# once, as root, at container start, purely to stage the flag and
# hand off to xinetd -- it is not in the path of any single connection.

set -e

if [ -z "${GZCTF_FLAG}" ]; then
    echo "flag{missing_GZCTF_FLAG_env_var_contact_admin}" > /flag.txt
else
    printf '%s\n' "${GZCTF_FLAG}" > /flag.txt
fi

chmod 400 /flag.txt
chown ctf:ctf /flag.txt

# Remove the flag from this process's own environment before exec.
unset GZCTF_FLAG

# Uses the package's default /etc/xinetd.conf, which includes
# /etc/xinetd.d/ (see Dockerfile) where ctf.xinetd defines the
# challenge service on port 9999.
exec /usr/sbin/xinetd -dontfork
