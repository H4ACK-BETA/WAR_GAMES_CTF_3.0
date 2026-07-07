# kub3::br34ch — Web + Cloud Challenge (Hard)

Kubernetes privilege escalation via SSRF + LFI + ServiceAccount token pivoting.

## Quick Start

```bash
docker-compose up --build
# Access at http://localhost:8082
```

## GZCTF Deployment

- **Type:** Dynamic container
- **Port:** 8080 (HTTP)
- **Flag:** Set via `GZCTF_FLAG` or `FLAG` env var
- **Image:** Build from Dockerfile

## Architecture

Single container simulating a Kubernetes environment:
- Flask web app (player-facing, port 8080)
- Simulated K8s API server (internal, port 6443)
- Fake ServiceAccount token mounted at standard path
- RBAC enforced: frontend-sa vs backup-agent-sa

## Attack Chain

1. `/debug/env` → Discover pod name, namespace, K8s API address
2. `/debug/logs?path=../../../../var/run/secrets/.../token` → LFI extracts SA token
3. SSRF via `/fetch` → K8s API `/api/v1/namespaces/production/pods` (frontend-sa can list pods)
4. Find `backup-agent` pod (labeled `privileged: true`, different SA)
5. Read backup pod logs → confirms it has secret access
6. Exec into backup pod → extract `backup-agent-sa` token (privilege escalation)
7. Use new token → list secrets (now allowed)
8. Read `flag-secret` → base64 decode → flag

## Why Hard

- Multi-stage: LFI → SSRF → K8s enumeration → privilege escalation → secret exfiltration
- Requires Kubernetes knowledge (SA tokens, RBAC, API structure)
- First token is deliberately limited (RBAC 403 on secrets)
- Must pivot through a second pod's service account
- Red herrings: fake secrets (aws-credentials, jwt-signing-key, etc.)

## Solve

```bash
python solve.py <host> <port>
```
