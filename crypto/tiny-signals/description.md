# t1ny::s1gn4ls

**Category:** Crypto  
**Difficulty:** Easy-Medium  
**Points:** 200  
**Author:** H3xPh4r04h  

---

> **SIGNAL INTERCEPT — PRIORITY: MODERATE**
>
> An encrypted message was intercepted over a military channel.
> The enemy uses RSA — 2048-bit modulus, textbook implementation.
>
> On paper, unbreakable.
>
> But our analysts noticed something in the key generation.
> The modulus `n = p × q`... one of those primes is suspiciously small.
>
> **Find the weak link. Break the chain.**

## Hints

1. `n` is large. But is it *balanced*?
2. Trial division doesn't take long when a factor is tiny.
3. Once you have `p`, the rest is textbook RSA.
4. `phi = (p-1)(q-1)`, `d = e^(-1) mod phi`, `m = c^d mod n`.

## Connection

```
nc <host> <port>
```
