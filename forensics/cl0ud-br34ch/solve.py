#!/usr/bin/env python3
"""
cl0ud::br34ch - Solve Script (Hard+)

Steps:
1. Find pods talking to API (10.96.0.1:6443) - multiple exist (decoys!)
2. Identify the attacker: the one that gets 403 first, then pivots to a new token
3. First token is low-priv (webapp-sa) - gets denied on secrets
4. Attacker reads backup pod logs - finds high-priv token leaked there
5. Pivots: uses new token (cluster-backup-sa) to read secrets
6. Flag is triple-encoded: base64(base64(xor(flag, "k8s_breach")))
7. The annotations hint at the encoding scheme
"""
import sys
import os
import re
import json
import base64

try:
    from scapy.all import rdpcap, TCP, IP, Raw
except ImportError:
    print("[!] Install scapy: pip install scapy")
    sys.exit(1)


def xor_decode(data: bytes, key: bytes) -> bytes:
    return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))


def solve(pcap_path):
    print(f"[*] Loading {pcap_path}...")
    packets = rdpcap(pcap_path)
    print(f"[*] {len(packets)} packets loaded")
    print()

    API_SERVER = "10.96.0.1"

    # Step 1: Find ALL pods talking to API
    print("[1] Identifying pods communicating with K8s API...")
    api_talkers = {}
    for pkt in packets:
        if pkt.haslayer(IP) and pkt.haslayer(TCP):
            if pkt[IP].dst == API_SERVER and pkt[TCP].dport == 6443:
                src = pkt[IP].src
                api_talkers[src] = api_talkers.get(src, 0) + 1

    print(f"    Pods talking to API server:")
    for ip, count in sorted(api_talkers.items(), key=lambda x: -x[1]):
        print(f"      {ip}: {count} packets")
    print()

    # Step 2: Find the attacker - look for 403 responses (privilege escalation attempt)
    print("[2] Finding privilege escalation attempts (403 responses)...")
    attacker_ip = None
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP):
            if pkt[IP].src == API_SERVER:
                data = bytes(pkt[Raw].load).decode(errors='ignore')
                if "403 Forbidden" in data and "cannot list resource" in data:
                    # Find who this response was sent to
                    target = pkt[IP].dst
                    print(f"    403 sent to: {target}")
                    attacker_ip = target
                    break

    if not attacker_ip:
        # Fallback: most active non-monitoring pod
        attacker_ip = max(api_talkers, key=api_talkers.get)
    print(f"    Attacker identified: {attacker_ip}")
    print()

    # Step 3: Extract tokens used by attacker
    print("[3] Extracting tokens used by attacker...")
    tokens = []
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP):
            if pkt[IP].src == attacker_ip and pkt[IP].dst == API_SERVER:
                data = bytes(pkt[Raw].load).decode(errors='ignore')
                match = re.search(r'Authorization: Bearer ([A-Za-z0-9_\-\.]+)', data)
                if match:
                    t = match.group(1)
                    if t not in tokens:
                        tokens.append(t)

    print(f"    Unique tokens found: {len(tokens)}")
    for i, t in enumerate(tokens):
        parts = t.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
            try:
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                sa = payload.get("kubernetes.io/serviceaccount/service-account.name", "?")
                print(f"      Token {i+1}: {sa}")
            except:
                print(f"      Token {i+1}: (decode failed)")
    print()

    # Step 4: Find the pivot - token leaked in pod logs
    print("[4] Finding token pivot (leaked in pod logs)...")
    leaked_token = None
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP):
            if pkt[IP].src == API_SERVER and pkt[IP].dst == attacker_ip:
                data = bytes(pkt[Raw].load).decode(errors='ignore')
                if "Token:" in data and "backup" in data.lower():
                    match = re.search(r'Token: ([A-Za-z0-9_\-\.]+)', data)
                    if match:
                        leaked_token = match.group(1)
                        print(f"    Found leaked token in backup pod logs!")
                        parts = leaked_token.split(".")
                        if len(parts) >= 2:
                            payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                            sa = payload.get("kubernetes.io/serviceaccount/service-account.name", "?")
                            print(f"    Leaked SA: {sa} (high-privilege)")
                        break

    print()

    # Step 5: Find the flag secret response
    print("[5] Extracting flag from secrets response...")
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP):
            if pkt[IP].src == API_SERVER:
                data = bytes(pkt[Raw].load).decode(errors='ignore')
                if '"flag-secret"' in data and '"data"' in data and '"kind": "Secret"' in data:
                    body_match = re.search(r'\r\n\r\n(.+)', data, re.DOTALL)
                    if body_match:
                        try:
                            body = json.loads(body_match.group(1))
                            annotations = body.get("metadata", {}).get("annotations", {})
                            encoding = annotations.get("encoding", "")
                            xor_key = annotations.get("key", "")
                            flag_data_b64 = body.get("data", {}).get("flag", "")

                            print(f"    Encoding scheme: {encoding}")
                            print(f"    XOR key: {xor_key}")
                            print(f"    Raw data field: {flag_data_b64[:60]}...")

                            # Decode: base64 -> base64 string -> xor decode
                            step1 = base64.b64decode(flag_data_b64).decode()
                            print(f"    After outer base64: {step1[:60]}...")
                            step2 = base64.b64decode(step1)
                            print(f"    After inner base64: {step2[:30].hex()}...")
                            flag = xor_decode(step2, xor_key.encode()).decode()

                            print()
                            print(f"[+] FLAG: {flag}")
                            return
                        except Exception as e:
                            print(f"    Decode error: {e}")

    print("    [-] Flag not found")


if __name__ == "__main__":
    pcap_file = sys.argv[1] if len(sys.argv) > 1 else "cloud_breach.pcap"
    solve(pcap_file)
