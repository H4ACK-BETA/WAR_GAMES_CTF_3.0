# c0ns3nsus::m4ch1n3 - Writeup

**Category:** Reverse Engineering  
**Difficulty:** Insane  
**Points:** 800  

---

## The Anti-AI Design

This challenge is specifically structured to defeat automated reverse engineering:

- **Angr/symbolic execution** will try to satisfy all three engines simultaneously. It wastes time on the arithmetic and control-flow engines which always pass, and struggles with the state machine because the "opaque transform" looks conditional.
- **Z3/SMT solvers** fed the full binary will generate over-constrained models.
- **Fuzzing** won't find the 16-byte exact key in reasonable time.
- **AI code analysis** will focus on the complex-looking dead code, not the simple state machine.

A human who reads the code carefully will notice in ~30 minutes:
1. The arithmetic engine's if-condition is `(sum * sum) >= 0` - always true
2. The control-flow engine calls `opaque_true()` - always returns 1
3. The state machine is a simple sequential byte comparison

---

## Step 1: Run It

```
CONSENSUS MACHINE v2.1
Enter 16-byte key (hex): 0000...
[Engine 1 - Arithmetic]   : PASS   <- always
[Engine 2 - Control-Flow] : PASS   <- always  
[Engine 3 - State Machine]: FAIL   <- only real check
```

The output tells you exactly what matters. Engines 1 and 2 always pass.

---

## Step 2: Locate the State Machine

In Ghidra, find `state_machine_engine`. It's a loop:

```c
for (int i = 0; i < 16; i++) {
    uint8_t transform = (state * 7) ^ (i * 3);
    if ((key[i] ^ transform) == (expected[i] ^ transform))
        state = i + 1;
    else
        return 0;
}
```

The `transform` value is XOR'd onto BOTH sides of the comparison - it cancels out. The check is simply `key[i] == expected[i]`.

---

## Step 3: Read the Expected Bytes

The `DFA_ACCEPT_INPUT` array in `.rodata`:
```
0x77 0x61 0x72 0x43 0x54 0x46 0x7B 0x6B
0x33 0x79 0x5F 0x69 0x73 0x5F 0x31 0x74
```

Decode: `warCTF{k3y_is_1t`

---

## Step 4: Submit

```bash
echo "7761724354467b6b33795f69735f3174" | ./consensus
```

```
[Engine 3 - State Machine]: PASS
[Consensus]               : REACHED
[CONSENSUS REACHED] Flag: warCTF{c0ns3nsus_r34ch3d_st4t3_m4ch1n3_w1ns}
```

---

## Why AI Tools Fail Here

| Tool | Why It Fails |
|------|-------------|
| Angr | Explores all 3 engines, over-constrains the model, timeouts |
| Z3 direct | Arithmetic engine creates redundant constraints that slow solving |
| GPT/LLM | Focuses on `dead_complex_check` and `fake_validation` which look "real" |
| Fuzzing | 1 in 256^16 chance per guess - won't find in reasonable time |
| Radare2 auto | Can't automatically determine which branches are opaque |

**A skilled human** reads `(sum * sum) >= 0` and immediately knows it's always true. Takes 10 minutes.

---

## Tools

- **Ghidra** - identify the three engines, read `DFA_ACCEPT_INPUT`
- **Python** - hex encode the key
- **Common sense** - don't overthink it
