# c3r3brum::vm - Reverse Engineering (Insane)

Custom VM with encrypted bytecode. Reverse the ISA, write an emulator, recover the flag.

## Build

```bash
# Generate bytecode (author only)
FLAG="warCTF{...}" python src/gen_bytecode.py

# Compile
gcc -O2 -static -o chall-dist/cerebrum src/cerebrum.c -I src/
strip --strip-all chall-dist/cerebrum
```

## Distribution

Give players `chall-dist/cerebrum` only (stripped, static binary).

## Solve

```bash
python solve.py chall-dist/cerebrum
```

## Architecture

- 8 registers (R0-R7), 256B memory, 64-entry stack
- ~25 opcodes: arithmetic, branching, memory, I/O
- Bytecode XOR encrypted with key 0xC3
- Flag computed via obfuscated per-char arithmetic (MOV + XOR/ADD + PUTC)
