# -*- coding: utf-8 -*-
"""
@author: valerio
Date: 2018-04-09

"""
from SRSpci import operateSRS as op
from SRSpci import SRStools as srt
from SRSpci import cfg
import numpy as np
import sys
from datetime import datetime
import time

# Initialize the spectrometer, reading parameters stored into the ROM
params = op.Initialization()[1]
if params==0:
    sys.exit()
# Obtain the actual wavelength grid from the spectrometer
cfg.alambda = op.GetLambda()
Wvl = np.array(cfg.alambda)
#%%
Tint = float( input('Choose integration time [ms]  ') )
Nmeas = 1  # Make a single measure for each int. time
Navg = 20  # Keep measurement averaging fixed
M0 = 0   # Initialize a parameter to check for signal variations
##      ARPA VdA, Saint-Christophe (AO), 570 m asl; [45.7422 N, 7.3568 E]
Site = [ 45.7422, 7.3568, 570. ]
#%%
timestamp = datetime.utcnow()
SZA, Azim, SunEarthR = srt.sunPosition(timestamp, Site[:2], Height=Site[2])
print('Starting measure on ' + timestamp.strftime('%x %X' ) )
print('Solar coordinates: ' + str(SZA) + ' SZA,  ' + str(Azim) + ' Azimuth')
print( 'Using int. time: %10.4f ms.' % Tint )

while True:
    try:
        out = op.PrepareMeasure(Tint, Navg, Nmeas)
        if out < 0:
            print('Error on measurement preparation.')
            sys.exit()  # Alternatively, can use: break
        # Update timestamp with actual value
        timestamp = datetime.utcnow()
        SZA, Azim = srt.sunPosition(timestamp, Site[:2], Height=Site[2])[:2]
        # Before taking measures, check if the shutter can be opened
        out = op.OpenShutter()
        if out < 0:
            print('Error: can''t operate on TTL output (shutter OPENING)' )
            sys.exit()  # Alternatively, can use: break
        # Take an OPEN measurement
        Temp, Open = op.GetMeasure(params, Nmeas)
        # Close shutter immediately after measure, to avoid hysteresis effects
        out = op.CloseShutter()
        if (any(O >= 69000 for O in Open)):
            print('Saturation reached, adjusting int. time to ' + str(Tint/2) + ' ms')
            Tint = Tint/2.
            break
        # Calculate an average value of the most intense part of solar spectrum
        Intvl = (Wvl>=485) & (Wvl<586)
        M = np.mean(np.array(Open)[Intvl])
        if M0:
            if abs(M-M0) < 100:
                compare = 'remained quite STABLE from'
            elif (M-M0 > 100):
                compare = 'has INCREASED from'
            elif (M-M0 < -100):
                compare = 'has DECREASED from'
        else:
            compare = 'is going to be compared with'
        print( 'Mean value within [485:585]nm: {:f} counts.'.format(M) + \
                '\nSignal ' + compare + ' the last snapshot.\n' )
        # print( 'Next measurement in 1 sec...\n' )
        time.sleep(1)
        M0 = M
    except KeyboardInterrupt:
        op.ShutDown()
        print('Ctrl-C pressed, stopping measurements.')
        sys.exit()
