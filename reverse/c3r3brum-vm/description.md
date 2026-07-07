# c3r3brum::vm

**Category:** Reverse Engineering  
**Difficulty:** Insane  
**Points:** 750  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** Static (binary only)  

---

> **THREAT INTELLIGENCE BRIEF - EYES ONLY**
>
> **Designation:** CEREBRUM  
> **Origin:** Unknown (attributed APT-∞)  
> **Recovery Site:** Air-gapped facility, Building 7, Sub-level 3  
> **Classification:** Nation-state grade implant
>
> The recovered sample does not execute native instructions.
> It carries its own virtual machine - a custom ISA with encrypted
> bytecode, virtual registers, and a 256-entry opcode dispatch table.
>
> The bytecode is AES-encrypted at rest. On execution, the VM decrypts
> its program, interprets each instruction through an obfuscated
> dispatcher, and produces output only if the full program completes.
>
> We believe the flag - a verification string used by the operators -
> is computed by the VM during execution. No static extraction is possible.
>
> **Your mission: reverse the VM, write an emulator, recover the flag.**

## What You'll See

```
main() -> AES decrypt bytecode -> VM interpreter loop
  - 256-byte opcode table
  - 8 virtual registers (R0-R7)
  - 256 bytes virtual memory
  - Stack (64 entries)
  - Conditional branching
  - XOR/ADD/SUB/MUL arithmetic
  - Memory load/store
  - Output instruction
```

## Hints

1. Start with the dispatcher. It's a giant switch or function pointer table.
2. The AES key is derived from a hardcoded constant. Find it in .rodata.
3. Not all 256 opcodes are used. Focus on the ~25 that appear in the bytecode.
4. The VM has a "print" instruction. Whatever it outputs IS the flag.
5. You don't need to reverse the whole ISA. Trace what the bytecode actually does.

## Files

- `cerebrum` - the binary (stripped, static, no PIE)
