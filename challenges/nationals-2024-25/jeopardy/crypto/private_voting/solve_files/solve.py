from pwn import *
import random

CANDIDATE_COUNT = 10
VOTE_SUBTRACT_AMT = -15
VOTE_ADD_AMT = 1 - VOTE_SUBTRACT_AMT * (CANDIDATE_COUNT - 1)


def paillier_encrypt(pk, m, r):
    n, g = pk
    c = pow(g, m, n**2) * pow(r, n, n**2) % (n**2)
    return c


# A couple attempts might be needed.
for _ in range(5):
    conn = remote('10.0.2.11', 1337)
    #conn = process(["python3", "../server_files/private_voting.py"])

    conn.recvuntil(b"n = ")
    n = int(conn.recvline().decode().strip())

    conn.recvuntil(b"g = ")
    g = int(conn.recvline().decode().strip())

    selected_candidate = 9

    # create unencrypted vote
    vote = [n + VOTE_SUBTRACT_AMT] * CANDIDATE_COUNT
    vote[selected_candidate] = VOTE_ADD_AMT

    C = []
    R = 1
    for m in vote:
        r = random.randint(1, n - 1)
        c = paillier_encrypt((n, g), m, r)
        C.append(c)
        R = (R * r) % n

    for c in C:
        conn.recvuntil(b' = ')
        conn.sendline(str(c).encode())
    conn.recvuntil(b' = ')
    conn.sendline(str(R).encode())

    output = conn.recvall().decode()
    
    if 'cybersci{' in output:
        print(output)
        break 