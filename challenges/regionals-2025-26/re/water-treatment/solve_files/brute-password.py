#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2025/26
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Water treatment challenge bruteforcing script

from Crypto.Hash import MD2
import codecs

with codecs.open('rockyou.txt', encoding='latin1') as f:
    for l in f.readlines():
        if MD2.new((l.strip()).encode()).hexdigest() == "9e46248d91fdcbecb3f4ba7caae38b0d":
            print(f"The password is '{l}'")
            break
