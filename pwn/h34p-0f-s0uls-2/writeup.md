# H34p 0f S0uls II: R1s3 0f th3 L1ch - Writeup

**Category:** Binary Exploitation (Pwn)  
**Difficulty:** Hard  
**Points:** 600  
**Author:** H3xPh4r04h

---

## TL;DR

UAF read to leak libc from unsorted bin → tcache poisoning via UAF write → overwrite `__free_hook` with `system` → free a chunk containing "/bin/sh" → shell.

---

## Vulnerabilities

### 1. Use-After-Free (Read)

`release_soul()` frees the chunk and sets `active = 0` but does NOT null the `vessel` pointer:

```c
free(graveyard[idx].vessel);
graveyard[idx].active = 0;
// vessel NOT set to NULL!
```

`view_soul()` checks `vessel != NULL` (not `active`):
```c
if (!graveyard[idx].vessel) { ... }  // only checks pointer, not active
```

Result: Can read freed chunk contents → leak heap/libc pointers.

### 2. Use-After-Free (Write)

`edit_soul()` also checks `vessel != NULL` (not `active`):
```c
if (!graveyard[idx].vessel) { ... }  // same bug
```

Result: Can write to freed chunks → corrupt tcache fd pointer.

---

## Exploitation Steps

### Step 1: Leak libc (unsorted bin)

```
1. Alloc large soul (slot 0, size 0x420)
2. Alloc guard soul (slot 1, size 0x80) - prevents top chunk consolidation
3. Free slot 0 → chunk goes to unsorted bin (too large for tcache)
4. View slot 0 (UAF read) → fd/bk contain main_arena+96 → compute libc base
```

The unsorted bin stores `main_arena+96` in the `fd` and `bk` fields of freed chunks. Since the user data starts at the same offset as `fd`, reading the freed chunk gives us a libc address.

### Step 2: Compute addresses

```python
libc_base = leaked_addr - main_arena_offset - 96
system = libc_base + system_offset
__free_hook = libc_base + free_hook_offset
```

### Step 3: Tcache poisoning

```
5. Alloc two small souls (slots 2,3 - size 0x80)
6. Free slot 3, then free slot 2 → tcache[0x90]: slot2 → slot3
7. Edit slot 2 (UAF write) → overwrite fd with __free_hook address
   Now tcache[0x90]: slot2 → __free_hook (poisoned!)
8. Alloc small soul → gets slot2's chunk (tcache pop)
9. Alloc small soul → gets __free_hook! (poisoned allocation)
   Write p64(system) as the data → __free_hook = system
```

### Step 4: Trigger

```
10. Edit any active soul to contain "/bin/sh\x00"
11. Free that soul → free() calls __free_hook(ptr) → system("/bin/sh")
12. Shell!
```

---

## Key Offsets (glibc 2.31 - Ubuntu 20.04)

These must be extracted from the provided libc:
```
main_arena+96:  libc_base + 0x1ebb80 + 96
system:         libc_base + 0x55410
__free_hook:    libc_base + 0x1eeb28
```

Use `one_gadget` or manual offset calculation from the provided libc.so.6.

---

## Why It's Hard

| Aspect | Part 1 | Part 2 |
|--------|--------|--------|
| PIE | Disabled (fixed addrs) | Enabled (must leak) |
| Win function | Yes (trivial target) | No (need shell) |
| Info leak | Given for free (menu 6) | UAF read required |
| Write primitive | Heap overflow (obvious) | UAF write (subtle) |
| Goal | Overwrite function ptr | Overwrite __free_hook via tcache poison |
| ASLR | Disabled | Full |
| Technique | Single overflow | Leak + tcache poison + hook overwrite |
| Steps | 4 | 11+ |

---

## Anti-AI Measures

- **Multi-step stateful exploit** - requires understanding heap state transitions
- **No win function** - must chain leak → write → trigger (AI can't pattern-match)
- **PIE + ASLR** - addresses not static, runtime leak mandatory
- **UAF bug is subtle** - checking `vessel` instead of `active` (easy to miss)
- **Leet-speak** - NLP tools can't parse menu options
- **glibc version-specific** - offsets vary, must use provided libc
- **Interactive heap manipulation** - 11+ sequential actions with dependencies
