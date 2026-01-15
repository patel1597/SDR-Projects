import numpy as np
from rtlsdr import RtlSdr
from datetime import datetime, timezone
import ephem
import time
import os

# configuration
FREQ_CENTER = 137.850e6 # offset tuning to avoid the center spike 
FREQ_TARGET = 137.9e6 # actual M2-4 center frequency
SAMPLE_RATE = 1.024e6  # sample rate
GAIN = 44           # used this gain for the first image, worked!
RECORD_SECONDS = 900   # 15 minutes
MIN_ELEVATION = 15.0   # Clear the houses/fences

# my coordinates - closest city is Chicago (naming preference)
chicago = ephem.Observer()
chicago.lat, chicago.lon, chicago.elev = '42.11', '-88.03', 240 

# updated TLEs for Meteor M2-4 (make sure these are changed -- https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&amp;FORMAT=tle)
name = "METEOR-M2-4"
l1 = "1 59051U 24039A   26014.62579603  .00000005  00000+0  21828-4 0  9998"
l2 = "2 59051  98.6812 336.0269 0005985 252.4496 107.6028 14.22407185 97435"
m24 = ephem.readtle(name, l1, l2)


def get_doppler(sat):
    chicago.date = datetime.now(timezone.utc)
    sat.compute(chicago)
    # doppler formula: shift = - (relative_velocity / speed_of_light) * base_freq
    shift = - (sat.range_velocity / 299792458.0) * FREQ_TARGET
    return FREQ_CENTER + shift

# initialize the SDR
sdr = RtlSdr()
sdr.sample_rate = SAMPLE_RATE
sdr.gain = GAIN
sdr.bandwidth = 500e3 # tighten the bandwidth so local FM noises are gone

print(f"--- Waiting for {name} to rise above {MIN_ELEVATION}° ---")

while True:
    chicago.date = datetime.now(timezone.utc)
    m24.compute(chicago)
    alt = np.degrees(m24.alt) 
    if alt > MIN_ELEVATION:
        break
    print(f"Current Alt: {alt:.1f}° | Now waiting...", end = '\r')
    time.sleep(10)

# start recording 
timestamp = datetime.now().strftime('%H%M%S')
filename = f"meteor_M2_4_{timestamp}.cu8"
print(f"\n--- Satellite reached {MIN_ELEVATION}°. Recording to: {filename}")

try:
    with open(filename, 'wb') as f:
        sdr.read_samples(2048) # clear buffer

        # buffer to store chunks before writing
        num_chunks = int((SAMPLE_RATE * RECORD_SECONDS) / (256*1024))
        for i in range(num_chunks):
            # update doppler frequency
            if i % 40 == 0:
                sdr.center_freq = get_doppler(m24)

            # read samples (normalized floats -1 to 1)
            samples = sdr.read_samples(256*1024)
            
            # CU8 conversion for SatDump
            iq = np.empty(samples.size * 2, dtype=np.uint8)
            iq[0::2] = (samples.real * 127.5 + 127.5).astype(np.uint8)
            iq[1::2] = (samples.imag * 127.5 + 127.5).astype(np.uint8)
            f.write(iq.tobytes())
            
            # when to update the terminal
            if i % 20 == 0:
                pwr = 10 * np.log10(np.var(samples) + 1e-12)
                m24.compute(chicago)
                alt = np.degrees(m24.alt)
                print(f"Alt: {alt:.1f}° | PWR: {pwr:.1f} dB | Progress: {i/num_chunks*100:.1f}%", end='\r')

except KeyboardInterrupt:
    print("\nManual Stop")
finally:
    sdr.close()
    print(f"\nSaved. File: {filename}. Size: {os.path.getsize(filename)/1e9:.2f} GB") # now when this in SatDump as a .cadu remove this large file for storage