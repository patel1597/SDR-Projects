# RTL-SDR Projects

RF engineering projects built over Winter Break 2024 using Software-Defined Radio.

---

# 1. RTL-SDR FM Spectrum Analyzer

Captures and analyzes FM radio signals across the broadcast band.

## What it does:

- Captures RF signals from 88-108 MHz (FM radio band)
- Performs FFT analysis to convert time-domain to frequency-domain
- Averages 128 FFT chunks to reduce noise
- Automatically detects and identifies FM stations
- Calculates the SNR
- Displays professional spectrum plot

## Results:

- Can be seen in the screenshots folder

## Technologies:

- Python 3.12, NumPy, Matplotlib, SciPy
- RTL-SDR Blog V3 hardware (R820T tuner)
- FFT-based signal processing

# 2. FM Radio Demodulator

Decodes FM broadcasts and outputs audio files.

## What it does:

- Tunes to specific FM station (default: 96.3 MHz -- Chicago's main radio channel -- can be changed)
- Demodulates FM signal using polar discriminator algorithm
- Applies de-emphasis filter (75μs US broadcast standard)
- Processes multi-stage filtering and decimation
- Outputs 48 kHz WAV audio file

## Results:

- Successfully decoded FM radio broadcasts
- Clear audio output from multiple stations
- CD-quality audio (48 kHz, 16-bit)
- Can be heard from the fm_radio.wav

## Technologies:

- Python 3.12
- NumPy, SciPy, Matplotlib
- pyrtlsdr, PyAudio
- FFT-based signal processing
- Digital filtering (Butterworth)
- FM demodulation algorithms
