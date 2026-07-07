# Baby-pwn

**Category:** Binary Exploitation (pwn)  
**Difficulty:** Easy-Med  
**Points:** 200  
**Author:** H3xPh4r04h  

## Description

I wrote a simple greeting program, but my memory management is a bit... relaxed.

Can you exploit the vulnerability and get the flag?

## Hints

1. What happens when you write more than 64 characters?
2. There's a function that never gets called normally...
3. Stack alignment matters on modern Linux.

## Connection

```
nc <host> 8888
```

## Files

- `challenge` — the binary to reverse and exploit
