# cl0ud::br34ch - Writeup

**Category:** Forensics + Cloud  
**Difficulty:** Hard+  
**Points:** 550  

---

## Overview

A K8s cluster was breached. The PCAP contains the full kill chain:
- Multiple pods talk to the API server (decoys + attacker)
- Attacker starts with a low-privilege token (gets 403 on secrets)
- Pivots by reading another pod's logs which leak a high-privilege token
- Uses the new token to enumerate and read secrets
- Flag is XOR + base64 encoded inside the secret

---

## Step 1: Identify the Attacker Among Multiple API Callers

Three pods talk to the K8s API:
- `10.244.1.22` (prometheus-sa) - reads node status (legitimate monitoring)
- `10.244.1.33` (liveness-probe-sa) - reads pod status (legitimate health check)
- `10.244.1.47` (webapp-sa) - gets 403, reads logs, pivots tokens (ATTACKER)

**Key indicator:** Only `10.244.1.47` receives a `403 Forbidden` response and then switches to a different token mid-session.

---

## Step 2: Trace the Privilege Escalation

The attacker's API calls:

| # | Token | Path | Result |
|---|-------|------|--------|
| 1 | webapp-sa | GET /secrets | 403 Forbidden |
| 2 | webapp-sa | GET /pods | 200 - finds backup pod |
| 3 | webapp-sa | GET /pods/cluster-backup.../log | 200 - TOKEN LEAKED |
| 4 | cluster-backup-sa | GET /secrets | 200 - list secrets |
| 5 | cluster-backup-sa | GET /secrets/flag-secret | 200 - flag |

The pivot: pod logs accidentally contain the full JWT of `cluster-backup-sa`.

---

## Step 3: Decode the Flag

The secret response contains:
```json
{
  "metadata": {
    "annotations": {"encoding": "xor+base64", "key": "k8s_breach"}
  },
  "data": {"flag": "<base64>"}
}
```

Triple decode:
```python
import base64

raw = "<value from data.flag>"
step1 = base64.b64decode(raw).decode()       # outer base64
step2 = base64.b64decode(step1)               # inner base64 -> XOR'd bytes
key = b"k8s_breach"
flag = bytes(b ^ key[i % len(key)] for i, b in enumerate(step2)).decode()
```

---

## Why It's Hard+

| Factor | Difficulty Added |
|--------|-----------------|
| Multiple API callers | Must distinguish attacker from legitimate monitoring pods |
| Token pivot | Must notice the token CHANGES mid-session |
| Log-based token leak | Non-obvious lateral movement technique |
| XOR + double base64 | Three encoding layers, not just plain base64 |
| Annotation hint | Must read metadata annotations for decoding scheme |
| Realistic decoys | Monitoring + health-check traffic looks similar to attack |
| No clear timestamps | Can't rely on "first/last" - must follow logic |

---

## Tools

- **Wireshark** - filter by `ip.dst == 10.96.0.1`, follow streams
- **jq** - parse JSON responses
- **CyberChef** - JWT decode, XOR, base64
- **Python** - scripted multi-stage decode
