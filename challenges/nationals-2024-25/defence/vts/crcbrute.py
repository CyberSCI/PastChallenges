# CyberSci Nationals 2024/25
#
# Script to generate voting machine IDs that have the same CRC32 by 0xd13a

from z3 import *
import z3
import random
import binascii
import datetime

polynomial = 0xEDB88320

def crc32(data,size,prev=0):
    crc = prev ^ 0xFFFFFFFF
    for i in range(0,size,8):
        crc = crc ^ (z3.LShR(data,i) & 0xFF)
        for _ in range(8):
            crc = If(crc & 1 == BitVecVal(1, size), z3.LShR(crc,1) ^ polynomial, z3.LShR(crc,1))
    return crc ^ 0xFFFFFFFF

size = 16 * 8

for i in range(100):
    target_crc = random.randint(0, 0xffffffff)
    print(datetime.datetime.now())
    print("\nTarget:", hex(target_crc))

    s = z3.Solver()
    data = z3.BitVec('data',size)
    s.add(crc32(data,size) == target_crc)
    for i in range(0,size,8):
        s.add(Or(And(((z3.LShR(data,i) & 0xFF) >= 0x30),((z3.LShR(data,i) & 0xFF) <= 0x39)),
                 And(((z3.LShR(data,i) & 0xFF) >= 0x61),((z3.LShR(data,i) & 0xFF) <= 0x66))))

    iteration = 0
    while (iteration < 2) and (s.check() == z3.sat):
        print(datetime.datetime.now())
        print(binascii.unhexlify(hex(int(str(s.model()[data])))[2:])[::-1].decode())
        s.add(data != int(str(s.model()[data])))
        iteration += 1
