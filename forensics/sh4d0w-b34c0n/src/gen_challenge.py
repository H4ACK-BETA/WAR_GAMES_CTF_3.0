#!/usr/bin/env python3
"""
sh4d0w::b34c0n — PCAP Generator

Simulates a C2 beacon communicating over HTTP:
- Beacon checks in every ~60s via HTTP GET (with jitter)
- C2 server responds with base64-encoded commands
- Beacon exfiltrates data via HTTP POST with base64 in body
- Flag is split across multiple exfil POST requests

The traffic is mixed with normal-looking HTTP noise.
"""
import os
import sys
import random
import string
import base64
import time
import struct
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
    return "WarCTF{b34c0n_d3t3ct3d_c2_ch4nn3l_d3c0d3d}"


# Network layout
VICTIM_IP = "10.20.5.42"
VICTIM_MAC = "aa:bb:cc:11:22:33"
C2_IP = "185.199.47.103"
C2_MAC = "de:ad:c2:c2:c2:c2"
GATEWAY_MAC = "00:11:22:33:44:55"

# Legitimate sites for noise
LEGIT_SITES = ["10.20.5.1", "10.20.5.10", "93.184.216.34", "142.250.80.46"]
LEGIT_DOMAINS = ["updates.microsoft.com", "graph.microsoft.com",
                 "outlook.office365.com", "cdn.jquery.com", "fonts.googleapis.com"]

# C2 commands (what the server tells the beacon to do)
C2_COMMANDS = [
    "whoami",
    "systeminfo | findstr /B /C:OS",
    "dir C:\\Users\\finance\\Documents",
    "type C:\\Users\\finance\\Documents\\Q3_report.xlsx",
    "exfil_start",
]


def build_http_request(src_ip, src_mac, dst_ip, dst_mac, sport, dport, method, path, host, body=None, headers=None):
    """Build an HTTP request packet."""
    seq_c = random.randint(100000, 999999)
    seq_s = random.randint(100000, 999999)

    req_line = f"{method} {path} HTTP/1.1\r\n"
    hdrs = f"Host: {host}\r\n"
    hdrs += f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
    if headers:
        for k, v in headers.items():
            hdrs += f"{k}: {v}\r\n"
    if body:
        hdrs += f"Content-Length: {len(body)}\r\n"
        hdrs += f"Content-Type: application/x-www-form-urlencoded\r\n"
    hdrs += "Connection: keep-alive\r\n"
    hdrs += "\r\n"

    payload = (req_line + hdrs).encode()
    if body:
        payload += body.encode() if isinstance(body, str) else body

    pkt = (Ether(src=src_mac, dst=dst_mac) /
           IP(src=src_ip, dst=dst_ip) /
           TCP(sport=sport, dport=dport, flags="PA", seq=seq_c, ack=seq_s) /
           Raw(load=payload))
    return pkt


def build_http_response(src_ip, src_mac, dst_ip, dst_mac, sport, dport, status, body, content_type="text/html"):
    """Build an HTTP response packet."""
    seq_s = random.randint(100000, 999999)
    seq_c = random.randint(100000, 999999)

    resp = f"HTTP/1.1 {status}\r\n"
    resp += f"Content-Type: {content_type}\r\n"
    resp += f"Content-Length: {len(body)}\r\n"
    resp += f"Server: nginx/1.24.0\r\n"
    resp += f"Connection: keep-alive\r\n"
    resp += f"\r\n"
    resp += body

    pkt = (Ether(src=src_mac, dst=dst_mac) /
           IP(src=src_ip, dst=dst_ip) /
           TCP(sport=sport, dport=dport, flags="PA", seq=seq_s, ack=seq_c) /
           Raw(load=resp.encode()))
    return pkt


def gen_beacon_checkin(beacon_id, command_b64):
    """Generate a beacon check-in (GET) and C2 response with encoded command."""
    sport = random.randint(49152, 65535)

    # Beacon GET request (looks like normal analytics/tracking)
    path = f"/api/v2/status?sid={beacon_id}&t={random.randint(1000000, 9999999)}"
    req = build_http_request(
        VICTIM_IP, VICTIM_MAC, C2_IP, C2_MAC,
        sport, 443, "GET", path, "cdn-analytics.cloud",
        headers={"Accept": "application/json", "X-Session": beacon_id}
    )

    # C2 response with base64-encoded command in JSON
    resp_body = f'{{"status":"ok","data":"{command_b64}","interval":60}}'
    resp = build_http_response(
        C2_IP, C2_MAC, VICTIM_IP, VICTIM_MAC,
        443, sport, "200 OK", resp_body, "application/json"
    )

    return [req, resp]


def gen_exfil_post(beacon_id, chunk_b64, chunk_idx):
    """Generate a data exfiltration POST from victim to C2."""
    sport = random.randint(49152, 65535)

    path = f"/api/v2/telemetry"
    body = f"sid={beacon_id}&seq={chunk_idx}&d={chunk_b64}"
    req = build_http_request(
        VICTIM_IP, VICTIM_MAC, C2_IP, C2_MAC,
        sport, 443, "POST", path, "cdn-analytics.cloud",
        body=body,
        headers={"X-Request-ID": rand_str(12)}
    )

    resp = build_http_response(
        C2_IP, C2_MAC, VICTIM_IP, VICTIM_MAC,
        443, sport, "200 OK", '{"ack":true}', "application/json"
    )

    return [req, resp]


def gen_noise_http(count=3):
    """Generate legitimate-looking HTTP traffic."""
    packets = []
    for _ in range(count):
        src_ip = VICTIM_IP
        dst_ip = random.choice(LEGIT_SITES)
        sport = random.randint(49152, 65535)
        paths = ["/", "/favicon.ico", "/api/notifications", "/fonts/roboto.woff2",
                 "/v1/users/me", "/assets/logo.png", "/updates/check"]

        req = build_http_request(
            src_ip, VICTIM_MAC, dst_ip, GATEWAY_MAC,
            sport, 80, "GET", random.choice(paths),
            random.choice(LEGIT_DOMAINS)
        )
        packets.append(req)

        resp = build_http_response(
            dst_ip, GATEWAY_MAC, src_ip, VICTIM_MAC,
            80, sport, "200 OK", f"<html><body>{rand_str(50)}</body></html>"
        )
        packets.append(resp)
    return packets


def gen_noise_dns(count=4):
    """Generate DNS noise."""
    packets = []
    for _ in range(count):
        domain = random.choice(LEGIT_DOMAINS)
        pkt = (Ether(src=VICTIM_MAC, dst=GATEWAY_MAC) /
               IP(src=VICTIM_IP, dst="10.20.5.1") /
               UDP(sport=random.randint(49152, 65535), dport=53) /
               DNS(rd=1, qd=DNSQR(qname=domain, qtype="A")))
        packets.append(pkt)
    return packets


def generate_pcap(output_path: str, seed: str = None):
    """Main generator — produces C2 beacon PCAP."""
    if seed:
        random.seed(seed)

    flag = get_flag()
    beacon_id = rand_str(16, string.ascii_letters + string.digits)

    print(f"[*] Flag: {flag}")
    print(f"[*] Beacon ID: {beacon_id}")

    # Split flag into chunks for exfiltration
    flag_b64 = base64.b64encode(flag.encode()).decode()
    chunk_size = 12
    flag_chunks = [flag_b64[i:i+chunk_size] for i in range(0, len(flag_b64), chunk_size)]
    print(f"[*] Flag chunks: {len(flag_chunks)}")

    all_packets = []

    # Simulate 10 beacon intervals (~10 minutes of traffic)
    for interval in range(10):
        # Background noise before beacon
        all_packets.extend(gen_noise_dns(random.randint(2, 5)))
        all_packets.extend(gen_noise_http(random.randint(1, 3)))

        # Beacon check-in
        if interval < len(C2_COMMANDS):
            cmd = C2_COMMANDS[interval]
        else:
            cmd = "sleep"

        cmd_b64 = base64.b64encode(cmd.encode()).decode()
        all_packets.extend(gen_beacon_checkin(beacon_id, cmd_b64))

        # If command was exfil_start or after, send data chunks
        if interval >= 4 and (interval - 4) < len(flag_chunks):
            chunk_idx = interval - 4
            all_packets.extend(gen_noise_http(1))
            all_packets.extend(gen_exfil_post(beacon_id, flag_chunks[chunk_idx], chunk_idx))

        # More noise after beacon
        all_packets.extend(gen_noise_http(random.randint(1, 2)))
        all_packets.extend(gen_noise_dns(random.randint(1, 3)))

    wrpcap(output_path, all_packets)
    print(f"[+] PCAP written to: {output_path}")
    print(f"[+] Total packets: {len(all_packets)}")

    meta_path = output_path.replace(".pcap", "_meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"flag={flag}\n")
        f.write(f"flag_b64={flag_b64}\n")
        f.write(f"beacon_id={beacon_id}\n")
        f.write(f"c2_ip={C2_IP}\n")
        f.write(f"victim_ip={VICTIM_IP}\n")
        f.write(f"chunks={flag_chunks}\n")
        f.write(f"commands_b64={[base64.b64encode(c.encode()).decode() for c in C2_COMMANDS]}\n")
    print(f"[+] Metadata: {meta_path}")


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else "beacon_capture.pcap"
    generate_pcap(output, seed)
