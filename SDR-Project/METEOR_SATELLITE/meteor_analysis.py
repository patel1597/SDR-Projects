import numpy as np
import matplotlib.pyplot as plt

# 1. SETTINGS
filename = 'meteor_doppler_20260101_145021.iq'  # Change this to your actual file name
fs = 1.0e6                     # Sample rate

# 2. LOAD DATA
# Read the raw bytes and turn them into numbers
data = np.fromfile(filename, dtype=np.uint8)

# Convert 8-bit bytes to complex numbers (I + jQ)
# We subtract 127.5 to center the signal at zero
i = (data[0::2].astype(np.float32) - 127.5) / 127.5
q = (data[1::2].astype(np.float32) - 127.5) / 127.5
iq_signal = i + 1j * q

# 3. PLOT RESULTS
plt.figure(figsize=(12, 5))

# Plot Waterfall (Left Side)
plt.subplot(1, 2, 1)
plt.specgram(iq_signal[:1000000], NFFT=1024, Fs=fs, cmap='magma')
plt.title("Frequency (Waterfall)")
plt.xlabel("Freq (Hz)")
plt.ylabel("Time (s)")

# Plot Constellation (Right Side)
plt.subplot(1, 2, 2)
plt.scatter(i[:20000], q[:20000], s=1, alpha=0.5)
plt.title("Phase (Constellation)")
plt.xlabel("I")
plt.ylabel("Q")
plt.axis('equal')

plt.tight_layout()
plt.show()