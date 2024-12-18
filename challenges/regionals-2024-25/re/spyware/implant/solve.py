#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2024/25
#
# Shutdown key solver script by 0xd13a

import hashlib

def brute_sha256(hash):
	i = 0
	while i <= 0xffffff:
		val = i.to_bytes(3, 'big')
		if hashlib.sha256(val).digest() == hash:
			return val
		i += 1
	return 0

print("Solving Shutdown Key")

val1 = brute_sha256(b"\x37\x24\xb6\x5b\x2a\xf4\x46\x06\x37\xd4\xe5\x52\x21\x62\x19\xef\x33\xa8\xda\x5c\x16\x56\x68\x19\x68\xe4\x54\x6d\xa5\x44\xac\x46")
val2 = brute_sha256(b"\xc7\x8e\x86\xef\xff\x8e\xc6\x56\x00\x43\xb8\xc4\x5b\x6c\xdc\x10\xe4\xf1\x7b\xd9\xbc\xf9\x03\x5d\x31\x2a\xc4\xc5\x09\xca\x69\xd0")
val3 = brute_sha256(b"\x3e\x94\x36\x51\xc8\x26\x20\x0e\xb9\xf6\x74\x4c\x0c\x63\x08\x86\xe1\x5e\xf5\xa2\xb7\x9e\x78\x4b\xa5\x60\x7d\x96\xb9\xb7\x4c\xfd")
val4 = brute_sha256(b"\xf3\x2b\x70\x2f\xba\x23\x08\x3f\x02\xc8\x30\xee\x18\x5c\x03\xaf\x9e\x47\x0d\xde\x15\x44\xcd\x6f\x1b\xad\x09\xdd\x64\x1a\xbb\x56")
val5 = brute_sha256(b"\x31\x25\xfe\x5c\xf9\x8c\xa0\x78\x69\xa6\xe1\xd7\x5e\x6c\x6d\xb6\x3b\x79\xd7\xd0\xf4\xd0\xf3\x48\x9e\x4d\x2a\xcc\x7a\x04\x3d\x75")
val6 = brute_sha256(b"\x6e\x15\xc6\x07\xf0\xda\x38\x5c\xc7\x0c\x38\xe7\x8c\xd5\x21\x47\x59\x6f\xad\x6e\x42\x60\x76\x9a\x8c\x9d\x61\xd2\xd5\x3d\x7c\x6c")
val7 = brute_sha256(b"\x5c\x98\x33\xcb\xc7\xfd\x0a\xfd\x79\xe5\x9f\xb5\x13\xe0\xdf\x59\x45\xa9\x57\x7a\x68\xcd\x66\x59\x0c\xe2\x10\xad\x93\xc6\xc3\xc0")
val = val1 + val2 + val3 + val4 + val5 + val6 + val7
print(val)
assert(val == b"h45tA 1a V15tA, 8aBy!")
