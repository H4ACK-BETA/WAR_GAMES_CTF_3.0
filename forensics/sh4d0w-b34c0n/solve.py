#!/usr/bin/env python3
"""
sh4d0w::b34c0n — Solve Script

Steps:
1. Identify beaconing traffic (periodic HTTP to same IP)
2. Decode C2 commands from beacon responses (base64 in JSON)
3. Find exfiltration POSTs (d= parameter in body)
4. Reassemble chunks in order and base64 decode → flag
"""
import sys
import os
import re
import base64
import urllib.parse

try:
    from scapy.all import rdpcap, TCP, IP, Raw
except ImportError:
    print("[!] Install scapy: pip install scapy")
    sys.exit(1)


def solve(pcap_path):
    print(f"[*] Loading {pcap_path}...")
    packets = rdpcap(pcap_path)
    print(f"[*] {len(packets)} packets loaded")
    print()

    # Step 1: Identify C2 server (most contacted external IP)
    print("[1] Identifying beacon target (C2 server)...")
    ip_count = {}
    for pkt in packets:
        if pkt.haslayer(IP) and pkt.haslayer(TCP):
            dst = pkt[IP].dst
            if not dst.startswith("10."):
                ip_count[dst] = ip_count.get(dst, 0) + 1

    if ip_count:
        c2_ip = max(ip_count, key=ip_count.get)
        print(f"    C2 server: {c2_ip} ({ip_count[c2_ip]} packets)")
    else:
        print("    [-] No external IPs found")
        return
    print()

    # Step 2: Decode C2 commands from responses
    print("[2] Decoding C2 commands from beacon responses...")
    commands = []
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP):
            if pkt[IP].src == c2_ip:
                data = bytes(pkt[Raw].load).decode(errors='ignore')
                # Look for JSON with "data" field containing base64
                match = re.search(r'"data":"([A-Za-z0-9+/=]+)"', data)
                if match:
                    cmd_b64 = match.group(1)
                    try:
                        cmd = base64.b64decode(cmd_b64).decode()
                        commands.append(cmd)
                    except Exception:
                        pass

    print(f"    Commands decoded: {len(commands)}")
    for i, cmd in enumerate(commands):
        print(f"      [{i}] {cmd}")
    print()

    # Step 3: Extract exfiltrated data from POST bodies
    print("[3] Extracting exfiltrated data chunks...")
    chunks = {}
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt.haslayer(IP):
            if pkt[IP].dst == c2_ip:
                data = bytes(pkt[Raw].load).decode(errors='ignore')
                if "POST" in data and "/telemetry" in data:
                    # Extract body after headers
                    body_match = re.search(r'\r\n\r\n(.+)', data, re.DOTALL)
                    if body_match:
                        body = body_match.group(1)
                        params = urllib.parse.parse_qs(body)
                        if 'd' in params and 'seq' in params:
                            seq = int(params['seq'][0])
                            chunk = params['d'][0]
                            chunks[seq] = chunk

    if not chunks:
        print("    [-] No exfil data found!")
        return

    print(f"    Chunks found: {len(chunks)}")
    for seq in sorted(chunks.keys()):
        print(f"      [seq={seq}] {chunks[seq]}")
    print()

    # Step 4: Reassemble and decode
    print("[4] Reassembling and decoding flag...")
    assembled_b64 = ''.join(chunks[i] for i in sorted(chunks.keys()))
    print(f"    Assembled base64: {assembled_b64}")

    try:
        flag = base64.b64decode(assembled_b64).decode()
        print()
        print(f"[+] FLAG: {flag}")
    except Exception as e:
        print(f"    [-] Decode failed: {e}")
        print(f"    [*] Try padding: {assembled_b64}=")


if __name__ == "__main__":
    pcap_file = sys.argv[1] if len(sys.argv) > 1 else "beacon_capture.pcap"
    solve(pcap_file)
