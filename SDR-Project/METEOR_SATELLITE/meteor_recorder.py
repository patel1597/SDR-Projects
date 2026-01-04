import numpy as np
from rtlsdr import RtlSdr
from datetime import datetime, timezone
import ephem
import time

# --- CONFIG ---
FREQ_BASE = 137.1e6
SAMPLE_RATE = 1.0e6
GAIN = 40.0
RECORD_SECONDS = 900
MIN_ELEVATION = 10.0 

sats_info = {
    "METEOR-M2-3": ("1 57166U 23091A   26001.57598228  .00000071  00000+0  49901-4 0  9999",
                    "2 57166  98.6349  59.7662 0002969 302.9025  57.1867 14.24028888130809"),
    "METEOR-M2-4": ("1 59051U 24039A   26001.61231182  .00000098  00000+0  63505-4 0  9990",
                    "2 59051  98.6794 323.2123 0006119 296.7927  63.2625 14.22405061 95586")
}

chicago = ephem.Observer()
chicago.lat, chicago.lon, chicago.elev = '41.8781', '-87.6298', 181

def get_doppler(sat):
    """Calculates the center frequency based on orbital physics"""
    chicago.date = datetime.now(timezone.utc)
    sat.compute(chicago)
    shift = - (sat.range_velocity / 299792458.0) * FREQ_BASE
    return FREQ_BASE + shift

# --- INITIALIZE SDR ---
sdr = RtlSdr()
sdr.sample_rate = SAMPLE_RATE
sdr.gain = GAIN

best_sat_obj = None
best_strength = -999

print("--- Scanning for Meteor Signal ---")

for name, (l1, l2) in sats_info.items():
    sat = ephem.readtle(name, l1, l2)
    chicago.date = datetime.now(timezone.utc)
    sat.compute(chicago)
    
    alt = np.degrees(sat.alt)
    if alt > MIN_ELEVATION:
        sdr.center_freq = get_doppler(sat)
        # Power measurement
        pwr = 10 * np.log10(np.mean(np.abs(sdr.read_samples(256*1024))**2))
        print(f"Checking {name}: Alt {alt:.1f}°, Signal {pwr:.2f} dB")
        if pwr > best_strength:
            best_strength, best_sat_obj = pwr, sat
    else:
        print(f"Skipping {name}: Below horizon ({alt:.1f}°)")

if not best_sat_obj:
    print("No satellites visible. Closing SDR to stay cool.")
    sdr.close()
    exit()

# --- RECORDING LOOP ---
filename = f"meteor_AUTO_{datetime.now().strftime('%H%M%S')}.iq"
print(f"\n>>> LOCK ON: {best_sat_obj.name} | Recording to: {filename}")

try:
    with open(filename, 'wb') as f:
        num_chunks = int((SAMPLE_RATE * RECORD_SECONDS) / (256*1024))
        for i in range(num_chunks):
            # Hardware Doppler Tracking
            sdr.center_freq = get_doppler(best_sat_obj)
            samples = sdr.read_samples(256*1024)
            
            # Conversion to 8-bit Interleaved IQ
            iq = np.empty(samples.size * 2, dtype=np.uint8)
            iq[0::2] = (samples.real * 127.5 + 127.5).astype(np.uint8)
            iq[1::2] = (samples.imag * 127.5 + 127.5).astype(np.uint8)
            f.write(iq.tobytes())
            
            if i % 25 == 0:
                print(f"Tracking {best_sat_obj.name} | Alt: {np.degrees(best_sat_obj.alt):.1f}° | Progress: {i/num_chunks*100:.1f}%", end='\r')

except KeyboardInterrupt:
    print("\n[!] User stopped recording early.")
finally:
    sdr.close() # <--- THIS keeps your SDR from melting
    print("SDR powered down. File closed.")