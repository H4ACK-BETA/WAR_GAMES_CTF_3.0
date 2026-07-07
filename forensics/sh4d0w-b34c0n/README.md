# sh4d0w::b34c0n - Forensics Challenge (Medium)

C2 beacon analysis: identify periodic HTTP beaconing, decode commands, reassemble exfiltrated base64 data.

## Quick Start

```bash
docker-compose up --build
# Download PCAP at http://localhost:8085
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Port:** 8080
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- Randomized per team: beacon ID, flag chunks

## Attack Flow

1. Open PCAP → spot periodic traffic to external IP every ~60s
2. Decode base64 commands in C2 responses (JSON `data` field)
3. Find POST requests to `/api/v2/telemetry` with `d=` parameter
4. Sort chunks by `seq` → concatenate → base64 decode → flag

## Solve

```bash
python solve.py beacon_capture.pcap
```
