import numpy as np                      # imports the library to do array math
import matplotlib.pyplot as plt         # imports the library to graph and visualize
from rtlsdr import RtlSdr               # imports RTL-SDR radio control class which lets us talk to the RTL-SDR hardware
from scipy.signal import find_peaks     # import peak-finding function from SciPy, automatically detect stations 

# create RTL-SDR object - represents the physical RTL-SDR dongle
sdr = RtlSdr()

# configure SDR
sample_rate = 2.4e6  # 2.4 MHz - this is the sample rate by how fast the data is captured - limitation
center_freq = 96e6  # change to any frequency you want center at

# configuring the hardware what frequency to tune into and how fast to sample
sdr.sample_rate = sample_rate
sdr.center_freq = center_freq

sdr.gain = 40 # amplifies weak signals (but really not needed as these waves are near me)

# printing messages to let us know the settings and when it will start to capture the samples 
print("\nRTL-SDR Connected!")                         
print(f"Center Frequency: {center_freq/1e6} MHz")
print(f"Sample Rate: {sample_rate/1e6} MHz")
print(f"Gain: {sdr.gain} dB")
print("\nCapturing RF data...")

# capture samples
samples = sdr.read_samples(1024*1024) # Capture 1,048,576 samples from RTL-SDR, get lots of data for good spectrum resolution, the output is complex array
sdr.close() # close connection to the RTL-SDR

print(f"Captured {len(samples)} samples!") # printing how many samples captured 

# compute FFT with averaging to reduce noise
# divide samples into chunks of 8192
chunk_size = 8192
num_chunks = len(samples) // chunk_size
fft_avg = np.zeros(chunk_size) # create array of zeros, size 8192, later will store the averaged FFT result

# loop through each chunk
for i in range(num_chunks):
    chunk = samples[i*chunk_size:(i+1)*chunk_size] # process one chunk at a time
    fft_chunk = np.abs(np.fft.fftshift(np.fft.fft(chunk))) # frequency spectrum of this chunk, by taking the fast fourier transform, making sure 0 Hz is in the center, lastly taking the absolute value to get the magnitude instead of the phase 
    fft_avg += fft_chunk # add all of these chunks to get the overall FFT avg

fft_avg = fft_avg / num_chunks # divide by number of chunks, to get the avg
fft_power = 20 * np.log10(fft_avg) # converting to decibels

# frequency axis
freqs = np.linspace(-sample_rate/2, sample_rate/2, chunk_size) # make evenly spaced array, with proper frequency range by matching with the FFT output size
freqs_mhz = (freqs + center_freq) / 1e6 # add center frequency, convert Hz to MHz

# plot
plt.figure(figsize=(14, 7)) # creating the figure window
plt.plot(freqs_mhz, fft_power, linewidth=1, color='blue') # x-axis, y-axis, line thickness, and color
# label the axes and title
plt.xlabel('Frequency (MHz)', fontsize=14, fontweight='bold')
plt.ylabel('Power (dB)', fontsize=14, fontweight='bold')
plt.title('RF Spectrum', fontsize=16, fontweight='bold')
# add grid lines that are dashed
plt.grid(True, alpha=0.5, linestyle='--')
# adding axes limits to see the graph properly
plt.xlim([88, 108])
plt.ylim([np.min(fft_power), np.max(fft_power) + 5])

# find peaks
# must be 8 dB above average
# peaks must be 20 points apart
# must stand out by 3 dB
peaks, properties = find_peaks(fft_power, 
                                height=np.mean(fft_power) + 8,
                                distance=20,
                                prominence=3)

# if any peaks found
if len(peaks) > 0:
    print(f"\nFOUND {len(peaks)} FM STATIONS!")
    print("\nTop 10 or less stations:")
    
    # sort by power
    peak_powers = fft_power[peaks] # get power at each peak
    sorted_indices = np.argsort(peak_powers)[::-1]  # get indices that would sort array in descending order
    
    # printing the top 10 and formatting to certain decimal places
    for i, idx in enumerate(sorted_indices[:10]):
        peak = peaks[idx]
        freq = freqs_mhz[peak]
        power = fft_power[peak]
        print(f"Station {i+1}: {freq:.2f} MHz at {power:.1f} dB")
    
    # mark all peaks on plot, legend included
    plt.plot(freqs_mhz[peaks], fft_power[peaks], 
             "x", color='red', markersize=8, 
             markeredgewidth=2, label=f'{len(peaks)} Detected Stations')
    plt.legend(fontsize=12)
else:
    print("\nNo stations detected")

# finding SNR - tells us how much stronger the signal is from the noise
# sorts from low to high (weak to strong)
sorted_power = np.sort(fft_power)

# The average background noise level, when there's no signal, this is what you measure, everything above this is actual signal, choosing the lowest 20 percent -- int
noise_floor = np.mean(sorted_power[:int(len(sorted_power) * 0.2)])

print(f"\nNoise floor: {noise_floor:.1f} dB")

if len(peaks) > 0:
    print(f"\nFOUND {len(peaks)} FM STATIONS (with SNR):")
    print("\nTop 10 Stations or less stations:")
    
    for i, idx in enumerate(sorted_indices[:10]):
        peak = peaks[idx] # Index in frequency array
        freq = freqs_mhz[peak] # frequency in MHz
        power = fft_power[peak] # power in dB
        snr = power - noise_floor  # subtracts(dB) noise floor from signal power: result is Signal-to-Noise Ratio (SNR), subtraction is division in dB
        print(f"Station {i+1}: {freq:.2f} MHz at {power:.1f} dB (SNR: {snr:.1f} dB)")

plt.tight_layout()
plt.show() # display the plot

