#!/usr/bin/env python3

import os
import secrets
from hashlib import sha256
from socketserver import TCPServer, StreamRequestHandler

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

FLAG = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG") or "warCTF{fake_flag}"
FLAG = FLAG.encode()

A = 6364136223846793005
C = 1442695040888963407
M = 2**64

state = secrets.randbits(64)


def next_rand():
    global state
    state = (A * state + C) % M
    return state


class ChallengeHandler(StreamRequestHandler):
    def handle(self):
        global state

        
        outputs = [next_rand() for _ in range(5)]

       
        key_state = next_rand()
        key = sha256(str(key_state).encode()).digest()

        cipher = AES.new(key, AES.MODE_ECB)
        ct = cipher.encrypt(pad(FLAG, 16))

        self.wfile.write(b"[CLASSIFIED - SIGNAL INTERCEPT UNIT 8]\n")
        self.wfile.write(
            b"We intercepted several outputs from the enemy RNG.\n\n"
        )

        for i, value in enumerate(outputs):
            self.wfile.write(f"r{i} = {value}\n".encode())

        self.wfile.write(f"\nciphertext = {ct.hex()}\n".encode())


if __name__ == "__main__":
    TCPServer(("0.0.0.0", 1338), ChallengeHandler).serve_forever()
