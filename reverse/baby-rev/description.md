# b4by::r3v

**Category:** Reverse Engineering  
**Difficulty:** Easy  
**Points:** 100  
**Author:** H3xPh4r04h  

---

> *"The binary remembers what you forgot."*

A simple program asks for a password. Get it right and you get the flag. Get it wrong and... well, try harder.

The password isn't stored in plaintext — but the secret is still inside the binary, hiding in plain sight. All you need is the right perspective.

## Hints

1. The password is short. Very short.
2. XOR's cousin lives here.
3. Constants in the binary are your friends.
4. Ghidra is free. So is `objdump`.

## Connection

```
nc <host> 9999
```

## Files

- `challenge` — the binary (stripped)
