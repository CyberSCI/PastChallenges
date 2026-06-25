#!/usr/bin/env python3
"""
Flag 2 Generator: Ghost in the Weights

Creates a safetensors file with an embedding matrix. Most rows are random
noise (simulating trained weights), but a contiguous block of rows in the
unused/reserved token ID range has been overwritten: the first element of
each row is the float32 ASCII code of a flag character, and the rest are 0.0.
"""

import numpy as np
from pathlib import Path
from safetensors.numpy import save_file

FLAG = "CyberSci{3mb3dd1ng_gh0st_w31ght5}"
VOCAB_SIZE = 151936
EMBED_DIM = 896
START_ROW = 151900
OUTPUT = Path(__file__).resolve().parent.parent / "release_files" / "embeddings.safetensors"

np.random.seed(1337)


def main():
    print(f"[*] Creating embedding matrix: {VOCAB_SIZE} x {EMBED_DIM}")
    matrix = np.random.randn(VOCAB_SIZE, EMBED_DIM).astype(np.float32)

    print(f"[*] Injecting flag at rows {START_ROW}-{START_ROW + len(FLAG) - 1}")
    for i, ch in enumerate(FLAG):
        row = START_ROW + i
        matrix[row, 0] = float(ord(ch))
        matrix[row, 1:] = 0.0

    print(f"[*] Saving to {OUTPUT}")
    save_file({"model.embed_tokens.weight": matrix}, OUTPUT)

    size_mb = (VOCAB_SIZE * EMBED_DIM * 4) / (1024 * 1024)
    print(f"[+] Wrote {OUTPUT} (~{size_mb:.0f} MB)")
    print(f"[+] Flag 2: {FLAG}")


if __name__ == "__main__":
    main()
