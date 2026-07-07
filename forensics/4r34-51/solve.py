#!/usr/bin/env python3
"""
4r34::51 — Solve Script

Steps:
1. Identify the suspicious host (external IP 198.51.100.47)
2. Extract the encrypted ZIP from HTTP traffic (GET response on port 8080)
3. Recover the ZIP password from DNS exfil queries
   Pattern: <idx>-<hex_chunk>.data.ns1.area51-research.internal
4. Decrypt ZIP → read classified_document.txt → flag
"""
import sys
import os
import re
import tempfile
import zipfile

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

    # Step 1: Identify suspicious host
    print("[1] Identifying suspicious external host...")
    external_ips = set()
    for pkt in packets:
        if pkt.haslayer(IP):
            src = pkt[IP].src
            if not src.startswith("10."):
                external_ips.add(src)
    print(f"    External IPs found: {external_ips}")
    print()

    # Step 2: Recover password from DNS exfil
    print("[2] Extracting password from DNS queries...")
    dns_chunks = {}
    for pkt in packets:
        if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
            if pkt[DNS].qr == 0:
                qname = pkt[DNSQR].qname.decode().rstrip(".")
                if "area51-research.internal" in qname:
                    # Pattern: <idx>-<hex_chunk>.data.ns1.area51-research.internal
                    match = re.match(r'(\d+)-([a-f0-9]+)\.data\.ns1\.area51-research\.internal', qname)
                    if match:
                        idx = int(match.group(1))
                        chunk = match.group(2)
                        dns_chunks[idx] = chunk

    if not dns_chunks:
        print("    [-] No DNS exfil pattern found!")
        return

    hex_password = ''.join(dns_chunks[i] for i in sorted(dns_chunks.keys()))
    password = bytes.fromhex(hex_password).decode()
    print(f"    DNS chunks: {len(dns_chunks)}")
    print(f"    Recovered password: {password}")
    print()

    # Step 3: Extract ZIP from HTTP response
    print("[3] Extracting file from HTTP traffic...")
    zip_data = None
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw):
            data = bytes(pkt[Raw].load)
            if b"HTTP/1.1 200 OK" in data and b"application/zip" in data:
                # Find end of HTTP headers
                header_end = data.find(b"\r\n\r\n")
                if header_end != -1:
                    zip_data = data[header_end + 4:]
                    break

    if not zip_data:
        print("    [-] No ZIP found in HTTP traffic!")
        return

    print(f"    Extracted: {len(zip_data)} bytes")
    print()

    # Step 4: Decrypt and read
    print("[4] Decrypting archive...")
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.write(zip_data)
    tmp.close()

    try:
        with zipfile.ZipFile(tmp.name, 'r') as zf:
            zf.setpassword(password.encode())
            names = zf.namelist()
            print(f"    Files: {names}")
            for name in names:
                content = zf.read(name).decode()
                flag_match = re.search(r'(WarCTF\{[^}]+\})', content)
                if flag_match:
                    print()
                    print(f"[+] FLAG: {flag_match.group(1)}")
                    break
            else:
                print(f"    Document content:\n{content[:500]}")
    except Exception as e:
        print(f"    [-] Failed: {e}")
    finally:
        os.unlink(tmp.name)


if __name__ == "__main__":
    pcap_file = sys.argv[1] if len(sys.argv) > 1 else "exposure_window.pcap"
    solve(pcap_file)
