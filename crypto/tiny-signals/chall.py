#!/usr/bin/env python3

import os
from socketserver import TCPServer, StreamRequestHandler
from Crypto.Util.number import getPrime, bytes_to_long

FLAG = os.environ.get("GZCTF_FLAG") or os.environ.get("FLAG") or "warCTF{fake_flag}"
FLAG = FLAG.encode()


def generate_keys():
    p = getPrime(16)
    q = getPrime(2032)

    n = p * q
    e = 65537

    return n, e


def encrypt(m, n, e):
    return pow(m, e, n)


class ChallengeHandler(StreamRequestHandler):
    def handle(self):
        n, e = generate_keys()

        m = bytes_to_long(FLAG)
        c = encrypt(m, n, e)

        self.wfile.write(b"[CLASSIFIED - SIGNAL INTERCEPT UNIT 7]\n")
        self.wfile.write(f"n = {n}\n".encode())
        self.wfile.write(f"e = {e}\n".encode())
        self.wfile.write(f"c = {c}\n".encode())


if __name__ == "__main__":
    TCPServer(("0.0.0.0", 1337), ChallengeHandler).serve_forever()
