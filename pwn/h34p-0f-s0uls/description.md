# H34p 0f S0uls

**Category:** B1n4ry 3xpl01t4t10n (Pwn)  
**Difficulty:** M3d-H4rd  
**Author:** H3xPh4r04h  
**Points:** 450

---

## D3scr1pt10n

> *Th3 Gr4v3y4rd 0f L0st S0uls l13s 4t th3 3dg3 0f th3 D1g1t4l Und3rw0rld.*
>
> *34ch s0ul 1s b0und t0 4 v3ss3l - 4 fr4gm3nt 0f m3m0ry 4ll0c4t3d fr0m th3 h34p 0f th3 d4mn3d.*
>
> *Th3 N3cr0m4nc3r 0ff3rs y0u s1mpl3 t00ls: c0ll3ct, r3l34s3, v13w, 3d1t, 4nd p3rf0rm r1tu4ls up0n th3s3 s0uls.*
>
> *But th3 v3ss3ls 4r3 fr4g1l3. Th31r b0und4r13s... p0r0us. P0ur t00 much 3ss3nc3 1nt0 0n3, 4nd 1t sp1lls 1nt0 1ts n31ghb0r.*
>
> *C0rrupt th3 ch41n. P01s0n th3 r1tu4l. 4sc3nd.*
>
> *Th3 v01d y13lds 1ts s3cr3t 0nly t0 th0s3 wh0 und3rst4nd th3 4rch1t3ctur3 0f d34th.*

---

## H1nts

- Th3 s0uls l1v3 0n th3 h34p. Th31r b0und4r13s 4r3 n0t wh4t th3y s33m.
- 4 s0ul's "r1tu4l" 1s 4 p0w3rful th1ng. Wh4t 1f y0u c0uld ch4ng3 wh3r3 1t l34ds?
- Th3 N3cr0m4nc3r l34v3s cl34n cl33nly scr3ll3d 1nf0rm4t10n f0r th0s3 wh0 4sk.

---

## F1l3s

- `challenge` - Th3 Gr4v3y4rd b1n4ry (ELF x86-64)
- `libc.so.6` - Th3 l1bc us3d (glibc 2.31, Ubuntu 20.04)

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
PIE:      Disabled
ASLR:     Disabled (on binary)
```

---

*"M3m0ry 1s just 4n0th3r f0rm 0f d34th. 4nd d34th c4n b3 m4n1pul4t3d."*
