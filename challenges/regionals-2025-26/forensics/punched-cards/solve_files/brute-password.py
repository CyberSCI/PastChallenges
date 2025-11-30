#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2025/26
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Punched card challenge bruteforcing script

from Crypto.Hash import MD2
from pwn import *

s = iters.mbruteforce(lambda x: MD2.new(("CYBERSCI(PUNCHC4RD_1S_7H3_FL4SH_ST0R@GE_OF_"+x+")").encode()).hexdigest() == "e809236d4b94e54174e666cf3b1f53ce", string.ascii_uppercase + string.digits + "#,$.-@%*<-/+_)|&>:;'?\"=!(,.", 4, 'fixed')