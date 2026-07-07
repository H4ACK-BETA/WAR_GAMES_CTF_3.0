# c0ns3nsus::m4ch1n3 - Reverse Engineering (Insane)

Anti-AI crackme. Three engines. Only the DFA state machine matters.
Engines 1 and 2 always pass (opaque predicates + dead code).

## Build

```bash
gcc -O1 -no-pie -fno-stack-protector -o chall-dist/consensus src/consensus.c
strip --strip-all chall-dist/consensus
```

## Key

`7761724354467b6b33795f69735f3174` = `warCTF{k3y_is_1t` (hex-encoded)

## Solve

```bash
python solve.py
```
