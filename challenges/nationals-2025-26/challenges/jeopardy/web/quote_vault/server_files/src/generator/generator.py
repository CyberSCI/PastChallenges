#!/usr/bin/env python3
"""ocr-rotator generator.

Every ROTATION_INTERVAL seconds:
  - pick NUM_IMAGES unique 4-word phrases from the wordlist; choose one
  - render PNGs into /data/gen-N/images/img-NNNNN.png with the phrases drawn on them
  - all images get a 'Comment' tEXt chunk with random text
  - the chosen image gets an additional 'Solution' tEXt chunk (this is the hint)
  - the folder identifier for each phrase is HMAC-SHA256(phrase, HMAC_KEY)[:16]
    — the front-end exposes the same key in /js/app.js + a /verify page so
    players can compute card identifiers themselves
  - build /data/gen-N/db.sqlite holding:
      * a `quotes` table seeded with a few public quotes (red herrings),
      * a `secrets` table with one row per folder identifier; the chosen
        folder's row holds the real flag, the others hold random decoys with
        the same format. All secrets rows are public=0.
  - atomically swap /data/current to point at the new generation
  - keep the previous generation alive for GRACE_WINDOW seconds
"""

import hashlib
import hmac
import os
import random
import secrets
import shutil
import sqlite3
import string
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

DATA_ROOT = Path("/data")
CURRENT = DATA_ROOT / "current"

NUM_IMAGES = 5000
ROTATION_INTERVAL = 50          # seconds between rotations
GRACE_WINDOW = 5                # keep previous generation alive this long after rotation

WORDS_PER_PHRASE = 4
FOLDER_ID_LEN = 16              # number of hex chars taken from HMAC output
# Must match QV_SIGNING_KEY in src/site/js/app.js. The front-end uses the
# same key client-side to compute a card's identifier on the /verify page.
HMAC_KEY = b"qv-card-signing-2026"

FLAG_PREFIX = "Cybersci{"
FLAG_SUFFIX = "}"
FLAG_BODY_LEN = 24
FLAG_BODY_ALPHABET = string.ascii_letters + string.digits
FLAG_REAL = "Cybersci{vXukCggDCyberScigQKscRDR}"

# Constant flag stamped into the PNG `Flag` tEXt chunk on every card.
# Anyone reading metadata on any image gets it.
FLAG_IMAGE_META = "Cybersci{on-every-card-Q2eR8nFsD}"

# (The PoW-replay flag lives entirely in the proxy now — emitted as an
# `X-Audit-Token` response header when the proxy detects a nonce being
# reused for a different filename than the one it was registered for.
# See src/pow-server/pow_server.py.)

IMG_W, IMG_H = 720, 100
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SIZE = 32

PROCESS_WORKERS = max(2, os.cpu_count() or 2)
DEBUG = os.environ.get("OCR_DEBUG", "").lower() in ("1", "true", "yes", "on")

# 200+ common 4-7 letter English words. Chosen to be OCR-friendly: no
# digits, no punctuation, no homophones with confusing letter pairs.
WORDS = sorted(set([
    # nature
    "river", "ocean", "forest", "valley", "meadow", "cliff", "summit",
    "canyon", "prairie", "harbor", "beach", "desert", "creek", "glacier",
    "lagoon", "marsh", "fjord", "delta", "ridge", "savanna", "tundra",
    "estuary", "ravine", "knoll", "dune", "atoll",
    # weather / sky
    "cloud", "storm", "thunder", "rainbow", "sunset", "sunrise", "comet",
    "planet", "galaxy", "nebula", "aurora", "twilight", "dawn", "dusk",
    "breeze", "gale", "frost", "blizzard", "drizzle",
    # animals
    "rabbit", "falcon", "eagle", "tiger", "panda", "otter", "horse",
    "raven", "robin", "sparrow", "hawk", "lion", "moose", "bison",
    "panther", "leopard", "jaguar", "cheetah", "shark", "whale",
    "dolphin", "salmon", "trout", "heron", "swan", "magpie", "stork",
    "crane", "lemur", "wombat",
    # plants
    "willow", "cedar", "birch", "maple", "tulip", "lily", "bamboo",
    "spruce", "clover", "daisy", "violet", "poppy", "orchid", "thistle",
    "jasmine", "fern", "moss",
    # objects
    "bridge", "anchor", "beacon", "tower", "castle", "garden", "lantern",
    "compass", "scroll", "amulet", "shield", "arrow", "harp", "torch",
    "anvil", "forge", "saddle", "barrel", "chalice",
    # materials / stones
    "silver", "golden", "iron", "copper", "marble", "amber", "crystal",
    "jade", "pearl", "ivory", "bronze", "ruby", "sapphire", "emerald",
    "topaz", "onyx",
    # adjectives
    "mighty", "swift", "silent", "ancient", "noble", "calm", "brave",
    "fierce", "gentle", "humble", "loyal", "stern", "rugged", "frozen",
    "glowing", "blazing", "shining", "quiet", "stormy",
    # mythical / abstract
    "shadow", "shimmer", "gleam", "midnight", "phoenix", "dragon",
    "griffin", "kraken", "serpent", "wraith", "spirit", "echo", "ember",
    "haze", "vapor", "ripple", "current", "tide", "torrent", "cascade",
    "ash", "dust", "mist",
]))


DECOY_COMMENT_BASE = [
    "rendered",
    "challenge image",
    "img",
    "test pattern",
    "auto-generated",
    "frame",
    "tile",
    "raster",
    "do not enhance",
    "see metadata",
]

QUOTES_SEED = [
    (1, "Two things are infinite: the universe and human stupidity; and I'm not sure about the universe.", "Albert Einstein"),
    (2, "Be the change that you wish to see in the world.", "Mahatma Gandhi"),
    (3, "So many books, so little time.", "Frank Zappa"),
    (4, "A room without books is like a body without a soul.", "Marcus Tullius Cicero"),
    (5, "You only live once, but if you do it right, once is enough.", "Mae West"),
    (6, "Be yourself; everyone else is already taken.", "Oscar Wilde"),
    (7, "If you tell the truth, you don't have to remember anything.", "Mark Twain"),
    (8, "I have not failed. I've just found 10,000 ways that won't work.", "Thomas A. Edison"),
    (9, "It is better to be hated for what you are than to be loved for what you are not.", "Andre Gide"),
    (10, "Without music, life would be a mistake.", "Friedrich Nietzsche"),
]


def random_phrase(n: int = WORDS_PER_PHRASE) -> str:
    """N unique random words joined by single spaces."""
    return ' '.join(secrets_random_sample(WORDS, n))


def secrets_random_sample(pool, k):
    """Like random.sample, but draws from os.urandom (via secrets)."""
    pool = list(pool)
    out = []
    for _ in range(k):
        i = secrets.randbelow(len(pool))
        out.append(pool.pop(i))
    return out


def folder_id_for(phrase: str) -> str:
    """The folder identifier the API/SQLi uses to look up a flag.

    Must match the JS computeCardId() in src/site/js/app.js — both compute
    HMAC-SHA256 of the (normalized) phrase under HMAC_KEY and take the first
    FOLDER_ID_LEN hex chars.
    """
    normalized = ' '.join(phrase.lower().split())
    sig = hmac.new(HMAC_KEY, normalized.encode('utf-8'), hashlib.sha256).hexdigest()
    return sig[:FOLDER_ID_LEN]


def random_flag() -> str:
    body = ''.join(
        secrets.choice(FLAG_BODY_ALPHABET) for _ in range(FLAG_BODY_LEN)
    )
    return FLAG_PREFIX + body + FLAG_SUFFIX


def random_decoy_comment() -> str:
    base = random.choice(DECOY_COMMENT_BASE)
    suffix = ''.join(random.choices(string.hexdigits.lower(), k=random.randint(2, 8)))
    return f"{base} {suffix}"


def render_image(text: str, out_path: Path, is_chosen: bool) -> None:
    bg = (random.randint(235, 252), random.randint(235, 252), random.randint(235, 252))
    img = Image.new('RGB', (IMG_W, IMG_H), color=bg)

    # Light speckle background — enough to require a CTF-grade OCR call,
    # not so much that vanilla tesseract drops characters.
    pixels = img.load()
    for _ in range((IMG_W * IMG_H) // 200):
        x, y = random.randint(0, IMG_W - 1), random.randint(0, IMG_H - 1)
        c = random.randint(180, 220)
        pixels[x, y] = (c, c, c)

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (IMG_W - tw) // 2 - bbox[0]
    y = (IMG_H - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=(15, 15, 15), font=font)

    pnginfo = PngInfo()
    pnginfo.add_text("Comment", random_decoy_comment())
    pnginfo.add_text("Flag", FLAG_IMAGE_META)
    if is_chosen:
        pnginfo.add_text("Solution", "true")

    img.save(out_path, format='PNG', pnginfo=pnginfo, optimize=False)


def render_one(args):
    # Reseed: forked workers inherit parent RNG state and would otherwise produce
    # correlated output across the pool.
    random.seed()
    idx, text, is_chosen, gen_dir_str = args
    gen_dir = Path(gen_dir_str)
    img_path = gen_dir / "images" / f"img-{idx:05d}.png"
    render_image(text, img_path, is_chosen)


def write_database(gen_dir: Path, phrases, chosen_idx: int, real_flag: str) -> None:
    db_path = gen_dir / "db.sqlite"
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE quotes (
                id     INTEGER PRIMARY KEY,
                value  TEXT NOT NULL,
                author TEXT NOT NULL,
                public INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE secrets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_name TEXT UNIQUE NOT NULL,
                flag        TEXT NOT NULL,
                public      INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX idx_secrets_folder ON secrets(folder_name);
            """
        )
        cur.executemany(
            "INSERT INTO quotes (id, value, author, public) VALUES (?, ?, ?, 1)",
            QUOTES_SEED,
        )
        secret_rows = []
        for i, phrase in enumerate(phrases):
            flag = real_flag if i == chosen_idx else random_flag()
            secret_rows.append((folder_id_for(phrase), flag))
        # Shuffle the insertion order so the auto-increment secrets.id
        # does NOT correlate with the image filename index. Without this,
        # img-NNNNN.png maps directly to secrets.id = NNNNN, which lets a
        # solver skip OCR + HMAC entirely and just SQLi `WHERE id = NNNNN`
        # for whichever image had the Solution metadata. After the
        # shuffle, the chosen phrase's row gets a random id and the only
        # way to find it is the intended OCR -> HMAC -> folder_name path.
        random.shuffle(secret_rows)
        cur.executemany(
            "INSERT INTO secrets (folder_name, flag, public) VALUES (?, ?, 0)",
            secret_rows,
        )
        conn.commit()
    finally:
        conn.close()


def generate_cycle(gen_id: int):
    gen_dir = DATA_ROOT / f"gen-{gen_id}"
    (gen_dir / "images").mkdir(parents=True, exist_ok=True)

    used = set()
    phrases = []
    while len(phrases) < NUM_IMAGES:
        p = random_phrase()
        if p not in used:
            used.add(p)
            phrases.append(p)

    chosen_idx = secrets.randbelow(NUM_IMAGES)
    real_flag = FLAG_REAL

    # Render images in parallel.
    args = [(i + 1, p, i == chosen_idx, str(gen_dir)) for i, p in enumerate(phrases)]
    with ProcessPoolExecutor(max_workers=PROCESS_WORKERS) as pool:
        for _ in pool.map(render_one, args, chunksize=64):
            pass

    # Write the SQLite database (single-threaded; fast — bulk insert of 5000 rows).
    write_database(gen_dir, phrases, chosen_idx, real_flag)

    chosen_phrase = phrases[chosen_idx]
    return gen_dir, real_flag, chosen_phrase, folder_id_for(chosen_phrase)


def atomic_swap_current(target: Path) -> None:
    tmp = DATA_ROOT / "current.tmp"
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    tmp.symlink_to(target)
    os.replace(tmp, CURRENT)  # atomic on POSIX


def cleanup_pending(deletions) -> None:
    now = time.monotonic()
    keep = []
    for delete_at, path in deletions:
        if delete_at <= now:
            shutil.rmtree(path, ignore_errors=True)
        else:
            keep.append((delete_at, path))
    deletions[:] = keep


def cleanup_orphaned() -> None:
    """Remove any leftover gen-* dirs and stale 'current' symlink at startup."""
    if not DATA_ROOT.exists():
        return
    for entry in DATA_ROOT.iterdir():
        if entry.name.startswith("gen-") and entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        elif entry.name == "current" and (entry.is_symlink() or entry.exists()):
            try:
                entry.unlink()
            except (IsADirectoryError, OSError):
                shutil.rmtree(entry, ignore_errors=True)
        elif entry.name == "current.tmp" and (entry.is_symlink() or entry.exists()):
            try:
                entry.unlink()
            except (IsADirectoryError, OSError):
                shutil.rmtree(entry, ignore_errors=True)


def log(msg: str) -> None:
    print(msg, flush=True)


def log_cycle(gen_id: int, real_flag: str, chosen_phrase: str,
              chosen_folder: str, gen_time: float) -> None:
    if DEBUG:
        log(f"[gen-{gen_id}] generated in {gen_time:.2f}s | "
            f"chosen='{chosen_phrase}' | folder={chosen_folder} | flag={real_flag}")
    else:
        log(f"[gen-{gen_id}] generated in {gen_time:.2f}s")


def main() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    cleanup_orphaned()

    gen_id = 0
    pending_deletions = []

    log(f"[gen-{gen_id}] generating initial cycle ({NUM_IMAGES} images + db, {PROCESS_WORKERS} workers)…")
    t0 = time.monotonic()
    current_dir, real_flag, chosen_phrase, chosen_folder = generate_cycle(gen_id)
    log_cycle(gen_id, real_flag, chosen_phrase, chosen_folder, time.monotonic() - t0)
    atomic_swap_current(current_dir)
    next_swap_at = time.monotonic() + ROTATION_INTERVAL
    log(f"[gen-{gen_id}] active for {ROTATION_INTERVAL}s")

    while True:
        gen_id += 1

        log(f"[gen-{gen_id}] generating…")
        t0 = time.monotonic()
        next_dir, next_flag, next_phrase, next_folder = generate_cycle(gen_id)
        gen_time = time.monotonic() - t0
        log_cycle(gen_id, next_flag, next_phrase, next_folder, gen_time)

        cleanup_pending(pending_deletions)

        wait = next_swap_at - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        elif wait < -1:
            log(f"WARNING: gen-{gen_id} ran {-wait:.1f}s past its rotation slot")

        atomic_swap_current(next_dir)
        next_swap_at = time.monotonic() + ROTATION_INTERVAL
        log(f"[gen-{gen_id}] active for {ROTATION_INTERVAL}s")

        pending_deletions.append((time.monotonic() + GRACE_WINDOW, current_dir))
        current_dir = next_dir


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
