# c0ns3nsus::m4ch1n3

**Category:** Reverse Engineering  
**Difficulty:** Insane  
**Points:** 800  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** Static (binary only)  

---

> **MALWARE ANALYSIS LAB - SAMPLE #C0NS3NSUS**
>
> **Classification:** Experimental verification system  
> **Origin:** Intercepted from research network, attributed to unknown actor  
> **Behavior:** Accepts 16-byte input key. Decrypts flag only on correct key.
>
> This is not normal crackme logic.
>
> Three independent verification engines evaluate your input simultaneously.
> A consensus module combines their results. Only if all three "agree"
> does the flag decrypt.
>
> But here's the twist our analysts discovered after 72 hours of
> staring at decompiled garbage:
>
> - The **Arithmetic Engine** is a trap. It evaluates to TRUE for any
>   input matching a trivial pattern. It exists only to waste your time.
> - The **Control-Flow Engine** is a maze of opaque predicates, dead code,
>   and impossible branches. It ALWAYS returns TRUE regardless of input.
> - The **State Machine Engine** is the only one that actually validates.
>   A 6-state DFA processes each byte of your input. Only one path
>   through the machine reaches the accept state.
>
> The consensus function: `arithmetic AND control_flow AND state_machine`
>
> Since arithmetic and control-flow always pass, only the state machine matters.
>
> **Reverse the DFA. Find the accepting input. Get the flag.**
>
> Good luck. The dead code is designed to waste automated tools.
> Humans who read carefully will see through the noise.

## Hints

1. Three engines. Only one matters. Don't waste time on all three.
2. The control-flow engine has opaque predicates - expressions that LOOK conditional but always evaluate the same way. Skip it.
3. The arithmetic engine checks `input[0] + input[1] == 0xAA` and similar. It's a red herring.
4. Find the state machine. It has a transition table. Trace the accept path.
5. The key is 16 bytes. Each byte drives one state transition.

## Files

- `consensus` - the binary (stripped)
