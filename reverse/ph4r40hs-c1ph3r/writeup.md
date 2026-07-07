# Ph4r40h's C1ph3r — Writeup

**Category:** Reverse Engineering  
**Difficulty:** Hard  
**Points:** 500  
**Author:** H3xPh4r04h  
**Flag:** `WarCTF{...}` (dynamic)  
**Password:** `V1rtu4lM`

---

## TL;DR

Custom VM challenge with triple-encrypted bytecode, misleading opcode names, fake passwords in `.rodata`, dead code paths, and self-modifying instructions. The actual password verification uses a multi-layer XOR scheme: `input[i] ^ rot_key[i] ^ (i * 0x11 + 0x07) == expected[i]`.

---

## Step 1: Initial Recon

```bash
file challenge
# ELF 64-bit LSB pie executable, x86-64, stripped

strings challenge | grep -i pass
# Ank4Ra_X9
# K1ngTut!
# Py4m1dz
# N3fert1t
```

These are ALL fake passwords planted as red herrings. None of them work.

Running the binary shows it expects an 8-character input:
```
>>> Sp34k th3 4nc13nt w0rd: AAAAAAAA
C0ND3MN3D
```

---

## Step 2: Static Analysis (Ghidra/IDA)

Load the stripped binary. Key observations:

1. **No static bytecode blob** — the program constructs bytecode at runtime via `inscribe_codex()` then encrypts it, then decrypts it before execution.

2. **Two decryption layers** are visible:
   - `layer1_decrypt()`: Rolling XOR with seed `0xAA`, incrementing by `0x33` each byte
   - `layer2_decrypt()`: 16-bit Galois LFSR with polynomial `0xB400` and seed `0xACE1`

3. **Opaque predicate** — function `seal_of_ra(n)` computes `((n*n + n) & 1) == 0` which is ALWAYS true (n^2 + n is always even). This gates the real decryption path. The else-branch (copying `cursed_scroll`) is dead code.

4. **VM dispatcher** — a large switch statement with cases like `0x10`, `0x11`, `0x20`, etc. The struct fields have misleading names (`thoth` = program counter, `maat` = zero flag, `ka` = registers, `duat` = memory, etc.)

---

## Step 3: Reverse the VM ISA

By analyzing the switch cases:

| Opcode | Name in Binary | Real Operation |
|--------|---------------|----------------|
| 0x10 | ENGRAVE | MOV reg, imm8 |
| 0x11 | EXCAVATE | MOV reg, reg |
| 0x20 | ENTOMB | LOAD reg, mem[imm8] |
| 0x21 | EXHUME | STORE mem[imm8], reg |
| 0x22 | SANDSTORM | LOAD reg, mem[reg] (indexed) |
| 0x30 | SCARAB | XOR reg, reg |
| 0x31 | ANKH | XOR reg, imm8 |
| 0x40 | WEIGH | CMP reg, imm8 |
| 0x41 | JUDGE | CMP reg, reg |
| 0x50 | CROSS | JNE addr |
| 0x51 | ASCEND | JE addr |
| 0x52 | WANDER | JMP addr |
| 0x60 | OFFER | ADD reg, imm8 |
| 0x70 | CURSE_OP | SUB reg, imm8 |
| 0x72 | MULTIPLY | MUL reg, imm8 |
| 0x80 | BURY | PUSH reg |
| 0x81 | RESURRECT | POP reg |
| 0x90 | SUMMON | CALL addr |
| 0x91 | BANISH | RET |
| 0xA0 | SPHINX | Self-modify (XOR tail bytes) |
| 0xE0 | ETERNAL | NOP |
| 0xFF | AFTERLIFE | HALT (success) |
| 0xFE | DEVOUR | FAIL |

---

## Step 4: Dump the Decrypted Bytecode

Easiest approach: set a breakpoint after both `layer2_decrypt` and `layer1_decrypt` calls complete, then dump the bytecode buffer (256 bytes).

In GDB:
```gdb
# Break after the second layer decrypt call
b *main+<offset_after_layer1_decrypt>
r <<< "AAAAAAAA"
x/256bx <address_of_g_codex>
```

Or use Frida/ltrace to hook the VM execution function and log every instruction.

---

## Step 5: Disassemble the Bytecode

The decrypted bytecode program does:

1. **Setup phase** (bytes 0x00-0x5F): Stores two tables into VM memory:
   - `mem[0x80..0x87]` = rotating keys: `[0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE]`
   - `mem[0x90..0x97]` = expected values: `[0x8F, 0x84, 0xE5, 0xA1, 0xF4, 0x96, 0xBB, 0x8D]`

2. **Dead code block** (skipped by JMP): A fake simple XOR-0x41 check against `false_tablets`. This never executes but confuses decompilers.

3. **Main loop** (R7 = 0..7): Calls a verification subroutine for each character.

4. **Subroutine** (the real check):
   ```
   R1 = mem[R7]              // input character
   R5 = R7 + 0x80
   R2 = mem[R5]              // rotating key
   R3 = R7 * 0x11 + 0x07    // derived key
   R1 ^= R2                  // input ^ rot_key
   R1 ^= R3                  // ^ derived_key
   R4 = mem[R7 + 0x90]       // expected value
   if R1 == R4: return 1
   else: return 0
   ```

5. **SPHINX opcode**: XORs random bytes in the NOP sled at the tail — irrelevant to correctness but corrupts memory dumps taken during execution.

---

## Step 6: Solve

The verification formula is:
```
input[i] ^ rot_key[i] ^ derived[i] == expected[i]
```

Therefore:
```
input[i] = expected[i] ^ rot_key[i] ^ derived[i]
```

Where `derived[i] = i * 0x11 + 0x07`.

```python
rot_keys = [0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE]
expected = [0x8F, 0x84, 0xE5, 0xA1, 0xF4, 0x96, 0xBB, 0x8D]

password = ""
for i in range(8):
    derived = (i * 0x11 + 0x07) & 0xFF
    password += chr(expected[i] ^ rot_keys[i] ^ derived)

print(password)  # V1rtu4lM
```

---

## Step 7: Get the Flag

```bash
echo 'V1rtu4lM' | nc <HOST> 9999
```

```
[SPH1NX] Judg1ng: ..oOOo.. 4CC3PT3D

  +=============================================+
  |   ankh Th3 Ph4r40h 4ckn0wl3dg3s y0u. ankh   |
  |   Y0u h4v3 sp0k3n th3 tru3 n4m3.          |
  +=============================================+

  [TR34SUR3] WarCTF{...}
```

---

## Pitfalls / Anti-AI Measures

| Trap | What happens if you fall for it |
|------|-------------------------------|
| Fake passwords in `.rodata` | `strings` shows `Ank4Ra_X9`, `K1ngTut!`, `Py4m1dz`, `N3fert1t` — all wrong |
| Dead code block | Simple XOR-0x41 check looks like the real algorithm but is skipped |
| Opaque predicate `seal_of_ra()` | The `else` branch (cursed_scroll) is unreachable but looks valid |
| SPHINX self-modify | Memory dumps taken mid-execution show corrupted bytecode |
| Egyptian-themed names | `SCARAB`=XOR, `ENTOMB`=LOAD — no semantic hints in decompiler output |
| Leet-speak UI | NLP solvers can't easily parse instructions for hints |
| Runtime bytecode construction | No static blob to extract without executing |

---

## Tools Used

- Ghidra / IDA Pro (static analysis of VM dispatcher)
- GDB (breakpoint after decryption to dump bytecode)
- Python (solve script)

---

## Solve Script

```python
#!/usr/bin/env python3
from pwn import remote, context

rot_keys = [0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE]
expected = [0x8F, 0x84, 0xE5, 0xA1, 0xF4, 0x96, 0xBB, 0x8D]

password = bytes(
    expected[i] ^ rot_keys[i] ^ ((i * 0x11 + 0x07) & 0xFF)
    for i in range(8)
)

context.log_level = "warning"
r = remote("127.0.0.1", 9999)
r.recvuntil(b"w0rd: ")
r.sendline(password)
print(r.recvall(timeout=3).decode())
```
