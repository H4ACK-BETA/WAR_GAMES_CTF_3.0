# sh4d0w::b34c0n - Writeup

**Category:** Forensics  
**Difficulty:** Medium  
**Points:** 300  
**Flag:** `WarCTF{dynamic_per_team}`

---

## Overview

A C2 beacon communicates via HTTP disguised as analytics traffic. The flag is exfiltrated as base64 chunks in POST requests. Players must identify the beaconing pattern, decode C2 commands, and reassemble the stolen data.

---

## Step 1: Open the PCAP and Identify Beaconing

Open `beacon_capture.pcap` in Wireshark.

**Quick observations:**
- Traffic from `10.20.5.42` (the compromised workstation)
- Most traffic goes to internal IPs and known sites
- But some traffic goes to `185.199.47.103` - an external IP

**Filter:** `ip.dst == 185.199.47.103`

You'll see periodic HTTP requests to this IP on port 443. The path pattern:
```
GET /api/v2/status?sid=<beacon_id>&t=<random>
```

This is the C2 check-in. The `sid` parameter is the same across all requests - it's the beacon session ID.

---

## Step 2: Decode C2 Commands

Look at the responses FROM `185.199.47.103`:

**Filter:** `ip.src == 185.199.47.103 && http`

Each response contains JSON:
```json
{"status":"ok","data":"d2hvYW1p","interval":60}
```

The `data` field is base64-encoded. Decode each:

```python
import base64

commands_b64 = ["d2hvYW1p", "c3lzdGVtaW5mbyB8IGZpbmRzdHIgL0IgL0M6T1M=", ...]
for c in commands_b64:
    print(base64.b64decode(c).decode())
```

**Decoded commands:**
```
whoami
systeminfo | findstr /B /C:OS
dir C:\Users\finance\Documents
type C:\Users\finance\Documents\Q3_report.xlsx
exfil_start
sleep
```

The attacker enumerated the system, found a file, then started exfiltration.

---

## Step 3: Find Exfiltration Data

After the `exfil_start` command, look for POST requests from the victim:

**Filter:** `ip.src == 10.20.5.42 && http.request.method == POST`

Each POST to `/api/v2/telemetry` has a body like:
```
sid=lv9WCzMNkohNBdgf&seq=0&d=V2FyQ1RGe2Iz
sid=lv9WCzMNkohNBdgf&seq=1&d=NGMwbl9kM3Qz
sid=lv9WCzMNkohNBdgf&seq=2&d=Y3QzZF9jMl9j
sid=lv9WCzMNkohNBdgf&seq=3&d=aDRubjNsX2Qz
sid=lv9WCzMNkohNBdgf&seq=4&d=YzBkM2R9
```

The `d` parameter contains the exfiltrated data chunks. The `seq` parameter gives the order.

---

## Step 4: Reassemble and Decode

Sort by `seq`, concatenate the `d` values:

```python
import base64

chunks = {
    0: "V2FyQ1RGe2Iz",
    1: "NGMwbl9kM3Qz",
    2: "Y3QzZF9jMl9j",
    3: "aDRubjNsX2Qz",
    4: "YzBkM2R9",
}

assembled = ''.join(chunks[i] for i in sorted(chunks.keys()))
flag = base64.b64decode(assembled).decode()
print(flag)
```

**Output:**
```
WarCTF{b34c0n_d3t3ct3d_c2_ch4nn3l_d3c0d3d}
```

---

## Quick Solve (One-liner in tshark)

```bash
tshark -r beacon_capture.pcap -Y "http.request.method==POST && ip.dst==185.199.47.103" \
  -T fields -e http.file_data | \
  grep -oP 'd=\K[^&]+' | sort | tr -d '\n' | base64 -d
```

---

## Key Indicators of Compromise (IOCs)

| IOC | Value |
|-----|-------|
| C2 IP | 185.199.47.103 |
| Beacon interval | ~60 seconds |
| C2 path | /api/v2/status |
| Exfil path | /api/v2/telemetry |
| User-Agent | Standard Chrome UA (blends in) |
| Host header | cdn-analytics.cloud |
| Data encoding | Base64 |

---

## Skills Tested

| Skill | Where |
|-------|-------|
| Timing analysis | Identify periodic beaconing (60s intervals) |
| HTTP analysis | Distinguish C2 traffic from legitimate browsing |
| Base64 decoding | Commands in responses, data in POST bodies |
| Data reassembly | Ordering chunks by seq number |
| IOC identification | Recognizing the external C2 IP |

---

## Why It's Medium (Not Hard)

- Single encoding layer (just base64, no encryption)
- C2 traffic uses HTTP (plaintext, not HTTPS/encrypted)
- Obvious external IP (only one non-10.x address)
- Sequential chunk ordering with clear `seq` parameter
- No anti-analysis techniques (no traffic obfuscation, no timing jitter in the data)

A harder version would use DNS over HTTPS, encrypted payloads, or fragment the data across multiple protocols.

---

## Tools Used

- **Wireshark** - packet analysis, filtering, HTTP stream following
- **tshark** - command-line extraction
- **Python** - base64 decoding, reassembly
- **CyberChef** - alternative for base64 decoding
