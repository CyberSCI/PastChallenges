from z3 import *
import struct

print("Solving Voting Machine 1")

orig = 0x2B82B772

id = (orig >> 24) ^ 0xd5
id |= (((orig >> 16) & 0xff) ^ 0x8a) << 8
id |= (((orig >> 8) & 0xff) ^ 0x17) << 16
id |= ((orig & 0xff) ^ 0x54) << 24

print(" ", hex(id))
assert(id == 0x26A008FE)

print("\nSolving Voting Machine 2")

solver = Solver()

NUM_CHARS = 10

for i in range(NUM_CHARS):
	globals()['c%i' % i] = BitVec('c%i' % i, 8)

	solver.add(And(globals()['c%i' % i] >= ord('A'), globals()['c%i' % i] <= ord('E')))

solver.add(globals()['c4'] == globals()['c9'])
solver.add(globals()['c5'] - 1 == globals()['c6'] - 1)
solver.add(globals()['c1'] == globals()['c3'])
solver.add(globals()['c0'] + 2 == globals()['c5'] + 2)
solver.add(globals()['c3'] * 5 == (globals()['c7'] * 10) - 345)
solver.add(globals()['c2'] == globals()['c8'])
solver.add(globals()['c0'] + 1 == globals()['c1'] - 1)
solver.add(globals()['c2'] + 1 == globals()['c4'] + 4)
solver.add(globals()['c3'] - 3 == globals()['c4'] + 1)

while solver.check() == z3.sat:  
    solution = "False"
    model = solver.model()

    res = ""
    for i in range(NUM_CHARS):
        obj = globals()['c%i' % i]
        res += chr(model[obj].as_long())
    print(" ", res, "" if res != "CEDEACCEDA" else "(Expected)")

    for i in model:
        solution = f"Or(({i} != {model[i]}), {solution})"
    f2 = eval(solution)
    solver.add(f2)


print("\nSolving Voting Machine 3")

version = bytes("v12.075-20250420", "utf8")

key = ""

for part in range(4):
    val = struct.unpack("<L", version[part*4:part*4+4])[0]
    for i in range(0xdb):
        val = (val + 0xdbdbdbdb) & 0xffffffff
        val = ((val>>1) | (val<<(31))) & 0xffffffff
        val ^= 0xdbdbdbdb
    key += struct.pack('<L', val).hex()
print(' ', key) 
