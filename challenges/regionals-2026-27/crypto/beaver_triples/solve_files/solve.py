import os
import socket
import subprocess
import sys

SERVER_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "release_files", "server.py")

P = 2**127 - 1
POOL_SIZE = 16


class Tube:
    def __init__(self, argv):
        if len(argv) == 3:
            s = socket.create_connection((argv[1], int(argv[2])))
            self.r = s.makefile("r")
            self.w = s.makefile("w")
        else:
            p = subprocess.Popen([sys.executable, SERVER_PY], text=True,
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.r, self.w = p.stdout, p.stdin

    def until(self, marker):
        lines = []
        while True:
            line = self.r.readline()
            if not line:
                raise EOFError
            lines.append(line.rstrip("\n"))
            if marker in line:
                return lines

    def send(self, s):
        self.w.write(f"{s}\n")
        self.w.flush()


def value(lines, key):
    for line in lines:
        if line.startswith(key):
            return int(line.split("=")[1])
    raise ValueError(key)


def plausible(x):
    if x.bit_length() > 120:
        return None
    b = x.to_bytes((x.bit_length() + 7) // 8, "big")
    return b if b and all(32 <= c < 127 for c in b) else None


def main():
    t = Tube(sys.argv)
    banner = t.until("> ")
    n_sections = int(next(l for l in banner if "has" in l).split()[3])

    def practice():
        t.send(1); t.until("u = "); t.send(0); t.until("v = "); t.send(0)
        lines = t.until("> ")
        return (-value(lines, "opened d")) % P

    def inspect(i):
        t.send(2); t.until("section index"); t.send(i)
        return value(t.until("> "), "opened d")

    pool = set()
    while len(pool) < POOL_SIZE:
        pool.add(practice())
    print(f"[+] harvested {len(pool)} reused triples")

    flag = b""
    for i in range(n_sections):
        cands = None
        while cands is None or len(cands) != 1:
            d = inspect(i)
            found = {b for a in pool if (b := plausible((d + a) % P))}
            if found:
                cands = found if cands is None else cands & found
        flag += cands.pop()
    print("[+] flag:", flag.decode())
    t.send(3)
    t.r.read()


if __name__ == "__main__":
    main()
