# Tree Rings

**Author:** Zachary Mambret / Seneque

**Category:** Crypto

## Description

A two-stage LCG challenge. Stage 1 (the "Old Oak") gives full LCG outputs, from
which the modulus and multiplier are recovered. Stage 2 (the "Young Birch") uses
the same LCG with a fresh seed but reveals only the top 48 of every 128-bit
state, and only every third state. Can be solved with LLL. Recovering the next state yields the key that decrypts the
flag. Difficulty: hard.

### Files

- `release_files/generate.py`
- `release_files/output.txt`

### Host

N/A

## Part 1

**CTFd name:** Tree Rings

### CTFd Description

The lodge marks every tree it fells with an ancient counting rite. Bucky's
certain no one will ever guess which tree falls next.

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{0ld_04k_l34k3d_th3_m0dulus_y0ung_b1rch_l34k3d_th3_st4t3}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

**Stage 1 — Old Oak** (unknown `m`, `a`, `c`, full outputs). Differences
`t_i = s_{i+1} − s_i` satisfy `t_{i+1} ≡ a·t_i`, so `t_{i+2}·t_i − t_{i+1}² ≡ 0
(mod m)`. Taking the gcd of several such values gives `m`, then `a = t_1·t_0⁻¹`
and `c = s_1 − a·s_0`.

**Stage 2 — Young Birch** (only the top 48 of 128 bits of every third state).
Stepping three at a time is still an LCG with `A = a³` and `C = c(a² + a + 1)`.
Writing `s_j = H_j·2⁸⁰ + l_j` with unknown 80-bit `l_j` gives
`l_j ≡ A^j·l_0 + B_j (mod m)` for known `B_j`. The vector `(l_0, …, l_11)` is
short in a lattice built from `(1, A, A², …)`, `m·e_j` rows and an embedding row
with the `B_j`, so LLL recovers it. From there, step once more, hash the state
and decrypt.

</details>
