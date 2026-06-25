#!/usr/bin/env python3
"""
Flag 1 Generator: Tokenizer Steganography

Crafts a text passage where the LSB of each Qwen token ID,
concatenated in order, forms a bitstream encoding the flag in ASCII.
"""

import random
import string
from pathlib import Path
from transformers import AutoTokenizer

FLAG = "CyberSci{qw3n_t0k3n1z3r_LSB}"
MODEL_ID = "Qwen/Qwen2.5-0.5B"
OUTPUT = Path(__file__).resolve().parent.parent / "release_files" / "passage.txt"

random.seed(42)


def flag_to_bits(flag: str) -> list[int]:
    bits = []
    for ch in flag:
        val = ord(ch)
        for shift in range(7, -1, -1):
            bits.append((val >> shift) & 1)
    return bits


def is_nice_token(decoded: str) -> bool:
    if len(decoded) < 2:
        return False
    if not all(c in string.printable for c in decoded):
        return False
    if any(c in decoded for c in "\n\t\r\x0b\x0c"):
        return False
    if decoded.strip() == "":
        return False
    return True


def main():
    print(f"[*] Loading tokenizer: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    vocab = tokenizer.get_vocab()
    print(f"[*] Vocab size: {len(vocab)}")

    even_tokens = []
    odd_tokens = []

    for token_str, token_id in vocab.items():
        decoded = tokenizer.decode([token_id])
        if not is_nice_token(decoded):
            continue
        if token_id % 2 == 0:
            even_tokens.append(token_id)
        else:
            odd_tokens.append(token_id)

    print(f"[*] Usable tokens: {len(even_tokens)} even (LSB=0), {len(odd_tokens)} odd (LSB=1)")

    bits = flag_to_bits(FLAG)
    print(f"[*] Flag '{FLAG}' -> {len(bits)} bits -> need {len(bits)} tokens")

    max_retries = 100
    selected_ids = []

    for i, bit in enumerate(bits):
        pool = odd_tokens if bit == 1 else even_tokens
        random.shuffle(pool)

        placed = False
        for attempt in range(min(max_retries, len(pool))):
            candidate_id = pool[attempt]
            trial = selected_ids + [candidate_id]
            text = tokenizer.decode(trial)
            re_encoded = tokenizer.encode(text, add_special_tokens=False)

            if re_encoded == trial:
                selected_ids.append(candidate_id)
                placed = True
                break

        if not placed:
            print(f"[!] Warning: could not find round-trip safe token for bit {i} (bit={bit}), using first candidate")
            selected_ids.append(pool[0])

    passage = tokenizer.decode(selected_ids)

    final_ids = tokenizer.encode(passage, add_special_tokens=False)
    if final_ids == selected_ids:
        print("[+] Round-trip verification PASSED")
    else:
        mismatches = sum(1 for a, b in zip(final_ids, selected_ids) if a != b)
        print(f"[!] Round-trip verification FAILED: {mismatches} mismatches out of {len(selected_ids)}")
        print("[!] The challenge may not solve cleanly. Consider re-running with a different seed.")

    with open(OUTPUT, "w") as f:
        f.write(passage)

    print(f"[+] Wrote {len(passage)} chars to {OUTPUT}")
    print(f"[+] Flag 1: {FLAG}")


if __name__ == "__main__":
    main()
