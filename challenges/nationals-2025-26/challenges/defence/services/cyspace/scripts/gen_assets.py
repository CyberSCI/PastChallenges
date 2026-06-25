#!/usr/bin/env python3
"""
One-off asset authoring script for CySpace.

Generates indexed-palette GIFs and writes them under release_files/src/assets/.
The output bytes are committed to the repo; this script is kept for
reproducibility but is not run at container build.

  logo.gif                     220x48   cobalt wordmark + tagline
  avatar_default.gif           160x160  grey silhouette
  online_bolt.gif               12x12   yellow lightning bolt
  avatars/<username>.gif       160x160  per-seed-user procedural portrait
  glitter/star.gif              16x16   animated 4-frame sparkle
  glitter/friends.gif          120x16   animated "FRIENDS 4 LIFE" text
  glitter/flame.gif             16x20   animated 4-frame flame

Run from the challenge root:
    .venv/bin/python3 scripts/gen_assets.py
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "release_files",
    "src",
    "assets",
)

COBALT = (0, 51, 153)
COBALT_MED = (110, 142, 218)
WHITE = (255, 255, 255)
YELLOW = (255, 204, 0)
PALE_YELLOW = (255, 255, 204)
GREY_BG = (204, 204, 204)
GREY_FG = (102, 102, 102)
BLACK = (0, 0, 0)


def _font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


# ----------------------------------------------------------------------------
# original three (logo, default avatar, online bolt)
# ----------------------------------------------------------------------------

def make_logo():
    w, h = 220, 48
    img = Image.new("RGB", (w, h), COBALT)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline=COBALT_MED)

    title_font = _font(22)
    tag_font = _font(10)

    draw.text((10, 4), "CySpace", fill=WHITE, font=title_font)
    draw.text((136, 8), ".com", fill=YELLOW, font=_font(16))
    draw.text((11, 30), "a place for friends", fill=WHITE, font=tag_font)

    out = os.path.join(ASSETS, "logo.gif")
    img.convert("P", palette=Image.ADAPTIVE, colors=16).save(out, "GIF", optimize=True)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


def make_default_avatar():
    w, h = 160, 160
    img = Image.new("RGB", (w, h), GREY_BG)
    draw = ImageDraw.Draw(img)
    draw.ellipse([55, 25, 105, 75], fill=GREY_FG)
    draw.ellipse([15, 90, 145, 200], fill=GREY_FG)
    draw.rectangle([0, 0, w - 1, h - 1], outline=COBALT)
    out = os.path.join(ASSETS, "avatar_default.gif")
    img.convert("P", palette=Image.ADAPTIVE, colors=8).save(out, "GIF", optimize=True)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


def make_online_bolt():
    w, h = 12, 12
    img = Image.new("RGB", (w, h), PALE_YELLOW)
    draw = ImageDraw.Draw(img)
    bolt = [(7, 0), (2, 6), (5, 6), (3, 11), (10, 4), (7, 4)]
    draw.polygon(bolt, fill=YELLOW, outline=(204, 102, 0))
    out = os.path.join(ASSETS, "online_bolt.gif")
    img.convert("P", palette=Image.ADAPTIVE, colors=4).save(out, "GIF", optimize=True)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


# ----------------------------------------------------------------------------
# per-seed-user procedural portraits
# ----------------------------------------------------------------------------

def _checker_bg(draw, w, h, c1, c2, size=8):
    for y in range(0, h, size):
        for x in range(0, w, size):
            on = ((x // size) + (y // size)) % 2 == 0
            draw.rectangle([x, y, x + size - 1, y + size - 1], fill=(c1 if on else c2))


def _gradient_bg(img, top, bot):
    w, h = img.size
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] * (1 - t) + bot[0] * t)
        g = int(top[1] * (1 - t) + bot[1] * t)
        b = int(top[2] * (1 - t) + bot[2] * t)
        for x in range(w):
            px[x, y] = (r, g, b)


def _draw_face(draw, theme):
    """Draw the head + neck + shoulders silhouette in the user's skin tone."""
    skin = theme["skin"]
    # neck
    draw.rectangle([66, 105, 94, 130], fill=skin, outline=(50, 30, 20))
    # shoulders / torso
    shirt = theme.get("shirt", (60, 60, 80))
    draw.polygon(
        [(20, 160), (40, 130), (70, 122), (90, 122), (120, 130), (140, 160), (140, 200), (20, 200)],
        fill=shirt,
        outline=(20, 20, 30),
    )
    # head
    draw.ellipse([45, 25, 115, 110], fill=skin, outline=(50, 30, 20))


def _draw_eyes(draw, theme, x_off=0):
    eye = theme.get("eye", BLACK)
    draw.ellipse([60 + x_off, 65, 70 + x_off, 75], fill=eye)
    draw.ellipse([90 + x_off, 65, 100 + x_off, 75], fill=eye)
    # tiny highlight
    draw.point([(63 + x_off, 67), (93 + x_off, 67)], fill=WHITE)


def _draw_mouth(draw, theme):
    style = theme.get("mouth", "neutral")
    color = theme.get("lip", (140, 60, 60))
    if style == "smile":
        draw.arc([66, 80, 94, 100], 0, 180, fill=color, width=3)
    elif style == "frown":
        draw.arc([66, 90, 94, 110], 180, 360, fill=color, width=2)
    elif style == "smirk":
        draw.line([(70, 90), (88, 88)], fill=color, width=2)
    elif style == "lipstick":
        draw.ellipse([68, 86, 92, 96], fill=color, outline=(80, 20, 20))
    else:
        draw.line([(70, 90), (90, 90)], fill=color, width=2)


def _draw_hair(draw, theme):
    color = theme["hair"]
    style = theme.get("hairstyle", "short")
    if style == "short":
        draw.pieslice([40, 20, 120, 100], 200, 340, fill=color)
        draw.rectangle([40, 50, 120, 60], fill=color)
    elif style == "spiky":
        draw.pieslice([40, 20, 120, 100], 200, 340, fill=color)
        for x in range(40, 121, 8):
            draw.polygon([(x, 30), (x + 4, 12), (x + 8, 30)], fill=color)
    elif style == "long":
        draw.pieslice([40, 20, 120, 100], 200, 340, fill=color)
        draw.rectangle([42, 50, 56, 130], fill=color)
        draw.rectangle([104, 50, 118, 130], fill=color)
    elif style == "mohawk":
        draw.pieslice([40, 20, 120, 100], 200, 340, fill=(40, 40, 40))
        for x in range(74, 87, 2):
            draw.line([(x, 5), (x, 50)], fill=color, width=1)
    elif style == "bald":
        # subtle dome highlight, no hair
        pass
    elif style == "pigtails":
        draw.pieslice([40, 20, 120, 100], 200, 340, fill=color)
        draw.ellipse([28, 60, 56, 105], fill=color)
        draw.ellipse([104, 60, 132, 105], fill=color)
    elif style == "bowl":
        draw.pieslice([35, 18, 125, 90], 180, 360, fill=color)


def _draw_accessory(draw, theme):
    acc = theme.get("accessory")
    if acc == "sunglasses":
        draw.rectangle([56, 62, 76, 78], fill=BLACK, outline=BLACK)
        draw.rectangle([84, 62, 104, 78], fill=BLACK, outline=BLACK)
        draw.line([(76, 70), (84, 70)], fill=BLACK, width=2)
    elif acc == "glasses":
        draw.ellipse([54, 60, 76, 78], outline=(60, 40, 30), width=2)
        draw.ellipse([84, 60, 106, 78], outline=(60, 40, 30), width=2)
        draw.line([(76, 70), (84, 70)], fill=(60, 40, 30), width=2)
    elif acc == "ska_hat":
        # pork pie hat
        draw.rectangle([42, 35, 118, 50], fill=BLACK)
        draw.ellipse([38, 28, 122, 42], fill=BLACK)
        draw.rectangle([42, 45, 118, 50], fill=(180, 180, 180))
    elif acc == "cap":
        draw.pieslice([35, 25, 125, 70], 180, 360, fill=theme.get("cap_color", (255, 100, 0)))
        draw.ellipse([20, 40, 80, 70], fill=theme.get("cap_color", (255, 100, 0)))  # brim
    elif acc == "headphones":
        draw.arc([35, 35, 125, 95], 180, 360, fill=BLACK, width=4)
        draw.ellipse([32, 60, 50, 86], fill=BLACK)
        draw.ellipse([110, 60, 128, 86], fill=BLACK)
    elif acc == "earrings":
        draw.ellipse([47, 78, 53, 84], fill=YELLOW, outline=(150, 100, 0))
        draw.ellipse([107, 78, 113, 84], fill=YELLOW, outline=(150, 100, 0))


def _draw_makeup(draw, theme):
    makeup = theme.get("makeup")
    if makeup == "goth":
        # heavy eyeliner
        draw.line([(56, 65), (72, 65)], fill=BLACK, width=2)
        draw.line([(88, 65), (104, 65)], fill=BLACK, width=2)
        draw.line([(56, 80), (72, 80)], fill=BLACK, width=1)
        draw.line([(88, 80), (104, 80)], fill=BLACK, width=1)
    elif makeup == "glitter":
        # small dots around eyes
        for x in range(50, 110, 6):
            draw.point([(x, 58), (x + 2, 56)], fill=YELLOW)


def _draw_overlay(draw, theme):
    overlay = theme.get("overlay")
    if overlay == "sparkle":
        for (x, y) in [(20, 20), (140, 30), (10, 100), (145, 120), (30, 145), (130, 145)]:
            draw.line([(x - 3, y), (x + 3, y)], fill=WHITE, width=1)
            draw.line([(x, y - 3), (x, y + 3)], fill=WHITE, width=1)
    elif overlay == "matrix":
        # vertical green digit rain
        for col in range(0, 160, 16):
            for row in range(0, 160, 14):
                if random.random() < 0.4:
                    draw.text((col, row), random.choice("01"), fill=(0, 200, 0), font=_font(10))
    elif overlay == "scanlines":
        for y in range(0, 160, 3):
            draw.line([(0, y), (160, y)], fill=(0, 0, 0, 0))
            # we're RGB so emulate via dark line
            draw.line([(0, y), (160, y)], fill=(0, 30, 0))


# personality-driven themes; comments on each describe the look
USER_THEMES = {
    "tommy": {
        "bg_kind": "checker", "bg1": (40, 40, 40), "bg2": WHITE,
        "skin": (244, 200, 154), "hair": (90, 60, 32), "hairstyle": "short",
        "accessory": "ska_hat", "shirt": (220, 80, 60), "mouth": "smirk",
    },
    "sk8rboi": {
        "bg_kind": "gradient", "bg1": (255, 140, 0), "bg2": (255, 100, 0),
        "skin": (255, 224, 179), "hair": (255, 245, 179), "hairstyle": "spiky",
        "accessory": "cap", "cap_color": (200, 30, 30),
        "shirt": (40, 40, 40), "mouth": "smirk",
    },
    "xXnightXx": {
        "bg_kind": "solid", "bg1": (10, 10, 18),
        "skin": (220, 200, 220), "hair": (20, 20, 30), "hairstyle": "long",
        "accessory": None, "makeup": "goth",
        "shirt": (10, 10, 10), "mouth": "frown", "lip": (150, 30, 60),
        "eye": (80, 0, 0),
    },
    "glitterbug": {
        "bg_kind": "gradient", "bg1": (255, 192, 220), "bg2": (255, 220, 240),
        "skin": (252, 220, 200), "hair": (240, 100, 180), "hairstyle": "long",
        "accessory": "earrings", "makeup": "glitter", "overlay": "sparkle",
        "shirt": (255, 100, 180), "mouth": "smile", "lip": (220, 60, 130),
    },
    "2cool4u": {
        "bg_kind": "solid", "bg1": (60, 60, 70),
        "skin": (250, 220, 180), "hair": (50, 30, 20), "hairstyle": "short",
        "accessory": "sunglasses",
        "shirt": (30, 30, 30), "mouth": "frown",
    },
    "valerie_v": {
        "bg_kind": "gradient", "bg1": (180, 30, 30), "bg2": (120, 10, 10),
        "skin": (244, 210, 174), "hair": (60, 30, 20), "hairstyle": "bowl",
        "accessory": None, "shirt": (220, 220, 220), "mouth": "smile",
        "lip": (200, 30, 60),
    },
    "dial_up_dan": {
        "bg_kind": "solid", "bg1": (20, 80, 20),
        "skin": (240, 215, 180), "hair": (140, 100, 60), "hairstyle": "bald",
        "accessory": "glasses", "shirt": (60, 80, 100), "mouth": "smile",
        "overlay": "matrix",
    },
    "mod_mandy": {
        "bg_kind": "gradient", "bg1": (200, 220, 240), "bg2": (170, 200, 230),
        "skin": (250, 224, 192), "hair": (110, 70, 30), "hairstyle": "bowl",
        "accessory": "glasses", "shirt": (40, 80, 140), "mouth": "neutral",
    },
    "y2k_survivor": {
        "bg_kind": "checker", "bg1": (255, 220, 0), "bg2": (255, 240, 80),
        "skin": (252, 220, 188), "hair": (200, 150, 60), "hairstyle": "short",
        "accessory": "headphones", "shirt": (40, 40, 200), "mouth": "smirk",
    },
    "radioheadz": {
        "bg_kind": "gradient", "bg1": (60, 60, 70), "bg2": (110, 110, 120),
        "skin": (220, 200, 188), "hair": (40, 40, 50), "hairstyle": "short",
        "accessory": "headphones", "shirt": (50, 50, 60), "mouth": "frown",
    },
    "neopet_luv": {
        "bg_kind": "gradient", "bg1": (255, 220, 60), "bg2": (255, 180, 220),
        "skin": (252, 220, 190), "hair": (255, 100, 100), "hairstyle": "pigtails",
        "accessory": None, "shirt": (255, 80, 140), "mouth": "smile",
        "overlay": "sparkle",
    },
    "nokia_3310": {
        "bg_kind": "solid", "bg1": (180, 220, 180),
        "skin": (240, 215, 180), "hair": (60, 40, 30), "hairstyle": "short",
        "accessory": "glasses", "shirt": (60, 100, 140), "mouth": "neutral",
    },
    # tom_cyspace intentionally absent from this dict: the avatar is not
    # procedurally generated.  release_files/src/assets/avatars/tom_cyspace.gif
    # is sourced from the real CyberSCI founder photo (resized to 160x160).
    # Re-running this script must not clobber it.
}


def make_user_avatar(username, theme):
    w, h = 160, 160
    img = Image.new("RGB", (w, h), theme["bg1"])
    draw = ImageDraw.Draw(img)

    kind = theme.get("bg_kind", "solid")
    if kind == "checker":
        _checker_bg(draw, w, h, theme["bg1"], theme["bg2"])
    elif kind == "gradient":
        _gradient_bg(img, theme["bg1"], theme["bg2"])
        draw = ImageDraw.Draw(img)

    # 4-pixel border
    draw.rectangle([0, 0, w - 1, h - 1], outline=COBALT)
    draw.rectangle([1, 1, w - 2, h - 2], outline=WHITE)

    _draw_face(draw, theme)
    _draw_hair(draw, theme)
    _draw_eyes(draw, theme)
    _draw_makeup(draw, theme)
    _draw_mouth(draw, theme)
    _draw_accessory(draw, theme)
    _draw_overlay(draw, theme)

    out_dir = os.path.join(ASSETS, "avatars")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{username}.gif")
    img.convert("P", palette=Image.ADAPTIVE, colors=64).save(out, "GIF", optimize=True)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


def make_all_avatars():
    for username, theme in USER_THEMES.items():
        random.seed(hash(username) & 0xFFFFFFFF)
        make_user_avatar(username, theme)


# ----------------------------------------------------------------------------
# mood emoji (Yahoo-IM-style 16x16 round faces)
# ----------------------------------------------------------------------------

# (face_color, eye_color, mouth_kind, accent)
MOODS = {
    "rockin":    ((255, 200, 60),  BLACK, "open",     "tongue"),
    "melancholy":((180, 200, 220), BLACK, "frown",    None),
    "bored":     ((220, 220, 100), BLACK, "flat",     "halflid"),
    "sparkly":   ((255, 180, 220), BLACK, "smile",    "sparkle"),
    "annoyed":   ((255, 140, 80),  BLACK, "frown",    "brow"),
    "proud":     ((255, 220, 60),  BLACK, "smile",    "sparkle"),
    "hopeful":   ((255, 240, 120), BLACK, "smile",    None),
    "busy":      ((220, 220, 220), BLACK, "flat",     "sweat"),
    "smug":      ((255, 220, 80),  BLACK, "smirk",    None),
    "paranoid":  ((180, 220, 180), BLACK, "frown",    "wide_eyes"),
    "worried":   ((220, 240, 180), BLACK, "wobble",   None),
    "chill":     ((140, 200, 220), BLACK, "smile",    "shades"),
    "default":   ((255, 220, 60),  BLACK, "flat",     None),
}


def make_mood(name, spec):
    face_color, eye_color, mouth_kind, accent = spec
    w, h = 16, 16
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # round head
    draw.ellipse([1, 1, 14, 14], fill=face_color, outline=BLACK)

    # eyes
    if accent == "wide_eyes":
        draw.ellipse([4, 5, 7, 9], fill=WHITE, outline=BLACK)
        draw.ellipse([8, 5, 11, 9], fill=WHITE, outline=BLACK)
        draw.point([(5, 7), (9, 7)], fill=BLACK)
    elif accent == "halflid":
        draw.line([(4, 7), (6, 7)], fill=eye_color, width=1)
        draw.line([(9, 7), (11, 7)], fill=eye_color, width=1)
    elif accent == "shades":
        draw.rectangle([3, 6, 7, 9], fill=BLACK)
        draw.rectangle([8, 6, 12, 9], fill=BLACK)
        draw.line([(7, 7), (8, 7)], fill=BLACK, width=1)
    else:
        draw.point([(5, 6), (5, 7)], fill=eye_color)
        draw.point([(10, 6), (10, 7)], fill=eye_color)

    # mouth
    if mouth_kind == "smile":
        draw.arc([5, 7, 10, 12], 0, 180, fill=BLACK, width=1)
    elif mouth_kind == "frown":
        draw.arc([5, 9, 10, 14], 180, 360, fill=BLACK, width=1)
    elif mouth_kind == "smirk":
        draw.line([(5, 11), (9, 10)], fill=BLACK, width=1)
    elif mouth_kind == "open":
        draw.ellipse([6, 9, 9, 12], fill=BLACK)
    elif mouth_kind == "wobble":
        draw.line([(5, 11), (7, 10), (9, 11), (11, 10)], fill=BLACK)
    else:  # flat
        draw.line([(5, 11), (10, 11)], fill=BLACK, width=1)

    # accent overlays
    if accent == "tongue":
        draw.rectangle([7, 11, 9, 13], fill=(220, 60, 60), outline=BLACK)
    elif accent == "sparkle":
        for (x, y) in [(2, 3), (13, 4), (2, 12), (13, 11)]:
            draw.point([(x, y), (x + 1, y), (x, y + 1)], fill=YELLOW)
    elif accent == "brow":
        draw.line([(3, 4), (6, 5)], fill=BLACK, width=1)
        draw.line([(9, 5), (12, 4)], fill=BLACK, width=1)
    elif accent == "sweat":
        draw.ellipse([12, 4, 14, 7], fill=(120, 200, 240), outline=(60, 100, 160))

    out_dir = os.path.join(ASSETS, "moods")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{name}.gif")
    img.convert("P", palette=Image.ADAPTIVE, colors=8).save(out, "GIF", optimize=True)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


def make_all_moods():
    for name, spec in MOODS.items():
        make_mood(name, spec)


# ----------------------------------------------------------------------------
# animated glitter GIFs
# ----------------------------------------------------------------------------

def make_glitter_star():
    w, h = 16, 16
    frames = []
    for f in range(4):
        img = Image.new("RGB", (w, h), (255, 192, 220))
        draw = ImageDraw.Draw(img)
        # rotating sparkle
        cx, cy = 8, 8
        size = 6 - f
        # outer star
        outer = (255, 255, 100)
        for angle in range(0, 360, 90):
            rad = math.radians(angle + f * 22)
            x = cx + int(math.cos(rad) * size)
            y = cy + int(math.sin(rad) * size)
            draw.line([(cx, cy), (x, y)], fill=outer, width=2)
        # diagonal arms
        for angle in range(45, 360, 90):
            rad = math.radians(angle + f * 22)
            x = cx + int(math.cos(rad) * (size - 2))
            y = cy + int(math.sin(rad) * (size - 2))
            draw.line([(cx, cy), (x, y)], fill=(255, 255, 200), width=1)
        draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=WHITE)
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=8))
    out_dir = os.path.join(ASSETS, "glitter")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "star.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=120,
                   loop=0, optimize=True, disposal=2, transparency=0)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


def make_glitter_friends():
    w, h = 140, 16
    frames = []
    text = "FRIENDS 4 LIFE"
    f0 = _font(12)
    palette = [(255, 60, 160), (255, 120, 60), (255, 200, 30), (140, 60, 220)]
    for f in range(len(palette)):
        img = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((4, 1), text, fill=palette[f], font=f0)
        # sparkle dots
        for i in range(6):
            sx = (f * 7 + i * 22) % w
            draw.point([(sx, 2), (sx + 1, 1), (sx, 3), (sx - 1, 2)], fill=WHITE)
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=16))
    out_dir = os.path.join(ASSETS, "glitter")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "friends.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=200,
                   loop=0, optimize=True, disposal=2)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


def make_glitter_flame():
    w, h = 16, 20
    frames = []
    for f in range(4):
        img = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        # outer red flame body — shifts slightly per frame
        sway = (-1 if f % 2 == 0 else 1) * (1 if f < 2 else 2)
        outer = [
            (8, 19), (3 + sway, 14), (5, 8), (2 + sway, 4),
            (6, 6), (8, 0), (10, 6), (14 - sway, 4),
            (11, 8), (13 - sway, 14),
        ]
        draw.polygon(outer, fill=(220, 40, 30))
        inner = [
            (8, 18), (5 + sway, 14), (7, 9), (5 + sway, 6),
            (8, 8), (8, 3), (10 - sway, 8), (11, 6),
            (10, 9), (12 - sway, 14),
        ]
        draw.polygon(inner, fill=(255, 180, 30))
        # tiny white-yellow core
        draw.polygon([(8, 14), (7, 11), (8, 8), (9, 11)], fill=(255, 255, 200))
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=8))
    out_dir = os.path.join(ASSETS, "glitter")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "flame.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=100,
                   loop=0, optimize=True, disposal=2, transparency=0)
    print(f"  wrote {out} ({os.path.getsize(out)} bytes)")


# ----------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Generating CySpace assets into {os.path.realpath(ASSETS)}")
    os.makedirs(ASSETS, exist_ok=True)
    make_logo()
    make_default_avatar()
    make_online_bolt()
    print("--- per-user avatars ---")
    make_all_avatars()
    print("--- mood emoji ---")
    make_all_moods()
    print("--- glitter ---")
    make_glitter_star()
    make_glitter_friends()
    make_glitter_flame()
    total = 0
    for root, _, files in os.walk(ASSETS):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    print(f"done. total assets on disk: {total} bytes")
