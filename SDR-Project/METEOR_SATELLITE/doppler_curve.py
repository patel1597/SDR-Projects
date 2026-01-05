import pandas as pd
import matplotlib.pyplot as plt

# 1. LOAD DATA
csv_file = '/Users/rahilpatel/Documents/GitHub/SDR-Projects/SDR-Project/METEOR_SATELLITE/doppler_log_140625.csv'
df = pd.read_csv(csv_file)

# 2. PRINT COLUMNS (Debugging)
print("I found these columns in your CSV:", df.columns.tolist())

# 3. CLEAN COLUMNS (Removes accidental spaces)
df.columns = df.columns.str.strip()

# 4. DYNAMIC PLOT (Uses index if 'Time' is missing)
plt.figure(figsize=(10, 6))

# If 'Time' doesn't exist, we'll use the 'Altitude_Deg' or just the row index
if 'Time' in df.columns:
    x_axis = df['Time']
    plt.xlabel('Time (UTC)')
elif 'Altitude_Deg' in df.columns:
    x_axis = df['Altitude_Deg']
    plt.xlabel('Satellite Elevation (Degrees)')
else:
    x_axis = df.index
    plt.xlabel('Sample Number')

plt.plot(x_axis, df['Frequency_Hz'], color='blue', linewidth=2, label='Tuned Frequency')
plt.axhline(y=137100000, color='red', linestyle='--', alpha=0.5, label='Center Freq (137.1 MHz)')

plt.title('Meteor-M2-4 Doppler Tracking')
plt.ylabel('Tuned Frequency (Hz)')
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend()
plt.show()