#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Nationals 2026
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Dropped stack challenge generation script

from PIL import Image, ImageDraw
import base64
import random
import string
import os
import datetime
import tarfile

# Vertical coordinates of punched card rows
lines = [170, 217, 263, 308, 355, 401, 445, 493, 540, 125, 80, 35]

# A mapping between a character and a set of rows in which to punch a hole 
# Full supported charset:  0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#,$.-@%*<-/+_)|&>:;'?"=!(,.
# Space is represented by no hole punched
chars = {
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

def punch(draw, col, row):
    """ Punch the hole for one character in a specific row and column """
    x = 39 + (col - 1) * 15.9
    y = lines[row - 1]
    rectangle_coords = (x, y, x + 10, y + 25)
    draw.rectangle(rectangle_coords, fill="white")

def generate_card(text, name):
    """ Punch text in a single punched card """

    input_path = "blank-card.jpg"

    # Open the punched card template
    image = Image.open(input_path)

    draw = ImageDraw.Draw(image)

    # Punch characters one by one
    for i in range(len(text)):
        c = text[i]
        if c in chars:
            cols = chars[c]
            for col in cols:
                punch(draw, i+1, col)

    # Output the modified image
    image.save(name)

    # Set all timestmps to be the same to complicate sorting of cards
    timestamp = datetime.datetime(2025, 9, 15, 3, 13, 37).timestamp()
    os.utime(name, (timestamp, timestamp))

# We will encode text on the card in 76 columns, then add a space column, and then a 3-digit card number
CHUNK_SIZE = 76

# Load flag file o encode
encoded = base64.b32encode(open("flag.pcx", "rb").read()).decode()

# Split text into segments
segments = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]

# Generate random file names
names = []
for i in range(len(segments)):
    while True:
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        if rand_str not in names:
            names.append(rand_str)
            break

# Build a list of text segments and card file names
cards = []
for i in range(len(segments)):
    cards.append((segments[i].ljust(CHUNK_SIZE) + " " + str(i).zfill(3), names[i] + ".png"))
random.shuffle(cards)

ARCHIVE = "../release_files/dropped-stack.tar.gz"

print("Generating tarball with punched cards...")

# Remove file if already exists
try:
    os.remove(ARCHIVE)
except FileNotFoundError:
    pass    

with tarfile.open(ARCHIVE, "w:gz") as tar:
    for card in cards:
        # Punch card
        generate_card(card[0], card[1])
        # Add it to tarball
        tar.add(card[1], arcname=card[1])
        # Delete file
        os.remove(card[1])