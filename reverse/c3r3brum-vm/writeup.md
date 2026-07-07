# c3r3brum::vm - Writeup

**Category:** Reverse Engineering  
**Difficulty:** Insane  
**Points:** 750  

---

## Overview

A custom virtual machine interprets encrypted bytecode that computes the flag. Players must reverse engineer the VM architecture, identify opcodes, decrypt the bytecode, and either write an emulator or trace the execution.

---

## Step 1: Initial Analysis

```bash
$ file cerebrum
ELF 64-bit LSB executable, x86-64, statically linked, stripped

$ ./cerebrum
[ CEREBRUM VM v1.0 ]
[ Decrypting bytecode... ]
[ Executing virtual program ]
[ Output: warCTF{...}
[ VM halted successfully ]
```

The binary prints the flag when run. But in the real challenge, it would require a key/input or only run on specific conditions. For analysis purposes, open in Ghidra.

---

## Step 2: Find the VM Dispatcher

In Ghidra, locate `main` (entry point). You'll see:
1. A call to a decrypt function (XORs a data blob with 0xC3)
2. A loop with a large switch statement (the VM dispatcher)
3. The switch has cases for each opcode

The dispatcher structure reveals the ISA:
- Fetch opcode byte
- Switch on opcode value
- Each case fetches operands and executes

---

## Step 3: Identify Key Opcodes

From the switch cases:

| Opcode | Mnemonic | Operands | Behavior |
|--------|----------|----------|----------|
| 0x00 | NOP | none | No operation |
| 0x10 | MOV_IMM | Rx, imm16 | Rx = immediate |
| 0x28 | ADD_IMM | Rx, imm8 | Rx += imm8 |
| 0x29 | XOR_IMM | Rx, imm8 | Rx ^= imm8 |
| 0x70 | PUTC | Rx | print(chr(Rx)) |
| 0xFF | HALT | none | Stop execution |

You only need these 5-6 opcodes to understand the flag computation.

---

## Step 4: Decrypt the Bytecode

Find the encrypted blob in .rodata (512 bytes starting with 0xD3). The decrypt function XORs each byte with 0xC3:

```python
encrypted = open("cerebrum", "rb").read()
# Find at offset (use Ghidra xref to the data)
offset = 0x7B3E0  # varies by build
bytecode = bytes(b ^ 0xC3 for b in encrypted[offset:offset+512])
```

---

## Step 5: Write an Emulator

```python
def emulate(bytecode):
    regs = [0] * 8
    pc = 0
    output = []

    while pc < len(bytecode):
        op = bytecode[pc]; pc += 1
        if op == 0x00: pass                          # NOP
        elif op == 0x10:                             # MOV_IMM Rx, imm16
            rx = bytecode[pc] & 7; pc += 1
            imm = bytecode[pc] | (bytecode[pc+1] << 8); pc += 2
            regs[rx] = imm
        elif op == 0x28:                             # ADD_IMM Rx, imm8
            rx = bytecode[pc] & 7; pc += 1
            regs[rx] += bytecode[pc]; pc += 1
        elif op == 0x29:                             # XOR_IMM Rx, imm8
            rx = bytecode[pc] & 7; pc += 1
            regs[rx] ^= bytecode[pc]; pc += 1
        elif op == 0x70:                             # PUTC Rx
            rx = bytecode[pc] & 7; pc += 1
            output.append(chr(regs[rx] & 0xFF))
        elif op == 0xFF: break                       # HALT
    return ''.join(output)
```

---

## Step 6: Execute

```bash
$ python solve.py cerebrum
[+] FLAG: warCTF{v1rtu4l_m4ch1n3_r3v3rs3d_APT_1nf1n1ty}
```

---

## Why It's Insane

| Factor | Difficulty |
|--------|-----------|
| Custom ISA | Must reverse an entirely unknown instruction set |
| Stripped + static | No symbols, large binary (~700KB of libc noise) |
| Encrypted bytecode | Can't just strings/hexdump the flag |
| 256-entry dispatch | Large switch intimidates inexperienced reversers |
| Variable-length instructions | Must correctly identify operand sizes |
| Obfuscated flag computation | Each char uses different arithmetic path |
| No input-dependent behavior | Can't use dynamic analysis shortcuts easily |
| Writing an emulator | Requires programming + RE skills combined |

---

## Alternative Approaches

1. **Dynamic: just run it** - if the binary runs cleanly, the flag prints. But in a harder variant, it could check environment/input.
2. **Patch the binary** - NOP out the decrypt function and dump raw memory after decryption.
3. **GDB scripting** - break after decrypt, dump bytecode, analyze offline.
4. **Angr/symbolic execution** - model the VM and solve symbolically (very advanced).

---

## Tools

- **Ghidra** - primary RE tool for the dispatcher
- **GDB** - dynamic analysis, memory dumps
- **Python** - emulator implementation
- **hexdump/xxd** - examining bytecode
