#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2024/25
#
# Key obfuscation prover script by 0xd13a

import binascii

print("Encoding the key")

key_val = "¡Patria o Muerte!"
print(key_val)

key = bytearray(key_val.encode("utf-8"))

for i in range(len(key)):
    key[i] = ((key[i] >> i%8)|(key[i] << (8 - i%8))) & 0xFF
print(binascii.hexlify(bytearray(key)))

for i in range(len(key)):
    key[i] ^= 0xAA+i*2
print(binascii.hexlify(bytearray(key)))

for i in range(len(key)):
    key[i] = ((key[i] << i%8)|(key[i] >> (8 - i%8))) & 0xFF
print(binascii.hexlify(bytearray(key)))

for i in range(len(key)):
    key[i] = (key[i]+i*2) & 0xFF

# Key is now encoded
print(binascii.hexlify(bytearray(key)))

print("\nDecoding the key")
for i in range(len(key)):
    key[i] = (key[i]-i*2) & 0xFF
print(binascii.hexlify(bytearray(key)))

for i in range(len(key)):
    key[i] = ((key[i] >> i%8)|(key[i] << (8 - i%8))) & 0xFF
print(binascii.hexlify(bytearray(key)))

for i in range(len(key)):
    key[i] ^= 0xAA+i*2
print(binascii.hexlify(bytearray(key)))

for i in range(len(key)):
    key[i] = ((key[i] << i%8)|(key[i] >> (8 - i%8))) & 0xFF

# Key is decoded
print(key.decode("utf-8"))