# -*- coding: utf-8 -*-
"""
Basic functions for the SRS python command interface (SRSpci)

To see versions and changelog, open the __init__.py

"""
import time
from . import avaspecSRS as AS
from . import cfg  # Special module contanining variables shared across all modules
# from pathlib import Path  # Path library (for Python >=3.4)

def Initialization():
    # Initialize the communication interface and the internal data structures
    AS.AVS_Init(0)
    # Checks the list of USB-connected devices
    Ndev = AS.AVS_GetNrOfDevices()
    if (Ndev == 0):
        print("No devices found.")
        return '', 0
    # Create the pointer to the buffer that stores identity info for each
    # of the connected spectrometers
    Dev_p = AS.AvsIdentityType * 1
    # Allocate 75 bytes for the list data, 0 bytes required, retrieve
    # info from the device buffer using the pointer
    Device = AS.AVS_GetList(75, 0, Dev_p)[1]
    cfg.serial = str(Device.SerialNumber.decode("utf-8"))
    cfg.dev_handle = AS.AVS_Activate(Device)
    devcon = AS.DeviceConfigType
    params = AS.AVS_GetParameter(cfg.dev_handle, 63484, 0, devcon)[1]
    # pixels = params.m_Detector_m_NrPixels
    return cfg.serial, params

def GetLambda():
    return AS.AVS_GetLambda(cfg.dev_handle, cfg.alambda)

def GetLambda_alt(params):
    """Alternative way to get the wavelength grid: from the polynomial fit
    coefficients recorded into the EEPROM, reconstruct the pixel values."""
    import numpy as np
    # Get the coefficients of the Wavelength calibration function
    Coeffs = list( params.m_Detector_m_aFit )
    Coeffs.reverse()
    # Reconstruct wavelengths from the calibration function
    return np.polyval( Coeffs, range(2048) )

def PrepareMeasure(Tint, Navg, Nmeas):
    AS.AVS_UseHighResAdc(cfg.dev_handle, True)
    measconfig = AS.MeasConfigType
    measconfig.m_StartPixel = 0
    measconfig.m_StopPixel = 2047
    measconfig.m_IntegrationTime = float(Tint) # Integration time in ms
    measconfig.m_IntegrationDelay = 0
    measconfig.m_NrAverages = int(Navg)
    measconfig.m_CorDynDark_m_Enable = 0
    measconfig.m_CorDynDark_m_ForgetPercentage = 0
    measconfig.m_Smoothing_m_SmoothPix = 0
    measconfig.m_Smoothing_m_SmoothModel = 0
    measconfig.m_SaturationDetection = 1  # Enable detection of saturated pixels
    measconfig.m_Trigger_m_Mode = 0
    measconfig.m_Trigger_m_Source = 0
    measconfig.m_Trigger_m_SourceType = 0
    measconfig.m_Control_m_StrobeControl = 0
    measconfig.m_Control_m_LaserDelay = 0
    measconfig.m_Control_m_LaserWidth = 0
    measconfig.m_Control_m_LaserWaveLength = 0.0
    measconfig.m_Control_m_StoreToRam = 0
    out = AS.AVS_PrepareMeasure(cfg.dev_handle, measconfig)
    if (out < 0):
        print("AVS_PrepareMeasure: Error code %d" % out)
    return out

def StartMeasure(Nmeas):
    scans = 0
    while (scans < Nmeas):
        AS.AVS_Measure(cfg.dev_handle, 0, 1)
        dataready = False
        while (dataready == False):
            dataready = (AS.AVS_PollScan(cfg.dev_handle) == True)
            time.sleep(0.01)
        if dataready == True:
            scans = scans + 1
            #print("Scan %d done" % scans)  # Debug output
    return

# Ver. 0.9: Assembled GetMeasure from test script and old GetData functions
def GetMeasure(params, Nmeas):
    # Wait 0.5 s before measuring
    time.sleep(0.5)
    # Get TEC temperature before exposing CCD
    Temp = Temperature(params)
    print( 'TEC temperature: %6.4f C' % Temp )
    # Check if temperature is within the acceptable range
    while abs( 5.0 - Temp ) >= 0.1:
        print( 'TEC out of tolerance. Waiting 10 sec. for stabilization...' )
        time.sleep(10)
        Temp = Temperature(params)
    StartMeasure(Nmeas)
    # Take measurement, return TEC temperature, and Spectrum
    timestamp = 0
    data = AS.AVS_GetScopeData(cfg.dev_handle, timestamp, cfg.spectraldata )
    # data[0] = timestamp
    # cfg.spectraldata = data[1]
    return Temp, data[1]

def StopMeasure():
    # Force stopping measurement. Needed when Nmeas= infinite
    return AS.AVS_StopMeasure(cfg.dev_handle)

def ShutDown():
    # Return error codes (1,0) if device is successfully released.
    Err1 = AS.AVS_Deactivate(cfg.dev_handle)
    Err2 = AS.AVS_Done()
    return Err1, Err2

def OpenShutter():
    """Make the spectrometer to output a TTL signal to open the shutter,
    i.e. put the digital output of port 3 to 0 V.
    Returns an ERROR code as output."""
    return AS.AVS_SetDigOut(cfg.dev_handle, 3, False)

def CloseShutter():
    """Make the spectrometer to output a TTL signal to close the shutter,
    i.e. put the digital output of port 3 to 5.0 V.
    Returns an ERROR code as output."""
    return AS.AVS_SetDigOut(cfg.dev_handle, 3, True)

def Temperature(params):
    """Retrieve temperature reading on the detector's TEC."""
    volts = AS.AVS_GetAnalogIn(cfg.dev_handle, 0, 0.0)
    Coeffs = list( params.m_Temperature_3_m_aFit )
    return Coeffs[0] + Coeffs[1] * volts

# Ver. 0.7.5: Introduced WriteHeader function
def WriteHeader(filepath):
    cfg.date = time.strftime('%Y-%m-%d',time.gmtime())
    F = open( filepath+cfg.date+'.txt', 'a' )
    F.write( '# Instrument ID: ' + cfg.serial + '\n' )
    F.write( '# Location: ARPA VdA\n' )
    F.write( '# Wavelength grid [nm]\n')
    # More pythonic way to write a list on a file. N.B. out is a list on None
    out = [ F.write( '%10.4f' % l ) for l in cfg.alambda ]; del out
    F.write( '\n# Date_Time  Integration_Time[ms]' +
                '  Averaging  TEC_Temperature[degC]  Spectral_data[cnts]\n' )
    F.close()

def WriteData( typestr, inttime, avg, temperature, data, filepath):
    """Write spectrometer data on a text file, with a standard format:
     - File name: year-month-day. NOTE: DATE used comes from the CFG module,
       update it by using the WriteHeader function.
     - Data format: one spectrum on each line, separator is a blanck (' ');
                    spectral data follows the real (GMT) and internal timestamp.

    Parameters
    ----------
    typestr : string
        A short string describing the measurement type. As convention, use:
        - 'dark' for dark current (shutter is closed)
        - 'solar' for direct sun measurement (shutter open)
        - 'labtest' for any measurement done indoor (shutter open)
    inttime : float
        Integration time used for measurement
    avg : integer
        Averaging used for measurement
    data: ndarray
        A single spectum retrieved from the spectrometer
    filepath: string
        The absolute path where to save spectral data

    """
    Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    F = open( filepath+cfg.date+'.txt', 'a' )   # Append data to a daily file
    # First values in a row: timestamp, int. time, averaging and temperature
    F.write( Time + ' ' + str(inttime) + ' ' + typestr + ' ' + str(avg) + \
            '%8.4f' % temperature )
    # More pythonic way to write a list on a file. N.B. out is a list on None
    out = [ F.write( '%8.1f' % d ) for d in data ]; del out
    F.write( '\n' )   # Write the EOL character at the row closing
    F.close()


