#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2025/26
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Solve script for Foreign message challenge

import gostcrypto  # to install run:  pip install gostcrypto
import uu
import os

# Switching between letters and numbers
TO_LETTERS = [1,1,1,1,1]
TO_FIGURES = [1,1,0,1,1]

# Text of the telegram with embedded encryption key
TEXT = "КЛЮЧ ШИФРОВАНИЯ: СТО ШЕСТНАДЦАТЬ, ТРИДЦАТЬ ДВА, СТО ШЕСТЬДЕСЯТ ДВА, ВОСЕМЬДЕСЯТ ЧЕТЫРЕ, СТО СЕМЬДЕСЯТ ДЕВЯТЬ, ДВЕСТИ СОРОК ДВА, СТО СОРОК ОДИН, ШЕСТЬДЕСЯТ ОДИН, СТО ВОСЕМНАДЦАТЬ, СТО ТРИДЦАТЬ ШЕСТЬ, ДВАДЦАТЬ ЧЕТЫРЕ, ВОСЕМЬДЕСЯТ ДВА, ДЕВЯТНАДЦАТЬ, ПЯТЬДЕСЯТ ОДИН, ДЕВЯНОСТО ШЕСТЬ, СТО ДЕВЯНОСТО ВОСЕМЬ, ДВАДЦАТЬ ЧЕТЫРЕ, СТО ПЯТЬДЕСЯТ ОДИН, ДВЕСТИ СОРОК ДВА, ДВАДЦАТЬ, СЕМЬДЕСЯТ ДВА, СТО ДЕВЯНОСТО ДВА, ДВЕСТИ ОДИННАДЦАТЬ, СТО ДЕВЯНОСТО ВОСЕМЬ, ТРИ, СТО СЕМЬДЕСЯТ ОДИН, ДВЕСТИ СЕМЬ, ДЕВЯНОСТО ЧЕТЫРЕ, ДВЕСТИ ОДИН, СТО ДЕВЯНОСТО ТРИ, СТО СОРОК ШЕСТЬ, ТРИДЦАТЬ ШЕСТЬ"

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

# Decode one line of the encoded telegram
def decode(line):
    result = []
    result.append(1 if line[0] == "o" else 0)
    result.append(1 if line[1] == "o" else 0)
    result.append(1 if line[3] == "o" else 0)
    result.append(1 if line[4] == "o" else 0)
    result.append(1 if line[5] == "o" else 0)
    return result

print("Decoding telegram... ", end="")

letter_mode = True
telegram = ""

# Decoding the telegram message
with open("../release_files/telegram.txt", "r") as f:
    for l in f.readlines():
        code = decode(l)

        if code == TO_FIGURES and letter_mode == True:
            letter_mode = False
        elif code == TO_LETTERS and letter_mode == False:
            letter_mode = True
        else:
            for key in chars.keys():
                val = chars[key]
                if val[1] == code and \
                   (val[0] is None or val[0] == letter_mode):
                    telegram += key
                    break

print("success" if TEXT in telegram else "failure")


print("Decrypting document... ", end="")


# Uudecode the file

MESSAGE_FILE = "../release_files/message.txt"
ENCRYPTED_FILE = "./message.enc"

uu.decode(MESSAGE_FILE, ENCRYPTED_FILE)

# Decrypt the document

with open(ENCRYPTED_FILE, "rb") as inf:
    cipher_text = bytearray(inf.read())

ENCRYPTION_KEY = bytearray([
    116,  32, 162, 84, 179, 242, 141,  61, 118, 136,  24, 82,  19,  51,  96, 198, 
     24, 151, 242, 20,  72, 192, 211, 198,   3, 171, 207, 94, 201, 193, 146,  36
])

cipher_obj = gostcrypto.gostcipher.new('kuznechik',
                                        ENCRYPTION_KEY,
                                        gostcrypto.gostcipher.MODE_ECB,
                                        pad_mode=gostcrypto.gostcipher.PAD_MODE_1)

plain_text = cipher_obj.decrypt(cipher_text)

FLAG = b"CyberSci\\{I ain't afraid of no GOST!\\}"

print("success" if FLAG in plain_text else "failure")

os.remove(ENCRYPTED_FILE)
