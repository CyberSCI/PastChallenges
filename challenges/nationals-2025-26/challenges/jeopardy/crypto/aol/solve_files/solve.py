"""
solve.py - AOL challenge solver

Plots the spectrogram of aol_connection.wav. The flag text is visible in
the frequency bands between seconds 4 and 8.

Dependencies: numpy, scipy, matplotlib
    pip install numpy scipy matplotlib
Usage:
    python solve.py 
"""
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as signal
import matplotlib.pyplot as plt

rate, data = wav.read("../release_files/aol_connection.wav")
data = data.astype(np.float32)

# Window size 64 + no overlap + rectangular window = zero spectral leakage
f, t, Sxx = signal.spectrogram(data, fs=rate, nperseg=64, noverlap=0, window='boxcar')
Sxx_db = 10 * np.log10(Sxx + 1e-20)

# Auto-scale to the stego window so background maps to black
t_mask = (t >= 4.0) & (t <= 8.0)
f_mask = (f >= 200) & (f <= 4000)
region = Sxx_db[np.ix_(f_mask, t_mask)]
vmin, vmax = np.percentile(region, 2), np.percentile(region, 98)

plt.figure(figsize=(24, 5))
plt.pcolormesh(t, f, Sxx_db, shading='nearest', cmap='hot', vmin=vmin, vmax=vmax)
plt.ylim(200, 3800)
plt.xlim(4.0, 8.0)
plt.xlabel("Time (s)")
plt.ylabel("Frequency (Hz)")
plt.tight_layout()
plt.show()