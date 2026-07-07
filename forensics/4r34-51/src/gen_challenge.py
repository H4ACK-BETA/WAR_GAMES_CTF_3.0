#!/usr/bin/env python3
"""
4r34::51 — PCAP Generator

Generates a forensics challenge PCAP simulating a 45-second data breach:
1. HTTP file transfer — an encrypted ZIP archive exfiltrated via HTTP POST
2. DNS exfil — the ZIP password hidden in DNS TXT query subdomains
3. Noise — legitimate-looking traffic to pad the capture

Twist: the password is split across multiple DNS queries (hex-encoded in subdomains).

Dependencies: scapy, zip (system command)
"""
import os
import sys
import random
import string
import base64
import struct
import hashlib
import time
import subprocess
import tempfile
from io import BytesIO

from scapy.all import (
    Ether, IP, UDP, TCP, DNS, DNSQR, DNSRR,
    Raw, wrpcap, RandMAC
)


def rand_str(n, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(n))


def get_flag():
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()
    return "WarCTF{th3_truth_1s_0ut_th3r3_45s_w4s_3n0ugh}"


def rand_password():
    return "COSMIC-" + rand_str(6, string.ascii_uppercase + string.digits) + "-UMBRA"


# Network layout
INTRUDER_IP = "198.51.100.47"
INTRUDER_MAC = "de:ad:be:ef:ca:fe"
ROSWELL_IP = "10.51.0.13"
ROSWELL_MAC = "00:51:a1:ea:51:13"
DNS_RESOLVER_IP = "10.51.0.1"
DNS_RESOLVER_MAC = "00:51:a1:00:00:01"
NOISE_IPS = ["10.51.0.20", "10.51.0.21", "10.51.0.30", "10.51.0.50"]


def create_encrypted_zip(flag: str, password: str) -> bytes:
    """Create a password-protected ZIP containing the classified document."""
    tmp_dir = tempfile.mkdtemp()
    doc_path = os.path.join(tmp_dir, "classified_document.txt")
    zip_path = os.path.join(tmp_dir, "output.zip")

    classified_content = f"""TOP SECRET // UMBRA // COSMIC
==============================
PROJECT ROSWELL - STATUS REPORT
Date: 2026-07-05
Classification: TS//UMBRA

EXECUTIVE SUMMARY:
The artifact recovered from Site 51-B continues to emit
low-frequency electromagnetic pulses at 3.7Hz intervals.
Research team Sigma-7 has confirmed non-terrestrial origin.

CRITICAL DATA (DO NOT DISTRIBUTE):
{flag}

-- END OF DOCUMENT --
"""
    with open(doc_path, 'w') as f:
        f.write(classified_content)

    result = subprocess.run(
        ["zip", "-j", "-P", password, zip_path, doc_path],
        capture_output=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"zip failed: {result.stderr.decode()}")

    with open(zip_path, 'rb') as f:
        data = f.read()

    os.unlink(doc_path)
    os.unlink(zip_path)
    os.rmdir(tmp_dir)
    return data


def gen_dns_password_exfil(password: str):
    """
    Exfiltrate the ZIP password via DNS queries.
    Password is hex-encoded and split across TXT queries to subdomains.
    Pattern: <hex_chunk>.exfil.area51.internal
    """
    packets = []
    hex_pass = password.encode().hex()

    # Split into chunks of 8 hex chars
    chunks = [hex_pass[i:i+8] for i in range(0, len(hex_pass), 8)]

    for idx, chunk in enumerate(chunks):
        qname = f"{idx:02d}-{chunk}.data.ns1.area51-research.internal"

        query = (
            Ether(src=ROSWELL_MAC, dst=DNS_RESOLVER_MAC) /
            IP(src=ROSWELL_IP, dst=DNS_RESOLVER_IP) /
            UDP(sport=random.randint(49152, 65535), dport=53) /
            DNS(rd=1, qd=DNSQR(qname=qname, qtype="TXT"))
        )
        packets.append(query)

        # Response (NXDOMAIN — the domain doesn't exist, but the data was sent)
        response = (
            Ether(src=DNS_RESOLVER_MAC, dst=ROSWELL_MAC) /
            IP(src=DNS_RESOLVER_IP, dst=ROSWELL_IP) /
            UDP(sport=53, dport=query[UDP].sport) /
            DNS(id=query[DNS].id, qr=1, rcode=3, qd=query[DNS].qd)  # NXDOMAIN
        )
        packets.append(response)

    return packets


def gen_http_file_transfer(zip_data: bytes):
    """
    Simulate HTTP POST exfiltration of the encrypted archive.
    Intruder downloads the file from ROSWELL via HTTP GET.
    """
    packets = []
    http_port = 8080
    client_port = random.randint(49152, 65535)
    seq_c = random.randint(100000, 999999)
    seq_s = random.randint(100000, 999999)

    # TCP handshake
    packets.append(Ether(src=INTRUDER_MAC, dst=ROSWELL_MAC) /
                   IP(src=INTRUDER_IP, dst=ROSWELL_IP) /
                   TCP(sport=client_port, dport=http_port, flags="S", seq=seq_c))
    packets.append(Ether(src=ROSWELL_MAC, dst=INTRUDER_MAC) /
                   IP(src=ROSWELL_IP, dst=INTRUDER_IP) /
                   TCP(sport=http_port, dport=client_port, flags="SA", seq=seq_s, ack=seq_c + 1))
    seq_c += 1

    # HTTP GET request
    http_req = (
        b"GET /vault/classified_archive.zip HTTP/1.1\r\n"
        b"Host: 10.51.0.13:8080\r\n"
        b"User-Agent: wget/1.21 (linux-gnu)\r\n"
        b"Accept: */*\r\n"
        b"X-Auth-Token: COSMIC-7f3a9b2e1d\r\n"
        b"\r\n"
    )
    packets.append(Ether(src=INTRUDER_MAC, dst=ROSWELL_MAC) /
                   IP(src=INTRUDER_IP, dst=ROSWELL_IP) /
                   TCP(sport=client_port, dport=http_port, flags="PA", seq=seq_c, ack=seq_s + 1) /
                   Raw(load=http_req))
    seq_c += len(http_req)

    # HTTP response with ZIP file
    http_resp_header = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: application/zip\r\n"
        f"Content-Disposition: attachment; filename=\"classified_archive.zip\"\r\n"
        f"Content-Length: {len(zip_data)}\r\n"
        f"Server: roswell-internal/0.1\r\n"
        f"X-Classification: TOP-SECRET\r\n"
        f"\r\n"
    ).encode()

    # Wrap in NetBIOS-style header for scapy compatibility on response
    full_response = http_resp_header + zip_data

    packets.append(Ether(src=ROSWELL_MAC, dst=INTRUDER_MAC) /
                   IP(src=ROSWELL_IP, dst=INTRUDER_IP) /
                   TCP(sport=http_port, dport=client_port, flags="PA", seq=seq_s + 1, ack=seq_c) /
                   Raw(load=full_response))

    # FIN
    packets.append(Ether(src=INTRUDER_MAC, dst=ROSWELL_MAC) /
                   IP(src=INTRUDER_IP, dst=ROSWELL_IP) /
                   TCP(sport=client_port, dport=http_port, flags="FA", seq=seq_c, ack=seq_s + 1 + len(full_response)))

    return packets


def gen_noise_packets(count=25):
    """Generate background noise traffic."""
    packets = []
    legit_domains = [
        "time.nist.gov", "updates.security.mil", "ldap.area51.internal",
        "mail.area51.internal", "ntp.area51.internal", "siem.area51.internal",
    ]

    for _ in range(count // 2):
        # DNS noise
        domain = random.choice(legit_domains)
        pkt = (Ether(src=RandMAC(), dst=DNS_RESOLVER_MAC) /
               IP(src=random.choice(NOISE_IPS), dst=DNS_RESOLVER_IP) /
               UDP(sport=random.randint(49152, 65535), dport=53) /
               DNS(rd=1, qd=DNSQR(qname=domain, qtype="A")))
        packets.append(pkt)

    for _ in range(count // 2):
        # TCP noise (SSH, HTTPS heartbeats)
        src = random.choice(NOISE_IPS)
        dst = random.choice(NOISE_IPS)
        if src == dst:
            continue
        pkt = (Ether(src=RandMAC(), dst=RandMAC()) /
               IP(src=src, dst=dst) /
               TCP(sport=random.randint(1024, 65535),
                   dport=random.choice([22, 443, 8443, 3389]),
                   flags=random.choice(["A", "PA"])))
        packets.append(pkt)

    return packets


def generate_pcap(output_path: str, seed: str = None):
    """Main generator."""
    if seed:
        random.seed(seed)

    flag = get_flag()
    password = rand_password()

    print(f"[*] Flag: {flag}")
    print(f"[*] ZIP password: {password}")

    zip_data = create_encrypted_zip(flag, password)
    print(f"[*] ZIP size: {len(zip_data)} bytes")

    all_packets = []

    # Phase 1: Pre-breach noise (seconds 0-5)
    all_packets.extend(gen_noise_packets(10))

    # Phase 2: DNS exfiltration of password (seconds 5-15)
    all_packets.extend(gen_noise_packets(3))
    all_packets.extend(gen_dns_password_exfil(password))
    all_packets.extend(gen_noise_packets(3))

    # Phase 3: HTTP file exfiltration (seconds 15-35)
    all_packets.extend(gen_noise_packets(5))
    all_packets.extend(gen_http_file_transfer(zip_data))
    all_packets.extend(gen_noise_packets(5))

    # Phase 4: Post-breach noise (seconds 35-45)
    all_packets.extend(gen_noise_packets(10))

    wrpcap(output_path, all_packets)
    print(f"[+] PCAP written to: {output_path}")
    print(f"[+] Total packets: {len(all_packets)}")

    meta_path = output_path.replace(".pcap", "_meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"flag={flag}\n")
        f.write(f"zip_password={password}\n")
        f.write(f"intruder_ip={INTRUDER_IP}\n")
        f.write(f"roswell_ip={ROSWELL_IP}\n")
        f.write(f"dns_pattern=<idx>-<hex_chunk>.data.ns1.area51-research.internal\n")
    print(f"[+] Metadata: {meta_path}")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else "exposure_window.pcap"
    generate_pcap(output, seed)
