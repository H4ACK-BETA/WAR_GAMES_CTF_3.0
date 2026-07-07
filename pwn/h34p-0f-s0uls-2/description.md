# H34p 0f S0uls II: R1s3 0f th3 L1ch

**Category:** B1n4ry 3xpl01t4t10n (Pwn)  
**Difficulty:** H4rd  
**Author:** H3xPh4r04h  
**Points:** 600

---

## D3scr1pt10n

> *Th3 L1ch h4s r1s3n fr0m th3 ru1ns 0f th3 f1rst gr4v3y4rd. Str0ng3r. Sm4rt3r. M0r3 pr0t3ct3d.*
>
> *Th3 w4lls 0f th3 und3rw0rld n0w sh1ft w1th 3v3ry s0ul y0u c0ll3ct (P1E + 4SLR). Th3r3 4r3 n0 fr33 g1fts th1s t1m3 - n0 d3bug m3nu, n0 w1n funct10n.*
>
> *But th3 d34d l34v3 tr4c3s. Wh3n 4 s0ul 1s r3l34s3d, 1ts 3ch0 r3m41ns - 4 gh0stly 1mpr1nt 0f wh3r3 1t 0nc3 w4s. R34d th3 3ch0. L34rn wh3r3 th3 L1ch's h00ks h1d3.*
>
> *P01s0n th3 ch41n 0f fr33d s0uls. Wr1t3 y0ur sp3ll 1nt0 th3 L1ch's 0wn h00k. Th3n r3l34s3 4 s0ul c4rry1ng th3 w0rds 0f p0w3r.*
>
> *`/bin/sh` - th3 1nc4nt4t10n th4t br34ks 4ll ch41ns.*

---

## N0t3s

- N0 w1n() funct10n. Y0u n33d 4 sh3ll.
- Th3 gr4v3y4rd sh1fts (PIE + ASLR). L34k f1rst.
- Th3 d34d l34v3 tr4c3s. Th31r m3m0ry l1ng3rs 4ft3r r3l34s3.
- Th3 L1ch h4s h00ks. F1nd th3m. 0v3rwr1t3 th3m.
- S1z3 m4tt3rs. Sm4ll s0uls 4nd l4rg3 s0uls b3h4v3 d1ff3r3ntly 1n d34th.

---

## F1l3s

- `challenge` - Th3 L1ch's d0m41n (ELF x86-64, PIE)
- `libc.so.6` - glibc 2.31 (Ubuntu 20.04)
- `ld-linux-x86-64.so.2` - dyn4m1c l1nk3r

## C0nn3ct10n

```
nc <HOST> 9999
```

---

## Pr0t3ct10ns

```
RELRO:    Partial RELRO
Stack:    No canary
NX:       Enabled
PIE:      Enabled
ASLR:     Full
```

---

*"Th3 L1ch d03s n0t d13. 1t m3r3ly w41ts f0r s0m30n3 w0rthy 3n0ugh t0 t4k3 1ts pl4c3."*
