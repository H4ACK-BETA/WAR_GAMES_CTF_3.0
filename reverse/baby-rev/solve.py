#!/usr/bin/env python3
import sys

enc = [0x35, 0x2a, 0x3f, 0x34, 0x05,
       0x29, 0x3f, 0x29, 0x3b, 0x37,
       0x3f, 0x05, 0x6e, 0x68]
KEY = 0x5A

password = bytes(b ^ KEY for b in enc)
print(f"[*] password: {password.decode()!r}")

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

try:
    from pwn import remote, context
    context.log_level = "warning"
    r = remote(HOST, PORT)
    r.recvuntil(b"Password: ")
    r.sendline(password)
    print(r.recvall(timeout=3).decode())
except ImportError:
    import socket, time
    s = socket.socket()
    s.connect((HOST, PORT))
    data = b""
    while b"Password: " not in data:
        data += s.recv(4096)
    s.sendall(password + b"\n")
    time.sleep(0.5)
    print(s.recv(4096).decode())
    s.close()
