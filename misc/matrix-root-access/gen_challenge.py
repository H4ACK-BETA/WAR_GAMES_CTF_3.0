#!/usr/bin/env python3
"""
gen_challenge.py

Generates a per-team variant of matrix://root_access:
  - picks a random access phrase from a wordlist
  - picks a random XOR key (1-255)
  - patches chall.c with the encrypted phrase bytes
  - writes a solve-helper metadata file (NOT shipped to players)

This script runs once at image build time (see Dockerfile), so every
team's container gets a different phrase/key baked into the binary,
but the flag itself is injected later at container start from the
GZCTF_FLAG environment variable (see start.sh) -- never embedded here.
"""

import random
import re
import sys
from pathlib import Path

WORDLIST = [
    "THERE_IS_NO_SPOON",
    "FOLLOW_THE_WHITE_RABBIT",
    "I_KNOW_KUNG_FU",
    "WELCOME_TO_THE_REAL_WORLD",
    "FREE_YOUR_MIND",
    "THE_ONE_HAS_AWOKEN",
    "RED_PILL_BLUE_PILL",
    "ZION_NEVER_FALLS",
]

SRC_PATH = Path(__file__).parent / "chall.c"
PLACEHOLDER = "    /* __SECRET_BYTES__ placeholder, replaced at generation time */\n    0x00\n"


def encrypt(secret: str, key: int) -> bytes:
    return bytes((ord(c) ^ key) for c in secret)


def format_c_byte_array(data: bytes) -> str:
    lines = []
    for i in range(0, len(data), 12):
        chunk = data[i:i + 12]
        lines.append("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) > 1:
        random.seed(sys.argv[1])  # allow deterministic builds for local testing

    secret = random.choice(WORDLIST)
    xor_key = random.randint(1, 255)
    encrypted = encrypt(secret, xor_key)

    src = SRC_PATH.read_text()

    if PLACEHOLDER not in src:
        print("[!] Placeholder not found in chall.c -- has it already been patched?", file=sys.stderr)
        sys.exit(1)

    patched = src.replace(PLACEHOLDER, format_c_byte_array(encrypted))
    patched = patched.replace("#define XOR_KEY 0x37", f"#define XOR_KEY 0x{xor_key:02X}")

    out_path = Path("/tmp/build/chall.c") if Path("/tmp/build").exists() else Path("chall_patched.c")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(patched)

    # Metadata for the challenge author / solve verification ONLY.
    # This file must never be shipped inside the player-facing image.
    meta_path = out_path.parent / "build_meta.txt"
    meta_path.write_text(
        f"secret_phrase={secret}\n"
        f"xor_key=0x{xor_key:02X}\n"
        f"encrypted_bytes={encrypted.hex()}\n"
    )

    print(f"[+] Patched source written to: {out_path}")
    print(f"[+] Build metadata written to: {meta_path}")
    print(f"[i] secret={secret!r} key=0x{xor_key:02X}  (for author eyes only)")


if __name__ == "__main__":
    main()
