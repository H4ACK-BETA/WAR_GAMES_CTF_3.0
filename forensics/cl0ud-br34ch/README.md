# cl0ud::br34ch - Forensics + Cloud (Hard)

Kubernetes cluster breach PCAP analysis: trace API calls, decode JWT, extract secrets.

## Quick Start

```bash
docker-compose up --build
# Download at http://localhost:8086
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Port:** 8080
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var

## Attack Flow in PCAP

1. Compromised pod (10.244.1.47) calls K8s API at 10.96.0.1:6443
2. Uses stolen ServiceAccount JWT token
3. Enumerates: /api -> /namespaces -> /pods -> /secrets -> /secrets/flag-secret
4. Flag is base64-encoded in the secret response

## Solve

```bash
python solve.py cloud_breach.pcap
```
