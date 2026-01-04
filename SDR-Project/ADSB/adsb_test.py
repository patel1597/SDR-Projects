import numpy as np                      # imports the library to do array math
import matplotlib.pyplot as plt         # imports the library to graph and visualize
from rtlsdr import RtlSdr               # imports RTL-SDR radio control class which lets us talk to the RTL-SDR hardware

ADSB_FREQ = 1090e6 # 1090 MHz is the ADS-B frequency
SAMPLE_RATE = 2e6 # sample rate
GAIN = 49.6 # maximum gain for weak signals 

print(f"\nConfiguring RTL-SDR:")
print(f"Frequency: {ADSB_FREQ/1e6} MHz")
print(f"Sample Rate: {SAMPLE_RATE/1e6} MS/s")
print(f"Gain: {GAIN} dB")

sdr = RtlSdr() # creating the RTL-SDR object
sdr.sample_rate = SAMPLE_RATE # what the RTL should sample at
sdr.center_freq = ADSB_FREQ # what frequency it should tune into
sdr.gain = GAIN # amplifier gain

print("\nCapturing data...")
samples = sdr.read_samples(256*1024) # read the samples (complex), changed due to overflow error, FFT works best with powers of 2
sdr.close() # disconnect from the SDR

print(f"Captured {len(samples):,} samples")

print("\nAnalyzing signal...")
fft = np.fft.fftshift(np.fft.fft(samples)) # converts time domain into frequency domain using fast fourier transform, and uses the shift the frequency to center 
freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/SAMPLE_RATE)) # generates the frequency values for each FFT and shifts them to the center
power_db = 20 * np.log10(np.abs(fft) + 1e-10) # finding the power in dB

magnitude = np.abs(samples) # the magnitude so only caring about signal strength
max_signal = np.max(magnitude) # finding the maximum magnitude
mean_signal = np.mean(magnitude) # average of the magnitude, to represent the noise floor

print(f"\nSignal Statistics:")
print(f"Max amplitude: {max_signal:.4f}")
print(f"Mean amplitude: {mean_signal:.4f}")
print(f"Peak-to-mean ratio: {max_signal/mean_signal:.2f}x")

# if the ratio is above 3 we have strong signals
if max_signal/mean_signal > 3:
    print(f"\nSeeing strong pulses!")
else:
    print(f"\nSignals look weak. Move closer to the window")

# plot the spectrum so it is readable
plt.figure(figsize=(14, 8))

# subplot 1: Spectrum
plt.subplot(2, 1, 1)
plt.plot(freqs/1e6, power_db, linewidth=0.5) # Hz to MHz, and plotting the power in dB
plt.xlabel('Frequency Offset (MHz)')
plt.ylabel('Power (dB)')
plt.title('ADS-B Signal Spectrum at 1090 MHz')
plt.grid(True, alpha=0.3)

# subplot 2: Time domain (first 10,000 samples)
plt.subplot(2, 1, 2)
time_samples = magnitude[:10000]
plt.plot(time_samples, linewidth=0.5) # plotting the magnitude of the first 10000 samples
plt.xlabel('Sample')
plt.ylabel('Magnitude')
plt.title('Time Domain - Looking for ADS-B Pulses')
plt.grid(True, alpha=0.3)

# adjust spacing and show us the plots
plt.tight_layout()
plt.show()
