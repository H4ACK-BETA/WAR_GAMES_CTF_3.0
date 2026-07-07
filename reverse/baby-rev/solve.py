#!/usr/bin/env python3
"""
Baby-rev solver
The binary stores the password as (char + 0x20).
To recover: password[i] = secret[i] - 0x20
"""
import sys

secret = [0x51, 0x57, 0x51, 0x52, 0x50, 0x58]
KEY = 0x20

password = bytes(b - KEY for b in secret)
print(f"[*] Password: {password.decode()!r}")

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

try:
    from pwn import remote, context
    context.log_level = "warning"
    r = remote(HOST, PORT)
    r.recvuntil(b"Enter password: ")
    r.sendline(password)
    print(r.recvall(timeout=3).decode())
except ImportError:
    import socket
    import time
    s = socket.socket()
    s.connect((HOST, PORT))
    data = b""
    while b"Enter password: " not in data:
        data += s.recv(4096)
    s.sendall(password + b"\n")
    time.sleep(0.5)
    print(s.recv(4096).decode())
    s.close()
