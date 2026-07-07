# d3j4::vu

**Category:** Crypto  
**Difficulty:** Easy-Medium  
**Points:** 200  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** 1338  

---

> **SIGNAL INTERCEPT - PRIORITY: HIGH**
>
> Our field team captured five consecutive outputs from an enemy key generator
> moments before it encrypted a classified transmission.
>
> Intelligence suggests the generator uses a Linear Congruential algorithm.
> The constants are known. The state advances predictably.
>
> The next output after those five was used to derive the AES key.
>
> **Predict the future. Decrypt the past.**

## Hints

1. LCG: `state = (A * state + C) % M`
2. You have 5 outputs. You only need the last one.
3. The key is `SHA256(next_state)`.
4. AES-ECB. No IV needed.

## Connection

```
nc <host> 1338
```
