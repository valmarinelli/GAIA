# -*- coding: utf-8 -*-
"""
@author: valerio
Date: 2018-04-09

"""
from SRSpci import operateSRS as op
from SRSpci import SRStool as srt
from SRSpci import cfg as cfg
import sys
#import numpy as np
from datetime import datetime
import time
import os
#import locale

params = op.Initialization()[1]
if params==0:
    sys.exit()
cfg.alambda = op.GetLambda()
DATAPATH = '/home/pi/GAIA/testdata/' + cfg.serial + '/'
if not os.path.exists(DATAPATH):
    os.mkdir(DATAPATH)

#%%
T0 = 1.1  # Starting from a low integration time, then adjusting
Nmeas = 1  # Make a single measure for each int. time
Navg = 20  # Keeping averaging fixed
Count = 0  # Initializing loop counter
path = DATAPATH # + Day + '_'    # General pattern where to save data files
##      ARPA VdA, Saint-Christophe (AO), 570 m asl; [45.7422 N, 7.3568 E]
Site = [ 45.7422, 7.3568, 570. ]
#-----------------------------------------------------------------------------#
#%% DAILY Routine
timestamp = datetime.utcnow()
SZA, Azim, SunEarthR = srt.sunPosition(timestamp, Site[:2], Height=Site[2])
# Set default output STRFTIME according to it_IT locale
# locale.setlocale( locale.LC_TIME, 'it_IT' )
print('Starting measure on ' + timestamp.strftime('%x %X' ) )
# Day = timestamp.strftime('%Y-%m-%d')
# Save each spectrum on a single file using incremental file naming
op.WriteHeader(path)
print( 'Written header on data file.' )

while SZA<80:

    if Count == 0:
            Tint = T0
    try:
        print( '[ Int. time %10.4f msec.' % Tint )
        out = op.PrepareMeasure(Tint, Navg, Nmeas)
        if out < 0:
            print('Error on measurement preparation.')
            sys.exit()  # Alternatively, can use: break
        # Update timestamp with actual value
        timestamp = datetime.utcnow()
        SZA, Azim = srt.sunPosition(timestamp, Site[:2], Height=Site[2])[:2]

        # Check shutter is closed before measuring dark current
        out = op.CloseShutter()
        if out < 0:
            print('Error: can''t operate on TTL output (shutter CLOSING)' )
            sys.exit()  # Alternatively, can use: break
        # Take DARK measurement
        DarkTemp, Dark = op.GetMeasure(params, Nmeas)

        out = op.OpenShutter()
        if out < 0:
            print('Error: can''t operate on TTL output (shutter OPENING)' )
            sys.exit()  # Alternatively, can use: break
        # Take OPEN measurement
        Temp, Open = op.GetMeasure(params, Nmeas)
        # Close shutter immediately after measure, to avoid hysteresis effects
        out = op.CloseShutter()

        # DarkCorr = [ m-n for m,n in zip(Open, Dark) ]
        M = 6.15e4 / max(Open)
        if (any(O>=6.55e4 for O in Open)):
            print('Saturation reached, adjusting int. time.')
            Tint = Tint/2.
            pass # break interrompe il ciclo!!
        # Take 5% as empirical threshold for re-adjusting int. time
        elif (Count == 0) or (abs(M - 1) >= 0.05):
            # Rescale int, time to obtain a max around 65'000 counts
            print('Adjusting int. time according to the last data counts.')
            Tint = Tint * M
            pass

        op.WriteData( 'dark', Tint, Navg, DarkTemp, Dark, path )
        print( 'Written dark spectral data on file.' )

        op.WriteData( 'solar', Tint, Navg, Temp, Open, path )
        print( 'Written experimental spectral data on file.\n' )

        Count += 1
        print( 'Waiting 10 sec. for the next measurement...' )
        time.sleep(10)
    except KeyboardInterrupt:
        op.ShutDown()
        print('Ctrl-C pressed, stopping measurements.')
        print('Measurement routine ended after %d iterations.' % Count)
        sys.exit()

