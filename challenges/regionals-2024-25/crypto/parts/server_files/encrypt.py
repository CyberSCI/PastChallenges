from Crypto.Util.number import getPrime, bytes_to_long
from Crypto.Util.Padding import pad
from secret import MESSAGE

p = getPrime(512)
q = getPrime(512)

n = p * q
e = 0x10001

pt = pad(MESSAGE, 4)
ct = []

for i in range(0, len(pt), 4):
    pt_block = bytes_to_long(pt[i:i+4])
    ct_block = pow(pt_block, e, n)
    ct.append(ct_block)

print(f'{n = }')
print(f'{e = }')
print(f'{ct = }')