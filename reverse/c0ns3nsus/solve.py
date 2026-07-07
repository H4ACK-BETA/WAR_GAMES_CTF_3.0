#!/usr/bin/env python3
"""
c0ns3nsus::m4ch1n3 - Solve Script

After reversing:
1. Arithmetic Engine: always returns PASS (opaque predicates)
2. Control-Flow Engine: always returns PASS (impossible branches)
3. State Machine: checks key[i] == DFA_ACCEPT_INPUT[i] via XOR transform
   - transform = (state * 7) ^ (i * 3) cancels out on both sides
   - so it just checks key[i] == DFA_ACCEPT_INPUT[i]
   - the accept path is the literal bytes of "warCTF{k3y_is_1t"
"""
import subprocess

# The DFA accept path found in .rodata after reversing state_machine_engine()
DFA_ACCEPT_INPUT = bytes([
    0x77, 0x61, 0x72, 0x43, 0x54, 0x46, 0x7B, 0x6B,
    0x33, 0x79, 0x5F, 0x69, 0x73, 0x5F, 0x31, 0x74
])
# = "warCTF{k3y_is_1t"

print(f"[*] DFA accept path: {DFA_ACCEPT_INPUT.hex()}")
print(f"[*] Decoded: {DFA_ACCEPT_INPUT.decode(errors='replace')}")
print()

key_hex = DFA_ACCEPT_INPUT.hex()
print(f"[*] Submitting key: {key_hex}")

# Test locally
result = subprocess.run(
    ["./chall-dist/consensus"],
    input=(key_hex + "\n").encode(),
    capture_output=True,
    timeout=5,
    cwd="reverse/c0ns3nsus"
)
output = result.stdout.decode()
print(output)

import re
match = re.search(r'warCTF\{[^}]+\}|WarCTF\{[^}]+\}', output, re.IGNORECASE)
if match:
    print(f"[+] FLAG: {match.group(0)}")
elif "CONSENSUS REACHED" in output:
    print("[+] Consensus reached! The flag will appear in the container where /flag exists.")
    print(f"    Full output:\n{output}")
else:
    print("[-] Failed")
