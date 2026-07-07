# gh0st::exf1l — Forensics Challenge (Medium-Hard)

PCAP analysis: DNS recon → HTTP credential leak → SMB file extraction → ZIP decryption → flag.

## Quick Start

```bash
docker-compose up --build
# Download PCAP at http://localhost:8083
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Port:** 8080 (HTTP file server)
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- Each team gets a unique PCAP with randomized hostnames, passwords, filenames, and flag.

## Attack Flow

1. Open PCAP in Wireshark
2. Filter DNS → find suspicious internal hostname (non-standard subdomain)
3. Filter HTTP → find Basic Auth header → base64 decode → get ZIP password
4. Filter TCP port 445 → Follow stream → extract ZIP file (PK magic)
5. Unzip with the password from step 3
6. Read flag.txt

## Randomized Per Team

- Exfil target hostname
- ZIP password
- ZIP filename inside the transfer
- Flag value

## Solve

```bash
python solve.py capture.pcap
```

## Dependencies (for generation)

- `scapy` (PCAP creation)
- `zip` command (password-protected ZIP creation)
- `flask` + `gunicorn` (file serving)
