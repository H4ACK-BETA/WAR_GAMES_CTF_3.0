# 4r34::51 — Forensics Challenge (Medium)

45-second exposure window PCAP: DNS exfiltration + HTTP file transfer + ZIP password recovery.

## Quick Start

```bash
docker-compose up --build
# Download at http://localhost:8084
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Port:** 8080 (HTTP file server)
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- Randomized per team: password, DNS subdomains, flag

## Attack Flow

1. Open PCAP → identify external IP `198.51.100.47` (the intruder)
2. Filter DNS → find queries to `*.data.ns1.area51-research.internal`
3. Extract hex chunks from DNS subdomains: `<idx>-<hex>.data.ns1...`
4. Reassemble hex → decode → ZIP password (format: `COSMIC-XXXXXX-UMBRA`)
5. Filter HTTP → find GET response with `application/zip` content type
6. Export the ZIP from the HTTP response body
7. Unzip with recovered password → read `classified_document.txt` → flag

## Solve

```bash
python solve.py exposure_window.pcap
```
