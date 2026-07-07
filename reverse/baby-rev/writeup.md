# b4by::r3v — Writeup

**Category:** Reverse Engineering  
**Difficulty:** Easy  
**Flag:** `WarCTF{dynamic_per_team}`

---

## Overview

The binary asks for a 6-character password. The password is stored as an encoded byte array, shifted by a constant key. Reverse the encoding to recover the password.

---

## Step 1: Initial Recon

```bash
$ file challenge
challenge: ELF 64-bit LSB executable, x86-64, statically linked, stripped

$ ./challenge
Enter password: test
Wrong! Try harder.
```

The binary is stripped — no symbol names. Let's open it in Ghidra.

---

## Step 2: Static Analysis (Ghidra)

Load the binary in Ghidra. Find `main` by looking for the entry point or searching for the string "Enter password:".

The decompiled main logic looks roughly like:

```c
char secret[] = {0x51, 0x57, 0x51, 0x52, 0x50, 0x58};
int KEY = 0x20;

// Read input
fgets(input, 128, stdin);

// Check length == 6
if (strlen(input) != 6) → fail

// Verify
for (i = 0; i < 6; i++) {
    if ((input[i] + KEY) != secret[i]) → fail
}

// Success → read /flag
```

**Key observations:**
- `secret` = `{0x51, 0x57, 0x51, 0x52, 0x50, 0x58}`
- `KEY` = `0x20`
- Validation: `input[i] + 0x20 == secret[i]`

---

## Step 3: Solve the Math

To find the password:

```
password[i] = secret[i] - KEY
password[i] = secret[i] - 0x20
```

Calculate:
```
0x51 - 0x20 = 0x31 = '1'
0x57 - 0x20 = 0x37 = '7'
0x51 - 0x20 = 0x31 = '1'
0x52 - 0x20 = 0x32 = '2'
0x50 - 0x20 = 0x30 = '0'
0x58 - 0x20 = 0x38 = '8'
```

**Password: `171208`**

---

## Step 4: Get the Flag

```bash
$ nc <host> 9999

  ____        _
 | __ )  __ _| |__  _   _       _ __ _____   __
 |  _ \ / _` | '_ \| | | |_____| '__/ _ \ \ / /
 | |_) | (_| | |_) | |_| |_____| | |  __/\ V /
 |____/ \__,_|_.__/ \__, |     |_|  \___| \_/
                    |___/

        Author: H3xPh4r04h

   I hid a secret in this binary...
   Can you find the password?

Enter password: 171208
Correct! Here is your flag:
WarCTF{...}
```

---

## Alternative Solve Methods

### Method 1: Python one-liner

```python
secret = [0x51, 0x57, 0x51, 0x52, 0x50, 0x58]
print(''.join(chr(b - 0x20) for b in secret))
```

### Method 2: strings + educated guess

```bash
$ strings challenge | grep -i password
Enter password:

$ hexdump -C challenge | grep -A1 "51 57 51"
# Find the byte array in .rodata
```

### Method 3: ltrace (if not stripped)

```bash
$ ltrace ./challenge <<< "171208"
fgets("171208\n", 128, 0x...)
strlen("171208") = 6
fopen("/flag", "r") = 0x...
```

### Method 4: GDB

```bash
$ gdb ./challenge
(gdb) break *main+200   # after the comparison loop
(gdb) run <<< "AAAAAA"
(gdb) x/6bx $rdi        # examine the secret array
```

---

## Why It's Easy

| Aspect | Reasoning |
|--------|-----------|
| Encoding | Simple addition (char + constant), not crypto |
| Key | Single byte, visible as an immediate in disassembly |
| Secret | Stored as a global array, easy to find in .rodata |
| Length | Only 6 characters — trivially brute-forceable too |
| No obfuscation | Straight comparison loop, no anti-debug |

This is designed as a first reverse engineering challenge. The goal is to teach:
- Loading binaries in Ghidra/IDA
- Reading decompiled code
- Identifying encoding schemes
- Solving simple byte arithmetic

---

## Tools Used

- **Ghidra** — decompilation + finding the secret array
- **Python** — computing the password
- **netcat** — connecting to the remote service
