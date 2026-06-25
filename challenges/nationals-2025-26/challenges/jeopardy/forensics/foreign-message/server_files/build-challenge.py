#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2025/26
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Generation of files for Foreign message challenge

import gostcrypto  # to install run:  pip install gostcrypto
import uu
import os

# Switch to Russian letters
TO_RUS = [0,0,0,0,0]

# Switching between letters and numbers
TO_LETTERS = [1,1,1,1,1]
TO_FIGURES = [1,1,0,1,1]

# Text of the telegram with embedded encryption key
TEXT = "КЛЮЧ ШИФРОВАНИЯ: СТО ШЕСТНАДЦАТЬ, ТРИДЦАТЬ ДВА, СТО ШЕСТЬДЕСЯТ ДВА, ВОСЕМЬДЕСЯТ ЧЕТЫРЕ, СТО СЕМЬДЕСЯТ ДЕВЯТЬ, ДВЕСТИ СОРОК ДВА, СТО СОРОК ОДИН, ШЕСТЬДЕСЯТ ОДИН, СТО ВОСЕМНАДЦАТЬ, СТО ТРИДЦАТЬ ШЕСТЬ, ДВАДЦАТЬ ЧЕТЫРЕ, ВОСЕМЬДЕСЯТ ДВА, ДЕВЯТНАДЦАТЬ, ПЯТЬДЕСЯТ ОДИН, ДЕВЯНОСТО ШЕСТЬ, СТО ДЕВЯНОСТО ВОСЕМЬ, ДВАДЦАТЬ ЧЕТЫРЕ, СТО ПЯТЬДЕСЯТ ОДИН, ДВЕСТИ СОРОК ДВА, ДВАДЦАТЬ, СЕМЬДЕСЯТ ДВА, СТО ДЕВЯНОСТО ДВА, ДВЕСТИ ОДИННАДЦАТЬ, СТО ДЕВЯНОСТО ВОСЕМЬ, ТРИ, СТО СЕМЬДЕСЯТ ОДИН, ДВЕСТИ СЕМЬ, ДЕВЯНОСТО ЧЕТЫРЕ, ДВЕСТИ ОДИН, СТО ДЕВЯНОСТО ТРИ, СТО СОРОК ШЕСТЬ, ТРИДЦАТЬ ШЕСТЬ"

# Other fileds of the telegram
HEADER = "РОССИЯ МОСКВА МИНИСТЕРСТВО ИНОСТРАННЫХ ДЕЛ 14/06 1300"
ADDRESS = "КАНАДА ОТТАВА МИНИСТЕРСТВО МЕЖДУНАРОДНЫХ ДЕЛ"
SIGNATURE = "ДИРЕКТОР ДЕПАРТАМЕНТА СВЯЗИ ИВАНОВ"

# Standard telegram format
FULL_MESSAGE = f"\r\n\n\n{HEADER}=\r\n\n{ADDRESS}=\r\n\n{TEXT}={SIGNATURE}-\r\n\n\n\n\n\n"

# Beginning and end of the telegram
BEGIN = [TO_RUS] * 3
END = [TO_FIGURES] * 6

# MTK-2 telegraph encoding standard
chars = {
    ' ': (None, [0,0,1,0,0]),
    '\r': (None, [0,0,0,1,0]),
    '\n': (None, [0,1,0,0,0]),

    'Я': (True, [1,1,1,0,1]),
    'В': (True, [1,1,0,0,1]),
    'Е': (True, [1,0,0,0,0]),
    'Р': (True, [0,1,0,1,0]),
    'Т': (True, [0,0,0,0,1]),
    'Ы': (True, [1,0,1,0,1]),
    'У': (True, [1,1,1,0,0]),
    'И': (True, [0,1,1,0,0]),
    'О': (True, [0,0,0,1,1]),
    'П': (True, [0,1,1,0,1]),
    'А': (True, [1,1,0,0,0]),
    'С': (True, [1,0,1,0,0]),
    'Д': (True, [1,0,0,1,0]),
    'Ф': (True, [1,0,1,1,0]),
    'Г': (True, [0,1,0,1,1]),
    'Х': (True, [0,0,1,0,1]),
    'Й': (True, [1,1,0,1,0]),
    'К': (True, [1,1,1,1,0]),
    'Л': (True, [0,1,0,0,1]),
    'З': (True, [1,0,0,0,1]),
    'Ь': (True, [1,0,1,1,1]),
    'Ц': (True, [0,1,1,1,0]),
    'Ж': (True, [0,1,1,1,1]),
    'Б': (True, [1,0,0,1,1]),
    'Н': (True, [0,0,1,1,0]),
    'М': (True, [0,0,1,1,1]),

    '1': (False, [1,1,1,0,1]),
    '2': (False, [1,1,0,0,1]),
    '3': (False, [1,0,0,0,0]),
    'Ч': (False, [0,1,0,1,0]),
    '5': (False, [0,0,0,0,1]),
    '6': (False, [1,0,1,0,1]),
    '7': (False, [1,1,1,0,0]),
    '8': (False, [0,1,1,0,0]),
    '9': (False, [0,0,0,1,1]),
    '0': (False, [0,1,1,0,1]),
    '-': (False, [1,1,0,0,0]),
    "'": (False, [1,0,1,0,0]),
    'Э': (False, [1,0,1,1,0]),
    'Ш': (False, [0,1,0,1,1]),
    'Щ': (False, [0,0,1,0,1]),
    'Ю': (False, [1,1,0,1,0]),
    '(': (False, [1,1,1,1,0]),
    ')': (False, [0,1,0,0,1]),
    '+': (False, [1,0,0,0,1]),
    '/': (False, [1,0,1,1,1]),
    ':': (False, [0,1,1,1,0]),
    '=': (False, [0,1,1,1,1]),
    '?': (False, [1,0,0,1,1]),
    ',': (False, [0,0,1,1,0]),
    '.': (False, [0,0,1,1,1]),
}

# Build a sequence of punched holes for the message
def build_sequence(message):
    seq = BEGIN

    letter_mode = True

    # Process the characters and generate punch sequence
    for i in range(len(message)):
        c = message[i]
        if c in chars:
            val = chars[c]
            if c != " ":
                # Neutral character 
                if val[0] is None:
                    pass
                # Letter 
                elif (val[0] == True) and not letter_mode:
                    seq.append(TO_LETTERS)
                    letter_mode = True
                # Number
                elif (val[0] == False) and letter_mode:
                    seq.append(TO_FIGURES)
                    letter_mode = False

            seq.append(val[1])

    seq += END

    return seq

# Punch the holes for one row
def punch_row(symbol):
    result = "o" if symbol[0] == 1 else " "
    result += "o" if symbol[1] == 1 else " "
    result += "."
    result += "o" if symbol[2] == 1 else " "
    result += "o" if symbol[3] == 1 else " "
    result += "o" if symbol[4] == 1 else " "
    result += "\n"
    return result

print("Generating telegram...")

seq = build_sequence(FULL_MESSAGE)

# Generate the telegram message
with open("../release_files/telegram.txt", "w") as f:
    for s in seq:
        f.write(punch_row(s))

print("Preparing encrypted document...")

# Encrypt the document
ENCRYPTION_KEY = bytearray([
    116,  32, 162, 84, 179, 242, 141,  61, 118, 136,  24, 82,  19,  51,  96, 198, 
     24, 151, 242, 20,  72, 192, 211, 198,   3, 171, 207, 94, 201, 193, 146,  36
])


with open("./message.rtf", "rb") as inf:
    plain_text = bytearray(inf.read())


cipher_obj = gostcrypto.gostcipher.new('kuznechik',
                                        ENCRYPTION_KEY,
                                        gostcrypto.gostcipher.MODE_ECB,
                                        pad_mode=gostcrypto.gostcipher.PAD_MODE_1)

cipher_text = cipher_obj.encrypt(plain_text)

ENCRYPTED_FILE = "./message.enc"
UUENCODED_FILE = "./message.uue"

with open(ENCRYPTED_FILE, "wb") as outf:
    outf.write(cipher_text)

# Uuencode the file
uu.encode(ENCRYPTED_FILE, UUENCODED_FILE)

# Compose the email
HEADER = """From: Департамент связи <comm@mid.ru>
To: Office of Communications <communications@international.gc.ca>
Date: Sun, 14 Jun 2026 14:00:34 +0300
Subject: Установление связи

"""

with open("../release_files/message.txt", "w") as outf:
    outf.write(HEADER)

    with open(UUENCODED_FILE, "r") as inf:
        contents = inf.read()

    outf.write(contents)

os.remove(ENCRYPTED_FILE)
os.remove(UUENCODED_FILE)
