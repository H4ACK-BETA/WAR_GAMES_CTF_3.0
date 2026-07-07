#!/usr/bin/env python3
"""
Pharaoh's Cipher - Solver
Author: H3xPh4r04h

The challenge is a custom VM ("Underworld") with Egyptian-themed opcode names.
The bytecode is triple-encrypted (rolling XOR + LFSR).

Solving requires:
1. Identify the two decryption layers in the binary:
   - Layer 1: Rolling XOR (seed=0xAA, step=+0x33 per byte)
   - Layer 2: 16-bit Galois LFSR (poly=0xB400, seed=0xACE1)
2. Dump and decrypt the bytecode after build_bytecode() runs
3. Reverse the VM dispatcher (opcodes are misleadingly named)
4. Identify the REAL verification path (skip dead code after WANDER/JMP)
5. Understand the subroutine:
     encoded[i] = input[i] ^ rot_key[i] ^ (i * 0x11 + 0x07)
6. Extract rot_keys from mem[0x80..0x87] and expected from mem[0x90..0x97]
7. Solve: password[i] = expected[i] ^ rot_key[i] ^ derived[i]

BEWARE:
- Fake passwords in .rodata ("Ank4Ra_X9", "K1ngTut!", "Py4m1dz", "N3fert1t")
- Dead code block uses false_tablets[] with XOR key 0x41 (wrong path)
- Opaque predicates (seal_of_ra) always route to real path
- SPHINX opcode corrupts tail bytes (self-modifying code)
"""
import sys

# Real values extracted from bytecode analysis
rot_keys = [0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE]
expected = [0x8F, 0x84, 0xE5, 0xA1, 0xF4, 0x96, 0xBB, 0x8D]

password = bytes(
    expected[i] ^ rot_keys[i] ^ ((i * 0x11 + 0x07) & 0xFF)
    for i in range(8)
)
print(f"[*] Password: {password.decode()!r}")

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

try:
    from pwn import remote, context
    context.log_level = "warning"
    r = remote(HOST, PORT)
    r.recvuntil(b"ancient word: ")
    r.sendline(password)
    print(r.recvall(timeout=3).decode())
except ImportError:
    import socket
    import time
    s = socket.socket()
    s.connect((HOST, PORT))
    data = b""
    while b"ancient word: " not in data:
        data += s.recv(4096)
    s.sendall(password + b"\n")
    time.sleep(0.5)
    print(s.recv(4096).decode())
    s.close()
