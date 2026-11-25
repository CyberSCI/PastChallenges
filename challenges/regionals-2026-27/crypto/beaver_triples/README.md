# Beaver Triples

**Author:** Zachary Mambret / Seneque

**Category:** Crypto

## Description

Two-party secret sharing with Beaver multiplication, where the "trusted dealer"
re-shares from a fixed pool of 16 triples every round. Because the masks
`(a, b)` are reused, the opened values `d = x - a` leak, and a practice round
with `u = v = 0` lets the player harvest the whole pool and recover the secret
blueprint (the flag). Difficulty: medium.

### Files

- `release_files/server.py`
### Host

`nc <host> 1337`

## Part 1

**CTFd name:** Beaver Triples

### CTFd Description

Bucky will happily measure his dam with you all day. He's quite sure you'll
never learn a thing about it.

`nc <host> 1337`

Files: `server.py`

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{tr1pl3s_4r3_0n3_t1m3_p4ds_n0t_r3cycl4bl3_l0gs}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

In Beaver multiplication, the opened values `d = x - a` and `e = y - b` are safe
only because `(a, b)` are uniformly random one-time masks. The dealer draws from
a fixed pool of 16 triples, and re-sharing them changes the shares but not the
values `a` and `b`.

1. Use the practice round with `u = v = 0`. The opened `d` equals `-a`, so each
   practice query leaks one pooled `a`. About 50–60 queries collect all 16.
2. Inspect each dam section. The opened `d = x_i - a`, so `x_i` is one of 16
   candidates `d + a`. Only the real one decodes to printable ASCII; if two
   candidates survive, inspect again and intersect.

`solve_files/solve.py`:

</details>