# sh4d0w::b34c0n

**Category:** Forensics  
**Difficulty:** Medium  
**Points:** 300  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** 8080 (PCAP download)  

---

> **SOC ALERT - TIER 2 ESCALATION**
>
> **Source:** Finance workstation `WS-FIN-042`  
> **Detection:** Network anomaly - periodic outbound every ~60 seconds  
> **AV Status:** Clean (all scans negative)  
> **Action Taken:** Host isolated. Full packet capture preserved.
>
> At 11:47 UTC, our NDR flagged `WS-FIN-042` for beaconing behavior.
> Exactly every 60 seconds, it reaches out to an external IP.
> Endpoint AV sees nothing. EDR shows no malicious process.
>
> Yet something is talking. Something is listening. And something left.
>
> The 8-minute capture contains everything. The beacon. The commands.
> The exfiltration. Whatever they took is encoded in the wire.
>
> **Find the rhythm. Decode the whispers. Recover what was stolen.**

## Hints

1. Beacons have a heartbeat. Find the interval.
2. HTTP can carry conversations disguised as normal traffic.
3. Commands flow inbound. Data flows outbound.
4. What looks like random query strings might be encoded payloads.
5. Reassemble in order. Decode twice if needed.

## Connection

```
http://<host>:8080   (download PCAP)
```
