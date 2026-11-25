import hashlib
import os
import secrets

FLAG = os.environ.get(
    "FLAG", "CyberSci{this_is_a_fake_flag}"
).encode()

BITS = 128
HIDDEN = 80
STRIDE = 3
N_OLD = 10
N_YOUNG = 12


def is_prime(n, rounds=40):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        x = pow(secrets.randbelow(n - 3) + 2, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def random_prime(bits):
    while True:
        n = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(n):
            return n


class RingCounter:
    def __init__(self, m, a, c, seed):
        self.m, self.a, self.c, self.state = m, a, c, seed

    def next(self):
        self.state = (self.a * self.state + self.c) % self.m
        return self.state


def main():
    m = random_prime(BITS)
    a = secrets.randbelow(m)
    c = secrets.randbelow(m)

    oak = RingCounter(m, a, c, secrets.randbelow(m))
    old_oak = [oak.next() for _ in range(N_OLD)]

    birch = RingCounter(m, a, c, secrets.randbelow(m))
    young_birch = []
    for _ in range(N_YOUNG):
        for _ in range(STRIDE - 1):
            birch.next()
        young_birch.append(birch.next() >> HIDDEN)

    next_tree = birch.next()
    key = hashlib.sha256(str(next_tree).encode()).digest()
    stream = hashlib.shake_256(key).digest(len(FLAG))
    ct = bytes(x ^ y for x, y in zip(FLAG, stream))

    with open("output.txt", "w") as f:
        f.write(f"old_oak = {old_oak}\n")
        f.write(f"young_birch = {young_birch}\n")
        f.write(f"ct = '{ct.hex()}'\n")


if __name__ == "__main__":
    main()
