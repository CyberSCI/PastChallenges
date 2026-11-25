import base64
import random
from pathlib import Path

import requests

LOGS_DIR = Path("./logs")
OUTPUT_DIR = Path("./requests")
URL = "http://localhost:3333/logs"
NUM_IDS = 10
FILES_PER_ID = 30
TIMEOUT = 30


def list_log_files(folder):
    """Return the filenames (not full paths) of every file in the folder."""
    if not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")
    return [p.name for p in folder.iterdir() if p.is_file()]


def main():
    all_files = list_log_files(LOGS_DIR)

    if len(all_files) < FILES_PER_ID:
        raise SystemExit(
            f"Need at least {FILES_PER_ID} files in '{LOGS_DIR}', found {len(all_files)}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for log_id in range(1, NUM_IDS + 1):
        # Unique within this id, but the same file can appear under other ids
        filenames = random.sample(all_files, FILES_PER_ID)
        filenames = [f"./logs/{fn}" for fn in filenames]

        # One POST per id, body is a JSON array of filenames
        response = requests.post(URL, json=filenames, timeout=TIMEOUT, stream=True)
        response.raise_for_status()

        # Read the raw gzip bytes (decode_content=False prevents requests/urllib3
        # from transparently decompressing if the server sets Content-Encoding: gzip)
        gzip_bytes = response.raw.read(decode_content=False)
        gzip_b64 = base64.b64encode(gzip_bytes).decode("ascii")

        # File "{id}": one filename per line, base64 gzip on the last line
        out_path = OUTPUT_DIR / str(log_id)
        with open(out_path, "w") as f:
            f.write("\n".join(filenames))
            f.write("\n")
            f.write(gzip_b64)

        print(f"[{log_id}/{NUM_IDS}] saved {out_path} ({len(gzip_bytes)} bytes gzip)")


if __name__ == "__main__":
    main()