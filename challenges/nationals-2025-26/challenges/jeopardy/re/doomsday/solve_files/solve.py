#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Nationals 2026
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# DOOMsday challenge solve script

encrypted_bytes = [0xf8, 0xbb, 0xd8, 0x38, 0xda, 0xfa, 0xf8, 
                   0xb9, 0x95, 0xfa, 0x19, 0x98, 0xbb, 0x94, 
                   0x1a, 0x99, 0xf6, 0x94, 0x39, 0x79, 0x59, 
                   0xfa, 0x1a, 0xf6, 0xda, 0x94, 0x7a, 0xb9, 
                   0x76, 0x99, 0xb9, 0x59, 0x94, 0xbb, 0x79, 
                   0x3a, 0xb5]

def rotate_right(byte: int, amount: int) -> int:
    return ((byte >> amount) | (byte << (8 - amount))) & 0xFF

def twister_decrypt(ciphertext: bytes, rounds: int, key: int) -> str:
    data = bytearray(ciphertext)

    for round_num in range(rounds - 1, -1, -1):
        round_key = key ^ ((round_num * 31) & 0xFF)

        for i in range(len(data)):
            data[i] = rotate_right(data[i], (round_num % 7) + 1)
            data[i] ^= round_key

        data.reverse()

    return data.decode("utf-8")


decrypted = twister_decrypt(encrypted_bytes, 1000, 0xDB)

print("Solving flag #1") 
print(decrypted)

assert(decrypted == "CYBERSCI(SL@Y TH3 MONST3R WI7HIN YOU)") 

###################################

map_names = [
    "MAP01: Hydroelectric Plant",
    "MAP02: Filtration Tunnels",
    "MAP03: Crude Processing Center",
    "MAP04: Containment Bay",
    "MAP05: Sludge Burrow",
    "MAP06: Gamma Labs",
    "MAP07: Outer Storage Warehouse",
    "MAP08: Astronomy Complex",
    "MAP09: Datacenter",
    "MAP10: Deadly Outlands",
    "MAP11: Infinite Plain",
    "MAP12: Railroads",
    "MAP13: Station Earth",
    "MAP14: Nuclear Zone",
    "MAP15: Hostile Takeover",
    "MAP16: Urban Jungle",
    "MAP17: City Capitol",
    "MAP18: Aquatics Lab",
    "MAP19: Sewage Control",
    "MAP20: Blood Ember Fortress",
    "MAP21: Under Realm",
    "MAP22: Remanasu",
    "MAP23: Underground Facility",
    "MAP24: Tertiary Loading Bay",
    "MAP25: Red Works",
    "MAP26: Dark Depths",
    "MAP27: Warped Elementality",
    "MAP28: Grim Redoubt",
    "MAP29: Last Stand",
    "MAP30: Jaws of Defeat",
    "MAP31: Be Quiet",
    "MAP32: Not Sure",
]

# flag pieces are encoded based on names of levels maps
encoded_flag = [0x3c, 0x4f, 0x34, 0x2e, 0x40, 0x5f, 0x4b, 0x25, 0x41, 0x22, 0x56, 0x38, 0x3f, 0x56, 0x5b, 0x58,
                0x2b, 0x5c, 0x2b, 0x26, 0x3a, 0x3f, 0x4a, 0x3b, 0x40, 0x35, 0x41, 0x56, 0x42, 0x06, 0x2c, 0x47]

flag = ""

for i in range(len(map_names)):
    name = map_names[i]
    key = ord(name[0])
    for char in name[1:]:
        key ^= ord(char)
    
    flag += chr(key ^ encoded_flag[i])

print("\nSolving flag #3")
print(f"CYBERSCI({flag})")
assert(flag == "WH4T DOE5NT KILL U M@KES U TIR3D")
