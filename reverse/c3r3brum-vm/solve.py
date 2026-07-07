#!/usr/bin/env python3
"""
c3r3brum::vm - Solve Script

After reversing the binary, the solver knows:
1. Bytecode is XOR'd with key 0xC3 (found in .rodata or via xref to decrypt func)
2. The VM uses opcodes: 0x10 (MOV_IMM), 0x29 (XOR_IMM), 0x28 (ADD_IMM), 0x70 (PUTC), etc.
3. The program computes each flag char via arithmetic and prints it

This script: extracts the encrypted bytecode, decrypts it, emulates the VM.
"""
import struct
import sys

# Found by reversing the binary:
XOR_KEY = 0xC3

# Opcodes (recovered from the dispatcher switch/table)
OP_NOP      = 0x00
OP_MOV_IMM  = 0x10
OP_MOV_REG  = 0x11
OP_ADD      = 0x20
OP_SUB      = 0x21
OP_XOR      = 0x22
OP_MUL      = 0x23
OP_AND      = 0x24
OP_OR       = 0x25
OP_SHR      = 0x26
OP_SHL      = 0x27
OP_ADD_IMM  = 0x28
OP_XOR_IMM  = 0x29
OP_CMP      = 0x30
OP_CMP_IMM  = 0x31
OP_JMP      = 0x40
OP_JZ       = 0x41
OP_JNZ      = 0x42
OP_STORE    = 0x50
OP_LOAD     = 0x51
OP_STORE_I  = 0x52
OP_LOAD_I   = 0x53
OP_PUSH     = 0x60
OP_POP      = 0x61
OP_PUTC     = 0x70
OP_HALT     = 0xFF


def emulate(bytecode):
    """Emulate the Cerebrum VM."""
    regs = [0] * 8
    mem = [0] * 256
    stack = []
    pc = 0
    zf = 0
    output = []

    def fetch8():
        nonlocal pc
        v = bytecode[pc]
        pc += 1
        return v

    def fetch16():
        nonlocal pc
        v = bytecode[pc] | (bytecode[pc + 1] << 8)
        pc += 2
        return v

    cycles = 0
    while pc < len(bytecode) and cycles < 100000:
        op = fetch8()
        cycles += 1

        if op == OP_NOP:
            pass
        elif op == OP_MOV_IMM:
            rx = fetch8() & 7
            imm = fetch16()
            regs[rx] = imm
        elif op == OP_MOV_REG:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] = regs[ry]
        elif op == OP_ADD:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] = (regs[rx] + regs[ry]) & 0xFFFFFFFF
        elif op == OP_SUB:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] = (regs[rx] - regs[ry]) & 0xFFFFFFFF
        elif op == OP_XOR:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] ^= regs[ry]
        elif op == OP_MUL:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] = (regs[rx] * regs[ry]) & 0xFFFFFFFF
        elif op == OP_AND:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] &= regs[ry]
        elif op == OP_OR:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] |= regs[ry]
        elif op == OP_SHR:
            rx = fetch8() & 7
            imm = fetch8()
            regs[rx] >>= imm
        elif op == OP_SHL:
            rx = fetch8() & 7
            imm = fetch8()
            regs[rx] = (regs[rx] << imm) & 0xFFFFFFFF
        elif op == OP_ADD_IMM:
            rx = fetch8() & 7
            imm = fetch8()
            regs[rx] = (regs[rx] + imm) & 0xFFFFFFFF
        elif op == OP_XOR_IMM:
            rx = fetch8() & 7
            imm = fetch8()
            regs[rx] ^= imm
        elif op == OP_CMP:
            rx = fetch8() & 7
            ry = fetch8() & 7
            zf = int(regs[rx] == regs[ry])
        elif op == OP_CMP_IMM:
            rx = fetch8() & 7
            imm = fetch8()
            zf = int(regs[rx] == imm)
        elif op == OP_JMP:
            addr = fetch16()
            pc = addr
        elif op == OP_JZ:
            addr = fetch16()
            if zf:
                pc = addr
        elif op == OP_JNZ:
            addr = fetch16()
            if not zf:
                pc = addr
        elif op == OP_STORE:
            rx = fetch8() & 7
            ry = fetch8() & 7
            mem[regs[rx] & 0xFF] = regs[ry] & 0xFF
        elif op == OP_LOAD:
            rx = fetch8() & 7
            ry = fetch8() & 7
            regs[rx] = mem[regs[ry] & 0xFF]
        elif op == OP_STORE_I:
            imm = fetch8()
            rx = fetch8() & 7
            mem[imm] = regs[rx] & 0xFF
        elif op == OP_LOAD_I:
            rx = fetch8() & 7
            imm = fetch8()
            regs[rx] = mem[imm]
        elif op == OP_PUSH:
            rx = fetch8() & 7
            stack.append(regs[rx])
        elif op == OP_POP:
            rx = fetch8() & 7
            regs[rx] = stack.pop() if stack else 0
        elif op == OP_PUTC:
            rx = fetch8() & 7
            output.append(chr(regs[rx] & 0xFF))
        elif op == OP_HALT:
            break
        else:
            print(f"[!] Unknown opcode 0x{op:02X} at PC={pc-1}")
            break

    return ''.join(output)


def extract_bytecode_from_binary(path):
    """Extract encrypted bytecode from the ELF binary."""
    with open(path, "rb") as f:
        data = f.read()

    # Look for the pattern of encrypted bytecode
    # In the compiled binary, the bytecode array is in .rodata
    # We search for a known sequence or use the XOR key to find it
    # Alternative: just hardcode what we found in Ghidra
    print(f"[*] Binary size: {len(data)} bytes")
    print("[*] Searching for encrypted bytecode in .rodata...")

    # The bytecode starts with 0xD3 0xC3 (which is OP_MOV_IMM=0x10 XOR 0xC3)
    # Look for the sequence
    marker = bytes([0x10 ^ XOR_KEY, 0x00 ^ XOR_KEY])  # MOV R0
    candidates = []
    for i in range(len(data) - 512):
        if data[i] == marker[0] and data[i+1] == marker[1]:
            # Check if decrypting produces valid opcodes
            sample = bytes(b ^ XOR_KEY for b in data[i:i+20])
            if sample[0] == OP_MOV_IMM and sample[4] in (OP_XOR_IMM, OP_ADD_IMM, OP_NOP):
                candidates.append(i)

    if not candidates:
        print("[-] Could not find bytecode. Provide offset manually.")
        return None

    offset = candidates[0]
    print(f"[+] Found bytecode at offset 0x{offset:X}")
    encrypted = data[offset:offset + 512]
    return encrypted


if __name__ == "__main__":
    binary_path = sys.argv[1] if len(sys.argv) > 1 else "chall-dist/cerebrum"

    print("[*] c3r3brum::vm solver")
    print(f"[*] Binary: {binary_path}")
    print()

    encrypted = extract_bytecode_from_binary(binary_path)
    if encrypted is None:
        sys.exit(1)

    # Decrypt
    bytecode = bytes(b ^ XOR_KEY for b in encrypted)
    print(f"[*] Decrypted {len(bytecode)} bytes of bytecode")
    print()

    # Emulate
    print("[*] Emulating VM...")
    flag = emulate(bytecode)
    print(f"\n[+] FLAG: {flag.strip()}")
