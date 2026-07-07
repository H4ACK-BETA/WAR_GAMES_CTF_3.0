#!/usr/bin/env python3
"""
gh0st::exf1l — PCAP Generator

Generates a forensics challenge PCAP containing:
1. DNS queries revealing an internal hostname (the exfil target)
2. HTTP traffic with Basic Auth (password for the ZIP)
3. SMB file transfer containing a password-protected ZIP
4. The ZIP contains a flag.txt

All values are randomized per generation:
- Internal hostname
- ZIP password
- Filenames
- Flag (from env or generated)

Dependencies: scapy, pyzipper
  pip install scapy pyzipper
"""
import os
import sys
import random
import string
import base64
import struct
import hashlib
import time
from io import BytesIO

try:
    from scapy.all import (
        Ether, IP, UDP, TCP, DNS, DNSQR, DNSRR,
        Raw, wrpcap, RandMAC
    )
except ImportError:
    print("[!] scapy not installed. Run: pip install scapy")
    sys.exit(1)


def rand_str(n, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(n))


def rand_hostname():
    prefixes = ["data-sync", "repo-mirror", "log-collect", "metric-push", "file-relay", "cache-warm"]
    suffixes = ["internal", "corp", "lan", "local", "priv"]
    return f"{random.choice(prefixes)}-{rand_str(4)}.{random.choice(suffixes)}.novacorp.io"


def rand_filename():
    names = ["backup_archive", "db_export", "quarterly_report", "config_dump", "user_data", "financial_records"]
    return f"{random.choice(names)}_{rand_str(6)}.zip"


def rand_password():
    return rand_str(8, string.ascii_letters + string.digits) + random.choice("!@#$%")


def get_flag():
    flag = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG")
    if flag:
        return flag.strip()
    return "WarCTF{gh0st_3xf1l_thr0ugh_th3_b4ckup_p1p3}"


# Network constants
BACKUP_SRV_IP = "10.10.5.30"
BACKUP_SRV_MAC = "aa:bb:cc:dd:ee:01"
EXFIL_TARGET_IP = "10.10.5.77"
EXFIL_TARGET_MAC = "aa:bb:cc:dd:ee:02"
DNS_SERVER_IP = "10.10.5.1"
DNS_SERVER_MAC = "aa:bb:cc:dd:ee:ff"
HTTP_STAGING_IP = "10.10.5.44"
HTTP_STAGING_MAC = "aa:bb:cc:dd:ee:03"


def create_encrypted_zip(flag: str, password: str, inner_filename: str = "flag.txt") -> bytes:
    """Create a password-protected ZIP using the zip command."""
    import tempfile, subprocess

    tmp_dir = tempfile.mkdtemp()
    flag_path = os.path.join(tmp_dir, inner_filename)
    zip_path = os.path.join(tmp_dir, "output.zip")

    with open(flag_path, 'w') as f:
        f.write(flag)

    result = subprocess.run(
        ["zip", "-j", "-P", password, zip_path, flag_path],
        capture_output=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"zip command failed: {result.stderr.decode()}")

    with open(zip_path, 'rb') as f:
        data = f.read()

    os.unlink(flag_path)
    os.unlink(zip_path)
    os.rmdir(tmp_dir)
    return data


def gen_noise_dns(count=15):
    """Generate benign DNS noise packets."""
    packets = []
    legit_domains = [
        "update.novacorp.io", "ntp.novacorp.io", "ldap.corp.novacorp.io",
        "smtp.novacorp.io", "monitoring.internal.novacorp.io",
        "git.dev.novacorp.io", "artifacts.build.novacorp.io",
    ]
    for _ in range(count):
        domain = random.choice(legit_domains)
        pkt = (
            Ether(src=BACKUP_SRV_MAC, dst=DNS_SERVER_MAC) /
            IP(src=BACKUP_SRV_IP, dst=DNS_SERVER_IP) /
            UDP(sport=random.randint(49152, 65535), dport=53) /
            DNS(rd=1, qd=DNSQR(qname=domain, qtype="A"))
        )
        packets.append(pkt)

        # DNS response
        resp = (
            Ether(src=DNS_SERVER_MAC, dst=BACKUP_SRV_MAC) /
            IP(src=DNS_SERVER_IP, dst=BACKUP_SRV_IP) /
            UDP(sport=53, dport=pkt[UDP].sport) /
            DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
                an=DNSRR(rrname=domain, type="A", rdata=f"10.10.{random.randint(1,254)}.{random.randint(1,254)}"))
        )
        packets.append(resp)
    return packets


def gen_exfil_dns(hostname: str):
    """Generate the suspicious DNS query for the exfil target."""
    pkt = (
        Ether(src=BACKUP_SRV_MAC, dst=DNS_SERVER_MAC) /
        IP(src=BACKUP_SRV_IP, dst=DNS_SERVER_IP) /
        UDP(sport=random.randint(49152, 65535), dport=53) /
        DNS(rd=1, qd=DNSQR(qname=hostname, qtype="A"))
    )

    resp = (
        Ether(src=DNS_SERVER_MAC, dst=BACKUP_SRV_MAC) /
        IP(src=DNS_SERVER_IP, dst=BACKUP_SRV_IP) /
        UDP(sport=53, dport=pkt[UDP].sport) /
        DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
            an=DNSRR(rrname=hostname, type="A", rdata=EXFIL_TARGET_IP))
    )
    return [pkt, resp]


def gen_http_basic_auth(password: str):
    """Generate HTTP traffic where the ZIP password leaks via Basic Auth."""
    username = "backup-agent"
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()

    syn = (Ether(src=BACKUP_SRV_MAC, dst=HTTP_STAGING_MAC) /
           IP(src=BACKUP_SRV_IP, dst=HTTP_STAGING_IP) /
           TCP(sport=44821, dport=8080, flags="S", seq=1000))

    syn_ack = (Ether(src=HTTP_STAGING_MAC, dst=BACKUP_SRV_MAC) /
               IP(src=HTTP_STAGING_IP, dst=BACKUP_SRV_IP) /
               TCP(sport=8080, dport=44821, flags="SA", seq=2000, ack=1001))

    ack = (Ether(src=BACKUP_SRV_MAC, dst=HTTP_STAGING_MAC) /
           IP(src=BACKUP_SRV_IP, dst=HTTP_STAGING_IP) /
           TCP(sport=44821, dport=8080, flags="A", seq=1001, ack=2001))

    http_req = (
        f"POST /api/staging/upload HTTP/1.1\r\n"
        f"Host: {HTTP_STAGING_IP}:8080\r\n"
        f"Authorization: Basic {creds}\r\n"
        f"Content-Type: application/octet-stream\r\n"
        f"User-Agent: backup-agent/2.1\r\n"
        f"Content-Length: 0\r\n"
        f"\r\n"
    )

    req_pkt = (Ether(src=BACKUP_SRV_MAC, dst=HTTP_STAGING_MAC) /
               IP(src=BACKUP_SRV_IP, dst=HTTP_STAGING_IP) /
               TCP(sport=44821, dport=8080, flags="PA", seq=1001, ack=2001) /
               Raw(load=http_req.encode()))

    http_resp = (
        f"HTTP/1.1 200 OK\r\n"
        f"Server: staging-relay/1.0\r\n"
        f"Content-Length: 19\r\n"
        f"\r\n"
        f"{{\"status\":\"ready\"}}"
    )

    resp_pkt = (Ether(src=HTTP_STAGING_MAC, dst=BACKUP_SRV_MAC) /
                IP(src=HTTP_STAGING_IP, dst=BACKUP_SRV_IP) /
                TCP(sport=8080, dport=44821, flags="PA", seq=2001, ack=1001 + len(http_req)) /
                Raw(load=http_resp.encode()))

    return [syn, syn_ack, ack, req_pkt, resp_pkt]


def gen_smb_transfer(zip_data: bytes, filename: str):
    """
    Generate simplified SMB-like traffic carrying the ZIP file.
    We simulate SMB2 with recognizable headers so Wireshark displays it
    as SMB traffic, and the file data is recoverable via 'Export Objects' or
    manual extraction from the TCP stream.
    """
    packets = []
    sport = random.randint(49152, 65535)
    seq = 5000
    ack = 6000

    # TCP handshake
    packets.append(Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                   IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                   TCP(sport=sport, dport=445, flags="S", seq=seq))
    packets.append(Ether(src=EXFIL_TARGET_MAC, dst=BACKUP_SRV_MAC) /
                   IP(src=EXFIL_TARGET_IP, dst=BACKUP_SRV_IP) /
                   TCP(sport=445, dport=sport, flags="SA", seq=ack, ack=seq + 1))
    seq += 1
    packets.append(Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                   IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                   TCP(sport=sport, dport=445, flags="A", seq=seq, ack=ack + 1))
    ack += 1

    # SMB2 Negotiate (simplified)
    smb2_negotiate = (
        b"\xfeSMB"  # SMB2 magic
        + b"\x40\x00"  # header size
        + b"\x00\x00"  # credit charge
        + b"\x00\x00\x00\x00"  # status
        + b"\x00\x00"  # command: negotiate
        + b"\x00\x00"  # credits
        + b"\x00" * 52  # padding
    )
    packets.append(Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                   IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                   TCP(sport=sport, dport=445, flags="PA", seq=seq, ack=ack) /
                   Raw(load=smb2_negotiate))
    seq += len(smb2_negotiate)

    # SMB2 Create (filename visible in stream)
    create_payload = (
        b"\xfeSMB"
        + b"\x40\x00"
        + b"\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x05\x00"  # command: create
        + b"\x00\x00"
        + b"\x00" * 20
        + filename.encode("utf-16-le")  # filename visible in packet
        + b"\x00" * 20
    )
    packets.append(Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                   IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                   TCP(sport=sport, dport=445, flags="PA", seq=seq, ack=ack) /
                   Raw(load=create_payload))
    seq += len(create_payload)

    # SMB2 Write — transfer the actual ZIP data in chunks
    chunk_size = 1400
    for i in range(0, len(zip_data), chunk_size):
        chunk = zip_data[i:i + chunk_size]
        write_header = (
            b"\xfeSMB"
            + b"\x40\x00"
            + b"\x00\x00"
            + b"\x00\x00\x00\x00"
            + b"\x09\x00"  # command: write
            + b"\x00\x00"
            + struct.pack("<I", i)  # offset
            + struct.pack("<I", len(chunk))  # length
            + b"\x00" * 16
        )
        packets.append(Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                       IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                       TCP(sport=sport, dport=445, flags="PA", seq=seq, ack=ack) /
                       Raw(load=write_header + chunk))
        seq += len(write_header) + len(chunk)

        # ACK from target
        packets.append(Ether(src=EXFIL_TARGET_MAC, dst=BACKUP_SRV_MAC) /
                       IP(src=EXFIL_TARGET_IP, dst=BACKUP_SRV_IP) /
                       TCP(sport=445, dport=sport, flags="A", seq=ack, ack=seq))

    return packets


def gen_noise_traffic(count=20):
    """Generate random TCP/UDP noise to make the PCAP more realistic."""
    packets = []
    for _ in range(count):
        src_ip = f"10.10.{random.randint(1,10)}.{random.randint(1,254)}"
        dst_ip = f"10.10.{random.randint(1,10)}.{random.randint(1,254)}"
        if random.random() < 0.5:
            pkt = (Ether(src=RandMAC(), dst=RandMAC()) /
                   IP(src=src_ip, dst=dst_ip) /
                   TCP(sport=random.randint(1024, 65535), dport=random.choice([80, 443, 22, 3306, 5432]),
                       flags="A"))
        else:
            pkt = (Ether(src=RandMAC(), dst=RandMAC()) /
                   IP(src=src_ip, dst=dst_ip) /
                   UDP(sport=random.randint(1024, 65535), dport=random.choice([53, 123, 514, 161])) /
                   Raw(load=os.urandom(random.randint(20, 200))))
        packets.append(pkt)
    return packets


def main():
    if len(sys.argv) > 1:
        random.seed(sys.argv[1])

    flag = get_flag()
    hostname = rand_hostname()
    zip_password = rand_password()
    zip_filename = rand_filename()

    print(f"[*] Flag: {flag}")
    print(f"[*] Exfil hostname: {hostname}")
    print(f"[*] ZIP password: {zip_password}")
    print(f"[*] ZIP filename: {zip_filename}")
    print()

    # Generate encrypted ZIP
    zip_data = create_encrypted_zip(flag, zip_password)
    print(f"[*] ZIP size: {len(zip_data)} bytes")

    # Build packet list
    packets = []

    # Phase 1: Noise DNS
    packets.extend(gen_noise_traffic(10))
    packets.extend(gen_noise_dns(8))

    # Phase 2: Suspicious DNS lookup
    packets.extend(gen_noise_traffic(5))
    packets.extend(gen_exfil_dns(hostname))

    # Phase 3: HTTP Basic Auth (password leak)
    packets.extend(gen_noise_dns(5))
    packets.extend(gen_http_basic_auth(zip_password))

    # Phase 4: More noise
    packets.extend(gen_noise_traffic(8))

    # Phase 5: SMB file transfer (the exfil)
    packets.extend(gen_smb_transfer(zip_data, zip_filename))

    # Phase 6: Trailing noise
    packets.extend(gen_noise_traffic(10))
    packets.extend(gen_noise_dns(5))

    # Write PCAP
    output_dir = os.environ.get("OUTPUT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(output_dir, "capture.pcap")
    wrpcap(output_path, packets)
    print(f"[+] PCAP written: {output_path} ({len(packets)} packets)")

    # Write metadata (for solve verification)
    meta_path = os.path.join(output_dir, "challenge_meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"hostname={hostname}\n")
        f.write(f"zip_password={zip_password}\n")
        f.write(f"zip_filename={zip_filename}\n")
        f.write(f"flag={flag}\n")
        f.write(f"exfil_target={EXFIL_TARGET_IP}\n")
        f.write(f"http_staging={HTTP_STAGING_IP}\n")
    print(f"[+] Metadata written: {meta_path}")


if __name__ == "__main__":
    main()


def gen_smb_transfer(zip_data: bytes, filename: str):
    """
    Generate SMB-like TCP traffic on port 445 carrying the ZIP file.
    Uses a simplified SMB2 structure that's parseable from the PCAP.
    """
    packets = []
    smb_port = 445
    client_port = random.randint(49152, 65535)

    seq_c = random.randint(100000, 999999)
    seq_s = random.randint(100000, 999999)

    # TCP handshake
    syn = (Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
           IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
           TCP(sport=client_port, dport=smb_port, flags="S", seq=seq_c))
    packets.append(syn)

    syn_ack = (Ether(src=EXFIL_TARGET_MAC, dst=BACKUP_SRV_MAC) /
               IP(src=EXFIL_TARGET_IP, dst=BACKUP_SRV_IP) /
               TCP(sport=smb_port, dport=client_port, flags="SA", seq=seq_s, ack=seq_c + 1))
    packets.append(syn_ack)

    seq_c += 1

    # SMB2 Tree Connect (reveals filename in share path)
    tree_path = f'\\\\{EXFIL_TARGET_IP}\\backup$\\{filename}'.encode()
    tree_pkt = (Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                TCP(sport=client_port, dport=smb_port, flags="PA",
                    seq=seq_c, ack=seq_s + 1) /
                Raw(load=tree_path))
    packets.append(tree_pkt)
    seq_c += len(tree_path)

    # File transfer: send ZIP wrapped in NetBIOS Session header (real SMB pattern)
    nb_header = b'\x00' + struct.pack('>I', len(zip_data))[1:]  # type=0x00, 3-byte length
    file_payload = nb_header + zip_data
    data_pkt = (Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
                IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
                TCP(sport=client_port, dport=smb_port, flags="PA",
                    seq=seq_c, ack=seq_s + 1) /
                Raw(load=file_payload))
    packets.append(data_pkt)
    seq_c += len(file_payload)

    # Server ACK
    ack_pkt = (Ether(src=EXFIL_TARGET_MAC, dst=BACKUP_SRV_MAC) /
               IP(src=EXFIL_TARGET_IP, dst=BACKUP_SRV_IP) /
               TCP(sport=smb_port, dport=client_port, flags="A",
                   seq=seq_s + 1, ack=seq_c))
    packets.append(ack_pkt)

    # FIN
    fin = (Ether(src=BACKUP_SRV_MAC, dst=EXFIL_TARGET_MAC) /
           IP(src=BACKUP_SRV_IP, dst=EXFIL_TARGET_IP) /
           TCP(sport=client_port, dport=smb_port, flags="FA",
               seq=seq_c, ack=seq_s + 1))
    packets.append(fin)

    return packets


def gen_noise_traffic(count=20):
    """Random benign TCP traffic for realism."""
    packets = []
    noise_ips = ["10.10.5.10", "10.10.5.20", "10.10.5.50", "10.10.5.100"]

    for _ in range(count):
        src_ip = random.choice(noise_ips)
        dst_ip = random.choice(noise_ips)
        if src_ip == dst_ip:
            continue
        pkt = (Ether(src=RandMAC(), dst=RandMAC()) /
               IP(src=src_ip, dst=dst_ip) /
               TCP(sport=random.randint(1024, 65535),
                   dport=random.choice([80, 443, 22, 3306, 5432]),
                   flags="A"))
        packets.append(pkt)
    return packets


def generate_pcap(output_path: str, seed: str = None):
    """Main generator — produces the challenge PCAP."""
    if seed:
        random.seed(seed)

    flag = get_flag()
    hostname = rand_hostname()
    zip_password = rand_password()
    zip_filename = rand_filename()

    print(f"[*] Flag: {flag}")
    print(f"[*] Exfil hostname: {hostname}")
    print(f"[*] ZIP password: {zip_password}")
    print(f"[*] ZIP filename: {zip_filename}")

    # Create the encrypted ZIP with the flag inside
    zip_data = create_encrypted_zip(flag, zip_password)
    print(f"[*] ZIP size: {len(zip_data)} bytes")

    # Build packet sequence
    all_packets = []

    # Phase 1: Noise DNS
    all_packets.extend(gen_noise_dns(10))

    # Phase 2: Suspicious DNS lookup
    all_packets.extend(gen_exfil_dns(hostname))

    # Phase 3: More noise
    all_packets.extend(gen_noise_traffic(8))

    # Phase 4: HTTP Basic Auth (leaks ZIP password)
    all_packets.extend(gen_http_basic_auth(zip_password))

    # Phase 5: Noise
    all_packets.extend(gen_noise_traffic(5))
    all_packets.extend(gen_noise_dns(5))

    # Phase 6: SMB file transfer (the ZIP)
    all_packets.extend(gen_smb_transfer(zip_data, zip_filename))

    # Phase 7: Trailing noise
    all_packets.extend(gen_noise_traffic(10))
    all_packets.extend(gen_noise_dns(5))

    # Write PCAP
    wrpcap(output_path, all_packets)
    print(f"[+] PCAP written to: {output_path}")
    print(f"[+] Total packets: {len(all_packets)}")

    # Write metadata (for challenge verification only)
    meta_path = output_path.replace(".pcap", "_meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"flag={flag}\n")
        f.write(f"hostname={hostname}\n")
        f.write(f"zip_password={zip_password}\n")
        f.write(f"zip_filename={zip_filename}\n")
        f.write(f"exfil_target_ip={EXFIL_TARGET_IP}\n")
        f.write(f"http_staging_ip={HTTP_STAGING_IP}\n")
    print(f"[+] Metadata written to: {meta_path}")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else "capture.pcap"
    generate_pcap(output, seed)
