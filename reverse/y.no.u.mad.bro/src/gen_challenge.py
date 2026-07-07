#!/usr/bin/env python3
import random
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
    "WAKE_UP_NEO",
    "THE_MATRIX_HAS_YOU",
    "KNOCK_KNOCK_NEO",
    "SENTINELS_ARE_COMING",
]

XOR_ROUNDS = 3
SRC_PATH = Path(__file__).parent / "challenge.c"
PLACEHOLDER = "    /* __SECRET_BYTES__ placeholder, replaced at generation time */\n    0x00\n"


def encrypt(secret: str, base_key: int) -> bytes:
    result = []
    key = base_key & 0xFF
    for i, ch in enumerate(secret):
        decoded = ord(ch)
        for r in range(XOR_ROUNDS):
            decoded ^= ((key + r * 0x11) & 0xFF)
        result.append(decoded & 0xFF)
        key = ((key ^ i) + 0x07) & 0xFF
    return bytes(result)


def decrypt(encrypted: bytes, base_key: int) -> str:
    result = []
    key = base_key & 0xFF
    for i, enc_byte in enumerate(encrypted):
        val = enc_byte
        for r in range(XOR_ROUNDS):
            val ^= ((key + r * 0x11) & 0xFF)
        result.append(chr(val & 0xFF))
        key = ((key ^ i) + 0x07) & 0xFF
    return "".join(result)


def format_c_byte_array(data: bytes) -> str:
    lines = []
    for i in range(0, len(data), 12):
        chunk = data[i:i + 12]
        lines.append("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) > 1 and sys.argv[1]:
        random.seed(sys.argv[1])

    secret = random.choice(WORDLIST)
    xor_key = random.randint(0x20, 0xFE)
    encrypted = encrypt(secret, xor_key)

    assert decrypt(encrypted, xor_key) == secret, "Encryption roundtrip failed!"

    src = SRC_PATH.read_text()

    if PLACEHOLDER not in src:
        print("[!] Placeholder not found in challenge.c", file=sys.stderr)
        print("[!] Looking for:", repr(PLACEHOLDER), file=sys.stderr)
        sys.exit(1)

    patched = src.replace(PLACEHOLDER, format_c_byte_array(encrypted))
    patched = patched.replace("#define XOR_KEY 0x37", f"#define XOR_KEY 0x{xor_key:02X}")

    out_path = Path("/tmp/build/challenge.c") if Path("/tmp/build").exists() else Path("challenge_patched.c")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(patched)

    meta_path = out_path.parent / "build_meta.txt"
    meta_path.write_text(
        f"secret_phrase={secret}\n"
        f"xor_key=0x{xor_key:02X}\n"
        f"xor_rounds={XOR_ROUNDS}\n"
        f"encrypted_bytes={encrypted.hex()}\n"
        f"encrypted_len={len(encrypted)}\n"
    )

    print(f"[+] Patched source written to: {out_path}")
    print(f"[+] Build metadata written to: {meta_path}")
    print(f"[i] secret={secret!r} key=0x{xor_key:02X} rounds={XOR_ROUNDS}")
    print(f"[i] Verify decrypt: {decrypt(encrypted, xor_key)!r}")


if __name__ == "__main__":
    main()
