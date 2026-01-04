import numpy as np # imports the library to do array math
from rtlsdr import RtlSdr # imports RTL-SDR radio control class which lets us talk to the RTL-SDR hardware
import pyModeS as pms # lets us turn the binary into names
import time # for us to work with time
from math import radians, cos, sin, asin, sqrt # the specific tools we need for distance calculation on earth

# configuation used
FREQ = 1090e6 # 1090 MHz is the ADS-B frequency
RATE = 2.0e6 # sample rate (fast enough)
GAIN = 40.0 # gain to amplify the weaker signals (this worked the best) -- planes are above me so far signals
THRESH = 0.03 # looked at the adsb_test to see where the strongest magnitudes are (used this for detection)

# my location to check how far the planes are
HOME_LAT = 42.096
HOME_LON = -88.121

sdr = RtlSdr() # creating the RTL-SDR object
sdr.center_freq = FREQ # what frequency it should tune into
sdr.sample_rate = RATE  # what the RTL should sample at
sdr.gain = GAIN # amplifier gain

# create the aircraft dictionary
aircraft = {}

def get_distance(lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [HOME_LON, HOME_LAT, lon2, lat2]) # converting the degrees into radians
    dlon = lon2 - lon1 # the longitude distance from the plane and me 
    dlat = lat2 - lat1 # the latitiude distance from the plane and me 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2 # Haversine Formula -- used to calculate the distance between two points on a sphere
    c = 2 * asin(sqrt(a)) # the central angle
    return c * 3956 # multiply to get angles into miles -- 3956 is the radius of the earth

# where the plane is heading in h
# this formuala is derived like so with and 8 point compass
# dividing the 360° compass into eight equal sectors, each spanning 45°
# add an offset + 22.5 -- since north is from -22.5 to 22.5 it would now be from 0 to 45, when using the integer division 
# removing that negative part (numbers from 0 to 360)
def get_dir(h):
    if h is None: 
        return "---"
    return ['N','NE','E','SE','S','SW','W','NW'][int((h+22.5)/45)%8] # lets us know where the plane is going in compass direction based on where it is heading

def sort_rule(plane_pair):
    data  = plane_pair[1] # get the data dictionary for the plane

    if data['dist'] is not None: # check if we have distance, return it, if not put it at the end
        return data['dist']
    else: 
        return 9999

iteration = 0 # used to control the display (updating every 1 second)

# starting the infinite loop since live airplane tracker
while True:
    iteration += 1 # increment the counter each loop

    try:
        samples = sdr.read_samples(256 * 1024) # try to get the samples (this worked best in the adsb_test file) -- complex numbers
    except:
        continue # jump back to the beginning, will keep trying to get the samples
        
    mag = np.abs(samples) # will calulate the magnitude of the complex samples
    # loop through the magnitude array
    i = 0
    while i < len(mag) - 250: # we need 250 samples ahead to decode the full message (there are 112 bits and 2 samples per bit so 224 samples minimum this just gives a buffer)
        if mag[i] > THRESH: # needs to exceed the threshold
            bits = []
            for b in range(112): # decode the 112 bits, ADS-B long message = 112 bits, this also contains all the data
                pos = i + b * 2 # calculate the position of bit in the array, each bit is 2 samples, remember 1 bit is 1 microsecond
                if pos + 1 >= len(mag): break # if the reads past the end 
                # decode one bit using PPM (pulse-position modulation), if pulse in first half bit 1, if pulse in second half bit 0
                if mag[pos] > mag[pos + 1]: 
                    bits.append('1')
                else:
                    bits.append('0')
            
            if len(bits) >= 112: # check if we decoded enough bits
                try:
                    msg = f"{int(''.join(bits[:112]), 2):028X}" # convert the bits into hex with 28 digits
                    if pms.crc(msg) != 0: # validate message using CRC (checking for corruption -- added due to call signs being strange), skips the message if it is strange
                        i += 1
                        continue

                    df = pms.df(msg) # extract Downlink Format 

                    if df in [17, 18]: # this has the callsign, position, velocity
                        icao = pms.adsb.icao(msg) # extract 24-bit aircraft address
                        if icao and icao not in ['000000','FFFFFF']: # validate the address
                            # create new aircraft entry if first time seeing this ICAO
                            if icao not in aircraft:
                                aircraft[icao] = {'cs':None,'alt':None,'spd':None,'hdg':None,'vr':None, 
                                                 'lat':None, 'lon':None, 'even':None, 'odd':None,
                                                 'dist':None, 'last': time.time()}
                            
                            ac = aircraft[icao] # create shorthand reference to this aircraft
                            ac['last'] = time.time() # update last-seen timestamp

                            tc = pms.adsb.typecode(msg) # extract Type Code from ADS-B message

                            if 1 <= tc <= 4: # decode callsign from message
                                cs = pms.adsb.callsign(msg).strip().replace('_', '')
                                if cs: 
                                    ac['cs'] = cs # only store if callsign exists
                            
                            elif 9 <= tc <= 18: # extract altitude from position message
                                ac['alt'] = pms.adsb.altitude(msg)
                                # store even or odd position message (need both pairs not just one) using oe_flag
                                if pms.adsb.oe_flag(msg) == 0: 
                                    ac['even'] = msg
                                else: 
                                    ac['odd'] = msg
                                
                                # decode position when we have both messages
                                if ac['even'] and ac['odd']:
                                    # takes even message, takes odd message, takes timestamps of both, returns (latitude, longitude) tuple
                                    pos = pms.adsb.position(ac['even'], ac['odd'], time.time(), time.time())
                                    if pos:
                                        ac['lat'], ac['lon'] = pos # store
                                        ac['dist'] = get_distance(ac['lat'], ac['lon']) # using the function to calculate the distance and store it

                            elif tc == 19: # decode velocity
                                v = pms.adsb.velocity(msg)
                                if v: 
                                    ac['spd'], ac['hdg'], ac['vr'] = v[0], v[1], v[2] # returns the speed (knots), degree, and vertical rate (ft/min)
                except: # if any error skip, no corrupted messages
                    pass
                i += 250 # skipping the 250 samples after message is processed
        else:
            i += 1 # no pulse detection move to next sample
    
    if iteration % 25 == 0: # updating the display around one second 
        now = time.time()
        # remove aircraft not seen for 60 seconds
        # create a temporary dictionary to hold the ones we want to keep
        temp_aircraft = {}
        for k, v in aircraft.items():
            # 'now' is the current time, 'v[last]' is when we last saw the plane
            time_since_seen = now - v['last']
            # if it was seen less than 60 seconds ago, keep it
            if time_since_seen < 60:
                temp_aircraft[k] = v
        # update the main aircraft database with the filtered list
        aircraft = temp_aircraft

        # Create a dictionary for the planes ready to be displayed
        active = {}
        for k, v in aircraft.items():
            # Check if we have an altitude OR a callsign for this plane
            if v['alt'] is not None or v['cs'] is not None:
                active[k] = v # add it 

        # making the title with border
        print("="*115)
        print(f"ADSB Tracker | ACTIVE: {len(active)}".center(115))
        print("="*115)
        
        # header Layout
        header = f"{'CALLSIGN':<12} {'ALTITUDE':<14} {'SPEED':<12} {'HEADING':<15} {'CLIMB RATE':<15} {'DIST':<12} {'LAT/LON'}" # proper padding to space it out
        print(f"\033[1;32m{header}\033[0m") # light green bold header with reset
        print("-" * 115)
        
        if active:
            # sort by proximity (closest planes first)
            sorted_planes = sorted(active.items(), key=sort_rule)
            for icao, d in sorted_planes:
                # callsign
                if d['cs']: 
                    cs = d['cs']
                else:
                    cs = f"{icao}"
                # altitude
                if d['alt']:
                    alt = f"{int(d['alt']):,} ft"
                else:
                    alt = "---"
                # speed
                if d['spd']:
                    spd = f"{int(d['spd'])} kt"
                else:
                    spd = "---"
                # heading
                if d['hdg']:
                    direction_name = get_dir(d['hdg'])
                    hdg = f"{int(d['hdg'])}° {direction_name}"
                else:
                    hdg = "---"
                # distance
                if d['dist']:
                    dist = f"{d['dist']:.1f} mi"
                else:
                    dist = "---"
                # position (Lat/Lon)
                if d['lat']:
                    pos = f"{d['lat']:.3f}, {d['lon']:.3f}"
                else:
                    pos = "---"
                # vertical rate (fpm)
                # using 115 due to air being bumpy
                if d['vr'] is not None:
                    if d['vr'] > 115:
                        vr = f"+{int(d['vr']):<5} fpm"
                    elif d['vr'] < -115:
                        vr = f"{int(d['vr']):<5} fpm"
                    else:
                        vr = "LEVEL"
                else:
                    vr = "---"
                
                print(f"{cs:<12} {alt:<14} {spd:<12} {hdg:<15} {vr:<15} {dist:<12} {pos}") # alligning to the header
        else:
            print("\n" + "SCANNING SKY FOR ADS-B SIGNALS...".center(115) + "\n")
        
        print("-" * 115)
    
    time.sleep(0.01) # pause for 10 milliseconds to give CPU a break