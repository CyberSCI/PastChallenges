import math

BITS = 256
PRIMES = 16

n = 796619421721763408110066621894301379640702094358332972179336180714381814791
e = 65537
c = 760460476332603195975870956320663031030142509238270316470240866540546100772

PRIME_BITS = BITS // PRIMES

primes = []

product = n

for i in range(2, 2 ** PRIME_BITS):
    while product % i == 0:
        print('Found factor:', i)
        primes.append(i)
        product //= i

phi = math.prod(p - 1 for p in primes)
d = pow(e, -1, phi)

m = pow(c, d, n)
flag = int.to_bytes(m, (m.bit_length() + 7) // 8, 'big').decode()

print(flag)