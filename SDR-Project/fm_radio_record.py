import numpy as np
from rtlsdr import RtlSdr
from scipy import signal
from scipy.io import wavfile # imports the WAV file writing functions

# configuration 
STATION_FREQ = 96.3e6      # from the spectrum found the strongest one - tune into this one (can change)
SAMPLE_RATE = 1.2e6        # FM station is 200 KHz wide - chose a sampling way above nyquist - can filter out the less important stuff later
AUDIO_RATE = 48000         # audio output - standard
GAIN = 35                  # gain in the middle (surrounding me, don't need too much gain)
DURATION = 10              # how long to record (can change)

print(f"\nTuning to: {STATION_FREQ/1e6:.1f} MHz")
print(f"Sample Rate: {SAMPLE_RATE/1e6} MHz")
print(f"Duration: {DURATION} seconds")

# SDR setup
sdr = RtlSdr() # creating the object
sdr.sample_rate = SAMPLE_RATE # how fast to capture the samples through the SDR
sdr.center_freq = STATION_FREQ # what frequency to tune into 
sdr.gain = GAIN # sets the amplifier gain

print("\nCapturing RF data...might take a while")
num_samples = int(SAMPLE_RATE * DURATION) # need the samples to be in int not float
samples = sdr.read_samples(num_samples) # capturing the RF data, this is complex numbers 
sdr.close() # disconnect from the SDR

print(f"Captured {len(samples):,} samples.")

# apply low-pass filter to isolate FM signal
print("\nFiltering RF signal...")
# FM stations are ~200 kHz wide
cutoff = 100e3  # 100 kHz cutoff
nyquist = SAMPLE_RATE / 2 # using the shannon theorem
normal_cutoff = cutoff / nyquist # normalizing the cutoff from 0 to 1 for filter use

# design low-pass filter (butterworth)
b, a = signal.butter(5, normal_cutoff, btype='low') # use 5 as the cutoff, not too sharp
samples_filtered = signal.filtfilt(b, a, samples) # use the filter design from above on the samples, removes phase shifts 

print("RF signal filtered")

# FM Demodulation
print("\nNow FM Demodulation...")

# polar discriminator method was better than simple diff
# below is code for the diff -- too much static ----
# phase = np.angle(samples)
# phase_unwrapped = np.unwrap(phase)
# audio = np.diff(phase_unwrapped)
# --------------------------------------------------

# the idea is simple: get all samples besides first
# get all samples besides the last
# multiply the current sample by the conjugate of the previous sample 
# since FM encodes audio in frequency and frequency is the derivative of phase (so rate of change in phase is frequency which is audio)
# the result is the phase difference therefore the frequency
y = samples_filtered[1:] * np.conj(samples_filtered[:-1])
audio_angle = np.angle(y) # extract the phase from complex numbers

print(f"Demodulated: {len(audio_angle):,} samples")

# de-emphasis filter (FM broadcast standard)
print("\nDe-emphasis filter...")
tau = 75e-6  # 75 microseconds (US FM standard)
d = SAMPLE_RATE * tau # the time constant in number of samples (seconds -> samples)
x = np.exp(-1/d) # calculate filter coefficient
# define filter coefficients for a first order IIR filter
b_deemph = [1 - x] 
a_deemph = [1, -x]
audio_deemph = signal.lfilter(b_deemph, a_deemph, audio_angle) # uses a linear filter function

# low-pass filter for audio (remove high-freq noise)
print("\nAudio filtering...")
audio_cutoff = 15000  # 15 kHz (human hearing limit)
audio_nyquist = SAMPLE_RATE / 2 # using the shannon theorem
audio_normal_cutoff = audio_cutoff / audio_nyquist # normalizing the cutoff from 0 to 1 for filter use

b_audio, a_audio = signal.butter(5, audio_normal_cutoff, btype='low') # use 5 as the cutoff, not too sharp
audio_filtered = signal.filtfilt(b_audio, a_audio, audio_deemph) # use the filter design from above on the audio, removes high frequency noise

# decimate/resample to audio rate, we sampled too high
print(f"Resampling to {AUDIO_RATE} Hz...")

# calculate decimation factor (how much to downsample)
decimation = int(SAMPLE_RATE / AUDIO_RATE)
if decimation > 1:
    # signal.decimate is a smart way to downsample the audio
    # it doesn't just throw away samples
    # applies anti-aliasing filter, then downsamples by factor, prevents aliasing
    # zero_phase set to true for no phase distortion 
    audio_decimated = signal.decimate(audio_filtered, decimation, zero_phase=True)
else:
    # if it is not an integer resample
    # uses FFT-based resampling
    audio_decimated = signal.resample(audio_filtered, int(len(audio_filtered) * AUDIO_RATE / SAMPLE_RATE))

print(f"Audio: {len(audio_decimated):,} samples at {AUDIO_RATE} Hz")

# Normalize
print("\nNormalizing volume...")

# remove DC offset so the audio averages to 0
audio_decimated = audio_decimated - np.mean(audio_decimated)

# normalize to prevent clipping
max_val = np.max(np.abs(audio_decimated)) # finding the loudest point in audio, can be negative so take abs
if max_val > 0:
    # normalizing and scaling the audio
    audio_normalized = audio_decimated / max_val
    audio_normalized *= 0.5  # 50% volume to prevent distortion
else:
    audio_normalized = audio_decimated

# convert to int16 since WAV file format uses integers, not floats
audio_int16 = (audio_normalized * 32767).astype(np.int16)

print(f"Max amplitude: {np.max(np.abs(audio_normalized)):.2f}")

# save to WAV
wav_filename = 'fm_radio.wav'
print(f"\nSaving to {wav_filename}...")

wavfile.write(wav_filename, AUDIO_RATE, (audio_normalized * 32767).astype(np.int16))

print(f"\nSaved to {wav_filename}")