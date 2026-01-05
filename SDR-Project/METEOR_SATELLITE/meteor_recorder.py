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

# Updated TLEs for Jan 5, 2026
sats_info = {
    "METEOR-M2-3": ("1 57166U 23091A   26005.51071556  .00000047  00000+0  39593-4 0  9996",
                    "2 57166  98.6342  63.6309 0002894 287.5113  72.5749 14.24029570131368"),
    "METEOR-M2-4": ("1 59051U 24039A   26005.55153020  .00000049  00000+0  41673-4 0  9999",
                    "2 59051  98.6800 327.0910 0006012 283.4655  76.5853 14.22405817 96145")
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

# --- RECORDING & LOGGING ---
timestamp_str = datetime.now().strftime('%H%M%S')
filename_iq = f"meteor_{best_sat_obj.name}_{timestamp_str}.iq"
filename_log = f"doppler_log_{timestamp_str}.csv"

print(f"\n>>> LOCK ON: {best_sat_obj.name}")
print(f"Recording IQ to: {filename_iq}")
print(f"Logging Doppler to: {filename_log}")

try:
    with open(filename_iq, 'wb') as f_iq, open(filename_log, 'w') as f_log:
        # Write CSV Header for your portfolio graph
        f_log.write("Timestamp,Altitude_Deg,Frequency_Hz\n")
        
        num_chunks = int((SAMPLE_RATE * RECORD_SECONDS) / (256*1024))
        for i in range(num_chunks):
            # 1. Update Hardware Frequency
            current_f = get_doppler(best_sat_obj)
            sdr.center_freq = current_f
            
            # 2. Capture Samples
            samples = sdr.read_samples(256*1024)
            
            # 3. Save IQ Data (8-bit Interleaved)
            iq = np.empty(samples.size * 2, dtype=np.uint8)
            iq[0::2] = (samples.real * 127.5 + 127.5).astype(np.uint8)
            iq[1::2] = (samples.imag * 127.5 + 127.5).astype(np.uint8)
            f_iq.write(iq.tobytes())
            
            # 4. Log Telemetry every ~1 second
            if i % 4 == 0:
                best_sat_obj.compute(chicago)
                alt_deg = np.degrees(best_sat_obj.alt)
                time_now = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                f_log.write(f"{time_now},{alt_deg:.2f},{current_f:.2f}\n")
                
                print(f"Tracking {best_sat_obj.name} | Alt: {alt_deg:.1f}° | Freq: {current_f/1e6:.4f} MHz | {i/num_chunks*100:.1f}%", end='\r')

except KeyboardInterrupt:
    print("\n[!] User stopped recording.")
finally:
    sdr.close()
    print(f"\nSDR Powered Down. IQ file and Doppler CSV saved successfully.")