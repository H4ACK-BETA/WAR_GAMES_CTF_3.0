# 4r34::51

**Category:** Forensics  
**Difficulty:** Medium  
**Points:** 250  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** 8080 (PCAP download)  

---

> **CLASSIFIED - EYES ONLY - CLEARANCE LEVEL: COSMIC**
>
> **Incident Timestamp:** 2026-07-05 04:17:33 UTC  
> **Window of Exposure:** 45 seconds  
> **Status:** Server isolated. Forensic image secured.
>
> At 04:17:33 UTC, monitoring systems detected unauthorized external connectivity
> from a classified research server (codename: ROSWELL). The server was air-gapped.
> It should not have been reachable. Yet for exactly 45 seconds, it was.
>
> Someone got in. Someone got out. With something.
>
> The only evidence we have is a packet capture from the perimeter tap.
> Whatever was exfiltrated left through this wire. Find it.
>
> This transmission is classified TOP SECRET // UMBRA.

## Your Mission

Analyze the 45-second capture window. Identify the intruder. Recover what was stolen.

## Hints

1. DNS can carry more than domain names.
2. Not every HTTP response contains a webpage.
3. Passwords don't always travel with the files they protect.
4. Look at what's encoded, not just what's encrypted.

## Connection

```
http://<host>:8080   (download PCAP)
```
