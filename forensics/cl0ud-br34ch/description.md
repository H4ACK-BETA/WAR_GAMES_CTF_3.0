# cl0ud::br34ch

**Category:** Forensics + Cloud  
**Difficulty:** Hard+  
**Points:** 550  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** 8080 (PCAP download)  

---

> **INCIDENT RESPONSE - PRIORITY: CRITICAL**
>
> **Cluster:** prod-eks-us-east-1  
> **Timestamp:** 2026-07-06 01:33 UTC  
> **Status:** Cluster wiped. Only VPC flow logs and a 4-minute PCAP remain.
>
> At 01:33, our alerting pipeline went silent. By 01:37, every secret
> in the production namespace was accessed. By 01:38, the attacker
> had exfiltrated and the cluster was burning.
>
> The IR team recovered a packet capture from the VPC network tap
> before the nodes went dark. Everything is in here - the initial
> pod compromise, the service account token theft, the API server
> calls, the secret extraction.
>
> **Your job: trace the kill chain. Recover what they stole.**

## Kill Chain (What Happened)

```
Compromised Pod --> SA Token Theft --> K8s API Auth --> Secret Enumeration --> Flag Exfil
```

## Hints

1. One pod is talking to the API server. Most pods don't do that directly.
2. Kubernetes API lives at `10.96.0.1:443`. Find who's calling it.
3. The Authorization header contains a JWT. Decode it - it tells you which ServiceAccount.
4. API responses contain JSON. One of those JSON blobs has secrets.
5. Kubernetes secrets are base64-encoded in the response body. Decode twice.

## Connection

```
http://<host>:8080   (download PCAP)
```
