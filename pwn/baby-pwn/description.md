# b4by::pwn

**Category:** Binary Exploitation (pwn)  
**Difficulty:** Easy-Med  
**Points:** 200  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** 8888  

---

> *"My memory is not very well protected..."*

I wrote a simple greeting program. It asks for your name. It says hello. Nothing fancy.

Except... there's a function that never gets called. And the buffer that holds your name is a bit smaller than what it's willing to read.

What could possibly go wrong?

## Hints

1. What happens when you write more than 64 characters?
2. There's a function that never gets called normally...
3. Stack alignment matters on modern Linux.

## Connection

```
nc <host> 8888
```

## Files

- `challenge` - the binary to reverse and exploit
