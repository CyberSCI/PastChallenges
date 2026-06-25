#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Nationals 2026
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Dropped stack challenge solve script

from PIL import Image
import base64
import tarfile
import io

# Vertical coordinates of punched card rows
lines = [170, 217, 263, 308, 355, 401, 445, 493, 540, 125, 80, 35]

# A mapping between a character and a set of rows in which to punch a hole 
# Full supported charset:  0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#,$.-@%*<-/+_)|&>:;'?"=!(,.
# Space is represented by no hole punched
chars = {
    ' ': [],
    '&': [12],
    '-': [11],
    '0': [10],
    '1': [1],
    '2': [2],
    '3': [3],
    '4': [4],
    '5': [5],
    '6': [6],
    '7': [7],
    '8': [8],
    '9': [9],
    'A': [1, 12],
    'B': [2, 12],
    'C': [3, 12],
    'D': [4, 12],
    'E': [5, 12],
    'F': [6, 12],
    'G': [7, 12],
    'H': [8, 12],
    'I': [9, 12],
    'J': [1, 11],
    'K': [2, 11],
    'L': [3, 11],
    'M': [4, 11],
    'N': [5, 11],
    'O': [6, 11],
    'P': [7, 11],
    'Q': [8, 11],
    'R': [9, 11],
    'S': [2, 10],
    'T': [3, 10],
    'U': [4, 10],
    'V': [5, 10],
    'W': [6, 10],
    'X': [7, 10],
    'Y': [8, 10],
    'Z': [9, 10],
    '/': [1, 10],
    ':': [2, 8],
    '#': [3, 8],
    '@': [4, 8],
    '\'': [5, 8],
    '=': [6, 8],
    '"': [7, 8],
    ',': [3, 8, 10],
    '%': [4, 8, 10],
    '_': [5, 8, 10],
    '>': [6, 8, 10],
    '?': [7, 8, 10],
    '!': [2, 8, 11],
    '$': [3, 8, 11],
    '*': [4, 8, 11],
    ')': [5, 8, 11],
    ';': [6, 8, 11],
    '.': [3, 8, 12],
    '<': [4, 8, 12],
    '(': [5, 8, 12],
    '+': [6, 8, 12],
    '|': [7, 8, 12]
}

# Number of character columns on the card. Will be followed by a space and a 3-digit card number
CHUNK_SIZE = 76

def decode_card(data):
    """ Decode card into a string of text """
    image_stream = io.BytesIO(data)

    img = Image.open(image_stream)

    txt = ""
    for col in range(1,80+1):
        x = 39 + (col - 1) * 15.9 + 5
        holes = []
        for row in range(1,12+1):
            y = lines[row - 1] + 12
            # Check if the color is white (indicating punched hole)
            if img.getpixel((x,y)) == (255,255,255):
                holes.append(row)

        # Fing the character for which the set of rows matches, and add it to the output
        for c in chars.keys():
            if holes == chars[c]:
                txt += c
                break

    return txt

print("Reading punched cards...")

# A map of card numbers to text chunks 
parts = {}
with tarfile.open("../release_files/dropped-stack.tar.gz", "r:gz") as tar:
    # Go though all files in the tarball
    for member in tar.getmembers():
        if member.isfile():
            f = tar.extractfile(member)
            data = f.read()
            text = decode_card(data)
            # Split the card text into a body and a card number
            body = text[:CHUNK_SIZE].strip()
            num = int(text[CHUNK_SIZE+1:])
            parts[num] = body

# Collect all text chunks in order
encoded = ""
for i in range(len(parts)):
    encoded += parts[i]

FILE = "flag.pcx"

print(f"Generating flag file {FILE}")
# Base32-decode flag file contents
with open(FILE, "wb") as f:
    f.write(base64.b32decode(encoded))
