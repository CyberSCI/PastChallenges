#!/usr/bin/env python3
"""Solution for Flag 1: Tokenizer Steganography"""

from pathlib import Path
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")

passage_path = Path(__file__).resolve().parent.parent / "release_files" / "passage.txt"
with open(passage_path) as f:
    text = f.read()

ids = tokenizer.encode(text, add_special_tokens=False)
bits = [token_id % 2 for token_id in ids]

chars = []
for i in range(0, len(bits) - len(bits) % 8, 8):
    byte = 0
    for b in bits[i:i + 8]:
        byte = (byte << 1) | b
    chars.append(chr(byte))

flag = "".join(chars)
print(f"Flag 1: {flag}")
