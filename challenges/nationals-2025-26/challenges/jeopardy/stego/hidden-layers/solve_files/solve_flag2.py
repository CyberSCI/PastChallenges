#!/usr/bin/env python3
"""Solution for Flag 2: Ghost in the Weights"""

import numpy as np
from pathlib import Path
from safetensors.numpy import load_file

embeddings_path = Path(__file__).resolve().parent.parent / "release_files" / "embeddings.safetensors"
tensors = load_file(str(embeddings_path))
embed = tensors["model.embed_tokens.weight"]

print(f"Embedding shape: {embed.shape}")

row_norms = np.linalg.norm(embed[:, 1:], axis=1)
anomalous = np.where(row_norms == 0.0)[0]

print(f"Found {len(anomalous)} anomalous rows at indices: {anomalous.tolist()}")

flag = "".join(chr(int(embed[row, 0])) for row in anomalous)
print(f"Flag 2: {flag}")
