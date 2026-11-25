import hashlib
import os
from fractions import Fraction
from functools import reduce
from math import gcd

HIDDEN = 80
STRIDE = 3

_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "release_files", "output.txt")
exec(open(_OUTPUT).read())


s = old_oak
t = [s[i + 1] - s[i] for i in range(len(s) - 1)]
u = [abs(t[i + 2] * t[i] - t[i + 1] ** 2) for i in range(len(t) - 2)]
m = reduce(gcd, u)
for p in range(2, 10_000):
    while m % p == 0 and m // p > max(s):
        m //= p
a = t[1] * pow(t[0], -1, m) % m
c = (s[1] - a * s[0]) % m
assert all((a * s[i] + c) % m == s[i + 1] for i in range(len(s) - 1))
print(f"[+] m = {m}\n[+] a = {a}\n[+] c = {c}")


def lll(B, delta=Fraction(3, 4)):
    B = [list(map(int, row)) for row in B]
    n = len(B)

    def dot(x, y):
        return sum(i * j for i, j in zip(x, y))

    def gso():
        Bs, mu = [], [[Fraction(0)] * n for _ in range(n)]
        for i in range(n):
            v = [Fraction(x) for x in B[i]]
            for j in range(i):
                mu[i][j] = dot(B[i], Bs[j]) / dot(Bs[j], Bs[j])
                v = [vi - mu[i][j] * bj for vi, bj in zip(v, Bs[j])]
            Bs.append(v)
        return Bs, mu

    Bs, mu = gso()
    k = 1
    while k < n:
        for j in range(k - 1, -1, -1):
            q = round(mu[k][j])
            if q:
                B[k] = [x - q * y for x, y in zip(B[k], B[j])]
                for i in range(j):
                    mu[k][i] -= q * mu[j][i]
                mu[k][j] -= q
        if dot(Bs[k], Bs[k]) >= (delta - mu[k][k - 1] ** 2) * dot(Bs[k - 1], Bs[k - 1]):
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            Bs, mu = gso()
            k = max(k - 1, 1)
    return B


A = pow(a, STRIDE, m)
C = c * sum(pow(a, i, m) for i in range(STRIDE)) % m
H = [h << HIDDEN for h in young_birch]
n = len(H)

Apow = [pow(A, j, m) for j in range(n)]
Cj = [0] * n
for j in range(1, n):
    Cj[j] = (A * Cj[j - 1] + C) % m
Bj = [(Apow[j] * H[0] + Cj[j] - H[j]) % m for j in range(n)]

K = 1 << HIDDEN
M = []
M.append(Apow + [0])
for j in range(1, n):
    M.append([m if i == j else 0 for i in range(n)] + [0])
M.append([0] + Bj[1:] + [K])

for row in lll(M):
    if abs(row[-1]) == K:
        sign = 1 if row[-1] == K else -1
        l0 = sign * row[0]
        if 0 <= l0 < K:
            break
else:
    raise SystemExit("[-] lattice failed")

state = H[0] + l0
for j in range(1, n):
    state = (A * state + C) % m
    assert state >> HIDDEN == young_birch[j]
next_tree = (a * state + c) % m
print(f"[+] next tree = {next_tree}")

key = hashlib.sha256(str(next_tree).encode()).digest()
ct_b = bytes.fromhex(ct)
stream = hashlib.shake_256(key).digest(len(ct_b))
print("[+] flag:", bytes(x ^ y for x, y in zip(ct_b, stream)).decode())
