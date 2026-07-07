#!/usr/bin/env python3
"""
gh0st::exf1l — Solve Script

Steps:
1. Parse DNS queries → find unusual hostname (non-standard subdomain)
2. Parse HTTP traffic → extract Basic Auth credentials (ZIP password)
3. Parse SMB/TCP port 445 traffic → reconstruct the ZIP file
4. Decrypt ZIP with the password → extract flag.txt
"""
import sys
import os
import base64
import struct
from io import BytesIO

try:
    from scapy.all import rdpcap, TCP, UDP, DNS, DNSQR, Raw, IP
except ImportError:
    print("[!] Install scapy: pip install scapy")
    sys.exit(1)


def solve(pcap_path):
    print(f"[*] Loading {pcap_path}...")
    packets = rdpcap(pcap_path)
    print(f"[*] {len(packets)} packets loaded")
    print()

    # Step 1: Find suspicious DNS queries
    print("[1] Analyzing DNS queries...")
    dns_queries = set()
    for pkt in packets:
        if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
            if pkt[DNS].qr == 0:  # Query
                qname = pkt[DNSQR].qname.decode().rstrip(".")
                dns_queries.add(qname)

    suspicious = [q for q in dns_queries if "novacorp.io" in q and
                  any(x in q for x in ["data-sync", "repo-mirror", "log-collect",
                                        "metric-push", "file-relay", "cache-warm"])]
    print(f"    All queries: {len(dns_queries)}")
    print(f"    Suspicious hostnames: {suspicious}")
    print()

    # Step 2: Extract HTTP Basic Auth
    print("[2] Extracting HTTP credentials...")
    zip_password = None
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw):
            payload = pkt[Raw].load
            if b"Authorization: Basic " in payload:
                auth_line = [l for l in payload.split(b"\r\n") if b"Authorization: Basic " in l][0]
                b64_creds = auth_line.split(b"Basic ")[1].strip()
                creds = base64.b64decode(b64_creds).decode()
                username, password = creds.split(":", 1)
                zip_password = password
                print(f"    Found: {username}:{password}")
                break

    if not zip_password:
        print("    [-] No HTTP Basic Auth found!")
        return
    print()

    # Step 3: Reconstruct ZIP from SMB traffic (port 445)
    print("[3] Reconstructing file from SMB traffic (port 445)...")
    from scapy.all import NBTSession
    zip_data = None

    for pkt in packets:
        if pkt.haslayer(TCP) and pkt[TCP].dport == 445:
            payload = None
            # Scapy parses port 445 as NBTSession
            if pkt.haslayer(NBTSession):
                # Get everything after NBTSession header
                payload = bytes(pkt[NBTSession].payload)
                if not payload and pkt.haslayer(Raw):
                    payload = bytes(pkt[Raw].load)
            elif pkt.haslayer(Raw):
                payload = bytes(pkt[Raw].load)

            if payload and b'PK\x03\x04' in payload:
                pk_idx = payload.find(b'PK\x03\x04')
                zip_data = payload[pk_idx:]
                break
            elif payload and len(payload) > 150:
                # Could be the ZIP without standard header (AES encrypted)
                zip_data = payload
                break

    if not zip_data:
        print("    [-] No ZIP file found in SMB traffic!")
        print("    [*] Tip: Follow TCP stream on port 445 in Wireshark")
        return

    print(f"    Extracted: {len(zip_data)} bytes")
    print()

    # Step 4: Decrypt ZIP
    print("[4] Decrypting ZIP with password...")
    try:
        import tempfile, zipfile
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.write(zip_data)
        tmp.close()

        with zipfile.ZipFile(tmp.name, 'r') as zf:
            zf.setpassword(zip_password.encode())
            names = zf.namelist()
            print(f"    Files in ZIP: {names}")
            for name in names:
                content = zf.read(name).decode()
                print(f"    {name}: {content}")
                if "CTF{" in content or "WarCTF{" in content:
                    print()
                    print(f"[+] FLAG: {content.strip()}")

        os.unlink(tmp.name)
    except Exception as e:
        print(f"    [-] Decryption failed: {e}")
        print(f"    [*] Try manually: unzip -P '{zip_password}' extracted.zip")


if __name__ == "__main__":
    pcap_file = sys.argv[1] if len(sys.argv) > 1 else "capture.pcap"
    solve(pcap_file)
