"""
generate_audio.py - produce aol_connection.wav for the AOL challenge.

The output is an 8000 Hz mono WAV that sounds like a real dial-up handshake.
Inside seconds 4–8, the flag text is silently encoded into the spectrogram
using per-column sine-wave injection at pixel-mapped frequencies.

Dependencies: numpy, scipy, Pillow
    pip install numpy scipy pillow
Usage:
    python generate_audio.py
"""

import os
import struct
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as sig
from PIL import Image, ImageDraw, ImageFont

FLAG        = "cybersci{d14l-up-4nd-tun3-1n-241316}"
SAMPLE_RATE = 8000
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../release_files/aol_connection.wav")

# ---------------------------------------------------------------------------
# 1. Build a realistic dial-up tone sequence
# ---------------------------------------------------------------------------

def tone(freq, duration, sr=SAMPLE_RATE, amp=0.4):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)

def silence(duration, sr=SAMPLE_RATE):
    return np.zeros(int(sr * duration), dtype=np.float32)

def dtmf(row_freq, col_freq, duration=0.08, sr=SAMPLE_RATE, amp=0.35):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return (amp * (np.sin(2 * np.pi * row_freq * t) +
                   np.sin(2 * np.pi * col_freq * t))).astype(np.float32)

def noise(duration, sr=SAMPLE_RATE, amp=0.04):
    return (amp * np.random.randn(int(sr * duration))).astype(np.float32)

def fsk_burst(duration, f0=1070, f1=1270, baud=300, sr=SAMPLE_RATE, amp=0.3):
    """Simple FSK-like burst simulating modem negotiation tones."""
    n = int(sr * duration)
    t = np.arange(n) / sr
    bits = np.random.randint(0, 2, int(duration * baud) + 1)
    samples_per_bit = sr / baud
    freqs = np.array([f0 if bits[int(i / samples_per_bit)] == 0 else f1
                      for i in range(n)])
    phase = np.cumsum(2 * np.pi * freqs / sr)
    return (amp * np.sin(phase)).astype(np.float32)

def build_dialup_audio():
    """Assemble ~10 seconds of dial-up handshake audio."""
    parts = []

    # Dial tone (350 + 440 Hz)
    parts.append(tone(350, 0.5) + tone(440, 0.5))

    # DTMF digits for a fake phone number
    dtmf_pairs = [
        (697, 1209), (697, 1336), (697, 1477),  # 1, 2, 3
        (770, 1209), (770, 1336),                # 4, 5
    ]
    for r, c in dtmf_pairs:
        parts.append(dtmf(r, c))
        parts.append(silence(0.05))

    # Ringing tone (silence between)
    for _ in range(2):
        parts.append(tone(440, 0.4) + tone(480, 0.4))
        parts.append(silence(0.3))

    # Answer: 2100 Hz CED (calling tone)
    parts.append(tone(2100, 0.8, amp=0.5))
    parts.append(silence(0.1))

    # V.8 CI tone + ANSam squeal (approximated)
    parts.append(tone(1300, 0.5, amp=0.45))
    parts.append(fsk_burst(0.6, f0=1070, f1=1270))
    parts.append(fsk_burst(0.6, f0=2025, f1=2225))

    # Negotiation / training (mixed FSK + noise)
    for _ in range(4):
        parts.append(fsk_burst(0.4, f0=1200, f1=2400, baud=1200))
        parts.append(noise(0.05))

    # "CONNECT" handshake silence then steady carrier
    parts.append(silence(0.2))
    parts.append(fsk_burst(1.0, f0=1650, f1=1850, baud=2400, amp=0.25))

    audio = np.concatenate(parts)

    # Pad or trim to exactly 10 seconds
    target = SAMPLE_RATE * 10
    if len(audio) < target:
        audio = np.concatenate([audio, silence((target - len(audio)) / SAMPLE_RATE)])
    else:
        audio = audio[:target]

    return audio

# ---------------------------------------------------------------------------
# 2. Render flag text as a bitmap for spectrogram injection
# ---------------------------------------------------------------------------

def render_flag_bitmap(text, width_px=500, height_px=28):
    """
    Render text to a binary bitmap (black=0, white=1).
    Width = number of spectrogram time frames; height = number of freq bins.
    Both must match the solver's nperseg/noverlap settings exactly.
    """
    img = Image.new("L", (width_px, height_px), 0)
    draw = ImageDraw.Draw(img)

    for path in [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Courier New.ttf",
        "/Library/Fonts/Courier New Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, 24)
            break
        except Exception:
            font = None

    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    content_h = bbox[3] - bbox[1]          # visible content height (excl. leading)
    x = max(0, (width_px - tw) // 2)
    # Centre by VISIBLE content so descenders (underscores) aren't clipped
    y = (height_px - content_h) // 2 - bbox[1]
    draw.text((x, y), text, fill=255, font=font)

    arr = np.array(img, dtype=np.float32) / 255.0  # shape (height, width)
    return arr

# ---------------------------------------------------------------------------
# 3. Inject the flag into seconds 4–8 via spectrogram pixel synthesis
# ---------------------------------------------------------------------------

STEGO_START   = 4.0    # seconds
STEGO_END     = 8.0    # seconds
# Frequencies must be exact integer multiples of SR/STEGO_NPERSEG (= 125 Hz)
# so injected tones fall exactly on FFT bin centres → zero spectral leakage.
STEGO_NPERSEG = 64     # must match solve.py
BIN_HZ        = SAMPLE_RATE / STEGO_NPERSEG   # 125 Hz per bin
FREQ_LOW      = 2  * BIN_HZ   # bin 2  = 250 Hz
FREQ_HIGH     = 29 * BIN_HZ   # bin 29 = 3625 Hz (exclusive upper bound)
STEGO_AMP     = 0.05   # per-tone amplitude; max 18 simultaneous → peak ≤ 0.90 < 1.0 (no clipping)

def inject_spectrogram_flag(audio, bitmap):
    """
    Each bitmap column is injected for exactly STEGO_NPERSEG samples so that
    the spectrogram (nperseg=STEGO_NPERSEG, noverlap=0, window='boxcar') sees
    one clean FFT frame per column.  Frequencies are bin-aligned → zero leakage.
    """
    start_sample = int(STEGO_START * SAMPLE_RATE)
    end_sample   = int(STEGO_END   * SAMPLE_RATE)

    height, width = bitmap.shape
    col_samples  = STEGO_NPERSEG          # one FFT window per column
    freq_per_row = BIN_HZ                 # 125 Hz = exactly 1 bin per row

    stego_len = width * col_samples
    stego = np.zeros(stego_len, dtype=np.float32)

    for col in range(width):
        col_start = col * col_samples
        col_end   = col_start + col_samples
        t = np.arange(col_samples) / SAMPLE_RATE

        for row in range(height):
            intensity = bitmap[height - 1 - row, col]  # flip: row 0 → low freq
            if intensity > 0.5:
                freq = FREQ_LOW + row * freq_per_row
                stego[col_start:col_end] += STEGO_AMP * np.sin(2 * np.pi * freq * t)

    audio = audio.copy()
    # Silence the background during the stego window for clean contrast
    audio[start_sample:start_sample + stego_len] *= 0.01
    audio[start_sample:start_sample + stego_len] += stego
    return np.clip(audio, -1.0, 1.0)

# ---------------------------------------------------------------------------
# 4. Write WAV
# ---------------------------------------------------------------------------

def write_wav(path, audio, sr=SAMPLE_RATE):
    pcm = (audio * 32767).astype(np.int16)
    wavfile.write(path, sr, pcm)
    print(f"Written: {path}  ({len(pcm)/sr:.1f}s, {sr} Hz, mono 16-bit PCM)")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    np.random.seed(42)  # reproducible noise

    print("Building dial-up audio...")
    audio = build_dialup_audio()

    print("Rendering flag bitmap...")
    bitmap = render_flag_bitmap(FLAG)

    print("Injecting spectrogram flag into seconds 4–8...")
    audio = inject_spectrogram_flag(audio, bitmap)

    out = os.path.abspath(OUTPUT_PATH)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_wav(out, audio)
    print("Done. Verify with: open in Audacity → Spectrogram view, t=4–8s.")
