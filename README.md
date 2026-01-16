# RTL-SDR Projects

RF engineering projects built over Winter Break 2024 using Software-Defined Radio and Python.

For a lot of the filter understanding I used: https://community.sw.siemens.com/s/article/introduction-to-filters-fir-versus-iir
And the basic of filtering from my Linear Systems and Signals Course

And for me to Python with SDR this helped me a lot: https://pysdr.org/content/intro.html

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
- RTL-SDR Blog V3 hardware
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
- RTL-SDR Blog V3 hardware
- NumPy, SciPy, Matplotlib
- pyrtlsdr, PyAudio
- FFT-based signal processing
- Digital filtering (Butterworth)
- FM demodulation algorithms

# 3. ADSB Live Tracker

Real-time decoding of 1090 MHz Mode S Extended Squitter messages to track aircraft

## What it does:

- Captures raw 2 MSPS IQ data streams at 1090 MHz
- Implements custom Pulse Position Modulation (PPM) demodulation
- Analyzes 1 µs bit timing for Mode S message frames
- Uses pyModeS library for CRC-24 parity checks to validate message integrity
- Resolves Compact Position Reporting (CPR) to get latitude/longitude
- Extracts Flight ID, Altitude, Velocity, and Heading with real-time distance calculations

## Results:

- Successfully tracked 10+ simultaneous aircraft, with old aircrafts being removed (making the live tracker affect)
- Achieved a stable decode range of 50+ miles
- Real-time telemetry data viewable in console output
- 100% position accuracy validated against FlightAware reference data

## Technologies:

- Python 3.12, NumPy, pyModeS
- RTL-SDR Blog V3
- Mode S / ADS-B Protocol (DF17/18)
- Custom PPM demodulation with histogram-based thresholding
- CRC Error Detection algorithms and CPR (even/odd) getting latitude/longitude
- Haversine distance calculations

# 4. Meteor M2-4 Satellite Reception

Automated reception and decoding of multispectral Earth-observation imagery (USA).

## What it does:

- Predicts orbital passes and calculates real-time Doppler shifts using PyEphem
- Validates satellite position using N2YO tracking data: https://www.n2yo.com/?s=59051
- Records 1.024 Msps baseband IQ data at 137.9 MHz using a custom Python script
- Implements a -50 kHz frequency offset to correct for spectral inversion
- Bypasses hardware-specific DC-offset interference to maintain signal lock
- Manages high-bandwidth data acquisition (approx. 1.47 GB per 12-minute pass)

## Results & Decode:

- Successfully recovered high-resolution imagery of the Great Lakes region with other parts of the US/Canada
- Used SatDump for QPSK demodulation and Viterbi/Reed-Solomon error correction
- Reconstructed multispectral data into Visible and Thermal channel composites
- Performed Root Cause Analysis on sync-loss artifacts, identifying Disk I/O latency as the primary cause
- The best image I got is in the second_run folder and the file is called: msu_mr_MCIR.png

## Technologies:

- Python 3.12
- NumPy, PyEphem, pyrtlsdr
- SatDump (Post-processing & Image Reconstruction)
- RTL-SDR Blog V3 Hardware
- V-Dipole Antenna

# Main Lessons Learned:

# Antenna Geometry & Impedance Matching:

- At first, I set up the antenna wrong, including its polarization. But after I got my HAM radio license, I corrected orientation to parallel-to-surface for optimal circular polarization reception
- As for the length and angle of the antenna, I found a reddit link: https://www.reddit.com/r/amateursatellites/comments/jkhaz8/using_a_vdipole_antenna_to_receive_noaa_apt_and/

# Disk I/O Latency:

- Discovered that writing 1.024+ million samples per second to disk in Python can cause "dropped samples." This resulted in black sync-loss lines in satellite images, highlighting the trade-off between Python's ease of use and using SatDump to record to take care of these tweaks.

# Antenna Radiation Patterns:

- Observed that signal gain dropped at peak elevation (70°), identifying physical antenna "nulls" and the importance of ground-plane reflections in my DIY setup.
