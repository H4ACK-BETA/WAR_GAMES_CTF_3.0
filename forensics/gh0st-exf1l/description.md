# gh0st::exf1l

**Category:** Forensics  
**Difficulty:** Medium-Hard  
**Points:** 350  
**Author:** H3xPh4r04h  

---

> *Incident Report #4471 — NovaCorp SOC*
>
> **Date:** 2026-07-02 03:47 UTC  
> **Severity:** Critical  
> **Analyst:** J. Reeves
>
> At 02:15 UTC, our SIEM flagged anomalous outbound traffic from `BACKUP-SRV-03`
> averaging 840MB/night for the past 11 days. The server's only authorized role
> is LAN-to-LAN replication. It has no business talking to the internet.
>
> At 03:12, we captured a full packet dump before isolating the host.
> Initial triage shows DNS queries to hostnames that don't exist in our
> internal zone, SMB sessions to an unregistered endpoint, and HTTP
> traffic with suspicious auth headers.
>
> Someone is exfiltrating data. Through our own backup server.
>
> The PCAP is attached. Find what they took.

## Your Mission

Analyze the network capture. Trace the ghost. Recover the exfiltrated data.

## Hints

1. DNS tells you where they went.
2. SMB tells you what they moved.
3. HTTP tells you how they locked it.
4. Base64 isn't a lock — it's a label.

## Files

- `capture.pcap` — Full packet capture from BACKUP-SRV-03

## Connection

This is a static challenge. Download the PCAP and analyze offline.
