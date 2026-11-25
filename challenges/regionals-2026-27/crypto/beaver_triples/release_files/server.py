import os
import secrets
import sys

P = 2**127 - 1
FLAG = os.environ.get(
    "FLAG", "CyberSci{this_is_a_fake_flag}"
).encode()
CHUNK = 15
POOL_SIZE = 16
MAX_QUERIES = 400


def share(v):
    r = secrets.randbelow(P)
    return [r, (v - r) % P]


def reveal(sh):
    return sum(sh) % P


class Dealer:

    def __init__(self):
        self.pool = []
        for _ in range(POOL_SIZE):
            a = secrets.randbelow(P)
            b = secrets.randbelow(P)
            self.pool.append((a, b, a * b % P))

    def triple(self):
        a, b, c = secrets.choice(self.pool)
        return share(a), share(b), share(c)


def beaver_mul(xs, ys, dealer):
    A, B, C = dealer.triple()
    d = reveal([(xs[i] - A[i]) % P for i in range(2)])
    e = reveal([(ys[i] - B[i]) % P for i in range(2)])
    zs = [(C[i] + d * B[i] + e * A[i]) % P for i in range(2)]
    zs[0] = (zs[0] + d * e) % P
    return zs, d, e


def out(s=""):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()


def main():
    sections = [int.from_bytes(FLAG[i:i + CHUNK], "big")
                for i in range(0, len(FLAG), CHUNK)]
    dealer = Dealer()

    out("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    out("  Welcome to the Lodge's Secure Dam Computation Service")
    out("  Two beavers, two secret shares, one careful lodge.")
    out("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    out(f"Field prime P = {P}")
    out(f"Bucky's blueprint has {len(sections)} dam sections.")

    for _ in range(MAX_QUERIES):
        out()
        out("[1] Practice round")
        out("[2] Inspect a dam section")
        out("[3] Swim away")
        out("> ")
        choice = sys.stdin.readline().strip()

        if choice == "1":
            try:
                out("u = ")
                u = int(sys.stdin.readline()) % P
                out("v = ")
                v = int(sys.stdin.readline()) % P
            except ValueError:
                out("That's not a number, that's a twig.")
                continue
            zs, d, e = beaver_mul(share(u), share(v), dealer)
            out(f"opened d = {d}")
            out(f"result   = {reveal(zs)}")

        elif choice == "2":
            try:
                out("section index = ")
                i = int(sys.stdin.readline())
                assert 0 <= i < len(sections)
            except (ValueError, AssertionError):
                out("No such section in this dam.")
                continue
            y = secrets.randbelow(P)
            zs, d, e = beaver_mul(share(sections[i]), share(y), dealer)
            out(f"opened d = {d}")
            out("result   = <delivered privately to Bucky>")

        else:
            out("Splash! Goodbye.")
            return

    out("The lodge is tired. Come back tomorrow.")


if __name__ == "__main__":
    main()
