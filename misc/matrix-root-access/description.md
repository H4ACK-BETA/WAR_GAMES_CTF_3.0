# matrix://root_access

**Category:** Misc (Rev + Pwn)  
**Difficulty:** Medium-Hard  
**Points:** 400  
**Author:** H3xPh4r04h  

## Description

> "Unfortunately, no one can be told what the Matrix is. You have to see it for yourself." — Morpheus

You've discovered a terminal deep inside the Machine City. It looks like a simple access point, but there's more here than meets the eye.

The machines left something behind. Find it.

## Hints

1. Not everything on the menu is visible. Some paths are hidden in the code.
2. The machine encrypted its secrets, but the key is still inside.
3. Once you're in, look for a way to go deeper. The transmission channel might be... unstable.
4. `checksec` is your friend.

## Connection

```
nc <host> 9999
```

## Files

- `chall` — the binary (stripped)
