#!/usr/bin/env python3

from pwn import *
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import re

A = 6364136223846793005
C = 1442695040888963407
M = 2**64

io = remote("localhost", 32774)

data = io.recvall().decode()
print(data)

outputs = [
    int(x)
    for x in re.findall(r"r\d+\s*=\s*(\d+)", data)
]

ciphertext = bytes.fromhex(
    re.search(r"ciphertext\s*=\s*([0-9a-f]+)", data).group(1)
)

state = outputs[-1]
key_state = (A * state + C) % M

key = sha256(str(key_state).encode()).digest()

cipher = AES.new(key, AES.MODE_ECB)
flag = unpad(cipher.decrypt(ciphertext), 16)

print("FLAG:", flag.decode())
