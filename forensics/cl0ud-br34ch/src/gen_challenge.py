#!/usr/bin/env python3
"""
cl0ud::br34ch - PCAP Generator (Hard+)

Multi-stage K8s breach with:
1. Multiple pods talking to API server (decoy + real attacker)
2. First SA token is low-privilege (can only list pods)
3. Attacker reads pod spec to find a privileged SA mounted in another pod
4. Pivots by crafting a request with the second token (found in pod env/volume)
5. Second token can read secrets
6. Flag is XOR'd then base64'd inside the secret (not plain base64)

Requires:
- Identifying WHICH pod is the attacker (multiple talk to API)
- Understanding token privilege escalation
- Noticing the pivot from one SA to another
- XOR + base64 decode to get the final flag
"""
import os
import sys
import random
import string
import base64
import json
import hashlib

from scapy.all import (
    Ether, IP, UDP, TCP, DNS, DNSQR,
    Raw, wrpcap, RandMAC
)


def rand_str(n, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(n))


def get_flag():
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()
    return "warCTF{p0d_2_s3cr3t_cl0ud_br34ch_k8s_g4m3_0v3r}"


def xor_encode(data: bytes, key: bytes) -> bytes:
    return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))


# Network layout
API_SERVER_IP = "10.96.0.1"
API_SERVER_MAC = "02:42:0a:60:00:01"
DNS_IP = "10.96.0.10"
DNS_MAC = "02:42:0a:60:00:0a"

# Multiple pods that talk to API (makes identification harder)
ATTACKER_POD_IP = "10.244.1.47"
ATTACKER_POD_MAC = "02:42:0a:f4:01:2f"

# Legitimate monitoring pod (also talks to API - decoy)
MONITOR_POD_IP = "10.244.1.22"
MONITOR_POD_MAC = "02:42:0a:f4:01:16"

# Health-check pod (also talks to API - decoy)
HEALTH_POD_IP = "10.244.1.33"
HEALTH_POD_MAC = "02:42:0a:f4:01:21"

NORMAL_PODS = [
    ("10.244.1.10", "02:42:0a:f4:01:0a"),
    ("10.244.1.15", "02:42:0a:f4:01:0f"),
    ("10.244.1.55", "02:42:0a:f4:01:37"),
    ("10.244.1.60", "02:42:0a:f4:01:3c"),
]

XOR_KEY = b"k8s_breach"


def make_jwt(service_account: str, namespace: str) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "kid": "cluster-signing-key-001"}).encode()).decode().rstrip("=")
    payload_data = {
        "iss": "kubernetes/serviceaccount",
        "kubernetes.io/serviceaccount/namespace": namespace,
        "kubernetes.io/serviceaccount/service-account.name": service_account,
        "kubernetes.io/serviceaccount/service-account.uid": f"a1b2c3d4-{rand_str(4)}-{rand_str(4)}-{rand_str(12)}",
        "sub": f"system:serviceaccount:{namespace}:{service_account}",
        "iat": 1720224000,
        "exp": 1751760000,
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(hashlib.sha256(f"{header}.{payload}".encode()).digest()).decode().rstrip("=")
    return f"{header}.{payload}.{sig}"


def build_pkt(src_ip, src_mac, dst_ip, dst_mac, sport, dport, payload_str):
    return (Ether(src=src_mac, dst=dst_mac) /
            IP(src=src_ip, dst=dst_ip) /
            TCP(sport=sport, dport=dport, flags="PA",
                seq=random.randint(100000, 999999), ack=random.randint(100000, 999999)) /
            Raw(load=payload_str.encode()))


def api_req(src_ip, src_mac, token, method, path):
    sport = random.randint(40000, 60000)
    req = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host: kubernetes.default.svc\r\n"
        f"Authorization: Bearer {token}\r\n"
        f"Accept: application/json\r\n"
        f"User-Agent: kubectl/v1.28.0 (linux/amd64)\r\n"
        f"\r\n"
    )
    return build_pkt(src_ip, src_mac, API_SERVER_IP, API_SERVER_MAC, sport, 6443, req), sport


def api_resp(sport, body_json, status="200 OK"):
    body = json.dumps(body_json)
    resp = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"\r\n"
        f"{body}"
    )
    return build_pkt(API_SERVER_IP, API_SERVER_MAC, ATTACKER_POD_IP, ATTACKER_POD_MAC, 6443, sport, resp)


def api_resp_to(dst_ip, dst_mac, sport, body_json, status="200 OK"):
    body = json.dumps(body_json)
    resp = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"\r\n"
        f"{body}"
    )
    return build_pkt(API_SERVER_IP, API_SERVER_MAC, dst_ip, dst_mac, 6443, sport, resp)


def gen_normal_traffic(count=8):
    packets = []
    for _ in range(count):
        src_ip, src_mac = random.choice(NORMAL_PODS)
        dst_ip, dst_mac = random.choice(NORMAL_PODS)
        if src_ip == dst_ip:
            continue
        pkt = (Ether(src=src_mac, dst=dst_mac) /
               IP(src=src_ip, dst=dst_ip) /
               TCP(sport=random.randint(30000, 60000),
                   dport=random.choice([80, 443, 3306, 6379, 8080, 9090]),
                   flags=random.choice(["A", "PA"])))
        packets.append(pkt)
    return packets


def gen_monitor_decoy(monitor_token):
    """Legitimate monitoring pod checking API health - DECOY."""
    packets = []
    req, sport = api_req(MONITOR_POD_IP, MONITOR_POD_MAC, monitor_token, "GET", "/api/v1/nodes")
    packets.append(req)
    packets.append(api_resp_to(MONITOR_POD_IP, MONITOR_POD_MAC, sport, {
        "kind": "NodeList", "items": [
            {"metadata": {"name": "worker-1"}, "status": {"conditions": [{"type": "Ready", "status": "True"}]}},
            {"metadata": {"name": "worker-2"}, "status": {"conditions": [{"type": "Ready", "status": "True"}]}},
        ]
    }))
    return packets


def gen_health_decoy(health_token):
    """Health-check pod querying pod status - DECOY."""
    packets = []
    req, sport = api_req(HEALTH_POD_IP, HEALTH_POD_MAC, health_token, "GET", "/api/v1/namespaces/production/pods")
    packets.append(req)
    packets.append(api_resp_to(HEALTH_POD_IP, HEALTH_POD_MAC, sport, {
        "kind": "PodList", "items": [
            {"metadata": {"name": "web-frontend-abc123"}, "status": {"phase": "Running"}},
            {"metadata": {"name": "api-backend-def456"}, "status": {"phase": "Running"}},
        ]
    }))
    return packets


def generate_pcap(output_path: str, seed: str = None):
    if seed:
        random.seed(seed)

    flag = get_flag()
    # XOR encode then base64 the flag (extra decode step)
    flag_xored = xor_encode(flag.encode(), XOR_KEY)
    flag_encoded = base64.b64encode(flag_xored).decode()

    # Tokens
    low_priv_sa = "webapp-sa"
    high_priv_sa = "cluster-backup-sa"
    monitor_sa = "prometheus-sa"
    health_sa = "liveness-probe-sa"

    low_token = make_jwt(low_priv_sa, "production")
    high_token = make_jwt(high_priv_sa, "production")
    monitor_token = make_jwt(monitor_sa, "monitoring")
    health_token = make_jwt(health_sa, "kube-system")

    print(f"[*] Flag: {flag}")
    print(f"[*] XOR key: {XOR_KEY.decode()}")
    print(f"[*] Flag encoded: {flag_encoded}")
    print(f"[*] Low-priv SA: {low_priv_sa}")
    print(f"[*] High-priv SA: {high_priv_sa}")
    print(f"[*] Attacker: {ATTACKER_POD_IP}")

    all_packets = []

    # === Phase 1: Normal cluster traffic + decoy API calls ===
    all_packets.extend(gen_normal_traffic(12))
    all_packets.extend(gen_monitor_decoy(monitor_token))
    all_packets.extend(gen_normal_traffic(5))
    all_packets.extend(gen_health_decoy(health_token))
    all_packets.extend(gen_normal_traffic(8))

    # === Phase 2: Attacker uses low-priv token to enumerate ===
    # Try to list secrets - DENIED
    req, sport = api_req(ATTACKER_POD_IP, ATTACKER_POD_MAC, low_token, "GET", "/api/v1/namespaces/production/secrets")
    all_packets.append(req)
    all_packets.extend(gen_normal_traffic(2))
    all_packets.append(api_resp(sport, {
        "kind": "Status", "status": "Failure",
        "message": f"secrets is forbidden: User \"system:serviceaccount:production:{low_priv_sa}\" cannot list resource \"secrets\"",
        "reason": "Forbidden", "code": 403
    }, status="403 Forbidden"))

    all_packets.extend(gen_normal_traffic(4))

    # List pods (allowed) - looking for privileged SAs
    req, sport = api_req(ATTACKER_POD_IP, ATTACKER_POD_MAC, low_token, "GET", "/api/v1/namespaces/production/pods")
    all_packets.append(req)
    all_packets.extend(gen_normal_traffic(2))
    all_packets.append(api_resp(sport, {
        "kind": "PodList", "items": [
            {"metadata": {"name": "web-frontend-7b4d9f-x2k4m", "namespace": "production"},
             "spec": {"serviceAccountName": "webapp-sa",
                      "containers": [{"name": "nginx", "image": "nginx:1.25"}]}},
            {"metadata": {"name": "api-backend-5c8f7d-j8n3p", "namespace": "production"},
             "spec": {"serviceAccountName": "webapp-sa",
                      "containers": [{"name": "node", "image": "node:20-slim"}]}},
            {"metadata": {"name": "cluster-backup-cronjob-28xk2", "namespace": "production",
                          "labels": {"app": "cluster-backup", "schedule": "nightly"}},
             "spec": {"serviceAccountName": high_priv_sa,
                      "automountServiceAccountToken": True,
                      "containers": [{"name": "backup", "image": "bitnami/kubectl:1.28",
                                      "env": [{"name": "BACKUP_TARGET", "value": "s3://novacorp-backups/"}],
                                      "volumeMounts": [{"name": "sa-token",
                                                        "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount",
                                                        "readOnly": True}]}]}},
            {"metadata": {"name": "redis-master-0", "namespace": "production"},
             "spec": {"serviceAccountName": "default",
                      "containers": [{"name": "redis", "image": "redis:7-alpine"}]}},
        ]
    }))

    all_packets.extend(gen_normal_traffic(6))
    all_packets.extend(gen_monitor_decoy(monitor_token))  # More decoy noise
    all_packets.extend(gen_normal_traffic(4))

    # === Phase 3: Attacker reads backup pod logs (looking for token leak) ===
    req, sport = api_req(ATTACKER_POD_IP, ATTACKER_POD_MAC, low_token, "GET",
                         "/api/v1/namespaces/production/pods/cluster-backup-cronjob-28xk2/log")
    all_packets.append(req)
    all_packets.extend(gen_normal_traffic(2))
    # Logs accidentally leak the high-priv token
    backup_log = (
        f"[2026-07-06T01:30:00Z] Starting nightly backup\n"
        f"[2026-07-06T01:30:01Z] Loading service account from /var/run/secrets/kubernetes.io/serviceaccount/token\n"
        f"[2026-07-06T01:30:01Z] Token: {high_token}\n"
        f"[2026-07-06T01:30:02Z] Authenticating to kubernetes.default.svc\n"
        f"[2026-07-06T01:30:03Z] Backup completed: 42 resources archived\n"
    )
    resp_str = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: text/plain\r\n"
        f"Content-Length: {len(backup_log)}\r\n"
        f"\r\n"
        f"{backup_log}"
    )
    all_packets.append(build_pkt(API_SERVER_IP, API_SERVER_MAC,
                                  ATTACKER_POD_IP, ATTACKER_POD_MAC, 6443, sport, resp_str))

    all_packets.extend(gen_normal_traffic(8))
    all_packets.extend(gen_health_decoy(health_token))  # More decoy

    # === Phase 4: Attacker uses HIGH-PRIV token to read secrets ===
    all_packets.extend(gen_normal_traffic(5))

    req, sport = api_req(ATTACKER_POD_IP, ATTACKER_POD_MAC, high_token, "GET", "/api/v1/namespaces/production/secrets")
    all_packets.append(req)
    all_packets.extend(gen_normal_traffic(2))
    all_packets.append(api_resp(sport, {
        "kind": "SecretList", "items": [
            {"metadata": {"name": "db-credentials"}, "type": "Opaque"},
            {"metadata": {"name": "tls-wildcard"}, "type": "kubernetes.io/tls"},
            {"metadata": {"name": "docker-registry-auth"}, "type": "kubernetes.io/dockerconfigjson"},
            {"metadata": {"name": "api-signing-key"}, "type": "Opaque"},
            {"metadata": {"name": "flag-secret"}, "type": "Opaque"},
            {"metadata": {"name": "aws-credentials"}, "type": "Opaque"},
        ]
    }))

    all_packets.extend(gen_normal_traffic(4))

    # Read the flag secret
    req, sport = api_req(ATTACKER_POD_IP, ATTACKER_POD_MAC, high_token, "GET",
                         "/api/v1/namespaces/production/secrets/flag-secret")
    all_packets.append(req)
    all_packets.extend(gen_normal_traffic(2))
    all_packets.append(api_resp(sport, {
        "kind": "Secret",
        "apiVersion": "v1",
        "metadata": {"name": "flag-secret", "namespace": "production",
                     "annotations": {"encoding": "xor+base64", "key": "k8s_breach"}},
        "type": "Opaque",
        "data": {"flag": base64.b64encode(flag_encoded.encode()).decode()}
    }))

    # === Phase 5: Post-exfil noise ===
    all_packets.extend(gen_normal_traffic(15))
    all_packets.extend(gen_monitor_decoy(monitor_token))
    all_packets.extend(gen_normal_traffic(8))

    wrpcap(output_path, all_packets)
    print(f"[+] PCAP written to: {output_path}")
    print(f"[+] Total packets: {len(all_packets)}")

    meta_path = output_path.replace(".pcap", "_meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"flag={flag}\n")
        f.write(f"xor_key={XOR_KEY.decode()}\n")
        f.write(f"flag_encoded={flag_encoded}\n")
        f.write(f"low_priv_sa={low_priv_sa}\n")
        f.write(f"high_priv_sa={high_priv_sa}\n")
        f.write(f"attacker_ip={ATTACKER_POD_IP}\n")
        f.write(f"pivot_point=pod logs leak high-priv token\n")
    print(f"[+] Metadata: {meta_path}")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else "cloud_breach.pcap"
    generate_pcap(output, seed)
