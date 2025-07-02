import math
from Crypto.Util.number import getPrime
from secret import FLAG

BITS = 4096
PRIMES = 64

primes = [getPrime(BITS // PRIMES) for _ in range(PRIMES)]

n = math.prod(primes)
phi = math.prod(p - 1 for p in primes)
e = 65537

m = int.from_bytes(FLAG, 'big')
c = pow(m, e, n)

print(f'{n = }')
print(f'{e = }')
print(f'{c = }')