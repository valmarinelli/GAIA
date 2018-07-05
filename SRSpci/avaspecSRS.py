"""
AvaSpec Linux Python library - modified for SRS

To see versions and changelog, open the __init__.py

"""
import ctypes
import struct

LIBAVS_PATH = "/usr/local/lib/libavs.so.0.2.0"

AVS_SERIAL_LEN = 10
USER_ID_LEN = 64
WM_MEAS_READY = 0x401
NPIXEL = 2048

class AvsIdentityType(ctypes.Structure):
  _pack_ = 1
  _fields_ = [("SerialNumber", ctypes.c_char * AVS_SERIAL_LEN),
              ("UserFriendlyName", ctypes.c_char * USER_ID_LEN),
              ("Status", ctypes.c_char)]

class MeasConfigType(ctypes.Structure):
  _pack_ = 1
  _fields_ = [("m_StartPixel", ctypes.c_uint16),
              ("m_StopPixel", ctypes.c_uint16),
              ("m_IntegrationTime", ctypes.c_float),
              ("m_IntegrationDelay", ctypes.c_uint32),
              ("m_NrAverages", ctypes.c_uint32),
              ("m_CorDynDark_m_Enable", ctypes.c_uint8),
              ("m_CorDynDark_m_ForgetPercentage", ctypes.c_uint8),
              ("m_Smoothing_m_SmoothPix", ctypes.c_uint16),
              ("m_Smoothing_m_SmoothModel", ctypes.c_uint8),
              ("m_SaturationDetection", ctypes.c_uint8),
              ("m_Trigger_m_Mode", ctypes.c_uint8),
              ("m_Trigger_m_Source", ctypes.c_uint8),
              ("m_Trigger_m_SourceType", ctypes.c_uint8),
              ("m_Control_m_StrobeControl", ctypes.c_uint16),
              ("m_Control_m_LaserDelay", ctypes.c_uint32),
              ("m_Control_m_LaserWidth", ctypes.c_uint32),
              ("m_Control_m_LaserWaveLength", ctypes.c_float),
              ("m_Control_m_StoreToRam", ctypes.c_uint16)]

class DeviceConfigType(ctypes.Structure):
  _pack_ = 1
  _fields_ = [("m_Len", ctypes.c_uint16),
              ("m_ConfigVersion", ctypes.c_uint16),
              ("m_aUserFriendlyId", ctypes.c_char * USER_ID_LEN),
              ("m_Detector_m_SensorType", ctypes.c_uint8),
              ("m_Detector_m_NrPixels", ctypes.c_uint16),
              ("m_Detector_m_aFit", ctypes.c_float * 5),
              ("m_Detector_m_NLEnable", ctypes.c_bool),
              ("m_Detector_m_aNLCorrect", ctypes.c_double * 8),
              ("m_Detector_m_aLowNLCounts", ctypes.c_double),
              ("m_Detector_m_aHighNLCounts", ctypes.c_double),
              ("m_Detector_m_Gain", ctypes.c_float * 2),
              ("m_Detector_m_Reserved", ctypes.c_float),
              ("m_Detector_m_Offset", ctypes.c_float * 2),
              ("m_Detector_m_ExtOffset", ctypes.c_float),
              ("m_Detector_m_DefectivePixels", ctypes.c_uint16 * 30),
              ("m_Irradiance_m_IntensityCalib_m_Smoothing_m_SmoothPix", ctypes.c_uint16),
              ("m_Irradiance_m_IntensityCalib_m_Smoothing_m_SmoothModel", ctypes.c_uint8),
              ("m_Irradiance_m_IntensityCalib_m_CalInttime", ctypes.c_float),
              ("m_Irradiance_m_IntensityCalib_m_aCalibConvers", ctypes.c_float * 4096),
              ("m_Irradiance_m_CalibrationType", ctypes.c_uint8),
              ("m_Irradiance_m_FiberDiameter", ctypes.c_uint32),
              ("m_Reflectance_m_Smoothing_m_SmoothPix", ctypes.c_uint16),
              ("m_Reflectance_m_Smoothing_m_SmoothModel", ctypes.c_uint8),
              ("m_Reflectance_m_CalInttime", ctypes.c_float),
              ("m_Reflectance_m_aCalibConvers", ctypes.c_float * 4096),
              ("m_SpectrumCorrect", ctypes.c_float * 4096),
              ("m_StandAlone_m_Enable", ctypes.c_bool),
              ("m_StandAlone_m_Meas_m_StartPixel", ctypes.c_uint16),
              ("m_StandAlone_m_Meas_m_StopPixel", ctypes.c_uint16),
              ("m_StandAlone_m_Meas_m_IntegrationTime", ctypes.c_float),
              ("m_StandAlone_m_Meas_m_IntegrationDelay", ctypes.c_uint32),
              ("m_StandAlone_m_Meas_m_NrAverages", ctypes.c_uint32),
              ("m_StandAlone_m_Meas_m_CorDynDark_m_Enable", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_CorDynDark_m_ForgetPercentage", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_Smoothing_m_SmoothPix", ctypes.c_uint16),
              ("m_StandAlone_m_Meas_m_Smoothing_m_SmoothModel", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_SaturationDetection", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_Trigger_m_Mode", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_Trigger_m_Source", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_Trigger_m_SourceType", ctypes.c_uint8),
              ("m_StandAlone_m_Meas_m_Control_m_StrobeControl", ctypes.c_uint16),
              ("m_StandAlone_m_Meas_m_Control_m_LaserDelay", ctypes.c_uint32),
              ("m_StandAlone_m_Meas_m_Control_m_LaserWidth", ctypes.c_uint32),
              ("m_StandAlone_m_Meas_m_Control_m_LaserWaveLength", ctypes.c_float),
              ("m_StandAlone_m_Meas_m_Control_m_StoreToRam", ctypes.c_uint16),
              ("m_StandAlone_m_Nmsr", ctypes.c_int16),
              ("m_StandAlone_m_Reserved", ctypes.c_uint8 * 12), # SD Card, do not use
              ("m_Temperature_1_m_aFit", ctypes.c_float * 5),
              ("m_Temperature_2_m_aFit", ctypes.c_float * 5),
              ("m_Temperature_3_m_aFit", ctypes.c_float * 5),
              ("m_TecControl_m_Enable", ctypes.c_bool),
              ("m_TecControl_m_Setpoint", ctypes.c_float),
              ("m_TecControl_m_aFit", ctypes.c_float * 2),
              ("m_ProcessControl_m_AnalogLow", ctypes.c_float * 2),
              ("m_ProcessControl_m_AnalogHigh", ctypes.c_float * 2),
              ("m_ProcessControl_m_DigitalLow", ctypes.c_float * 10),
              ("m_ProcessControl_m_DigitalHigh", ctypes.c_float * 10),
              ("m_EthernetSettings_m_IpAddr", ctypes.c_uint32),
              ("m_EthernetSettings_m_NetMask", ctypes.c_uint32),
              ("m_EthernetSettings_m_Gateway", ctypes.c_uint32),
              ("m_EthernetSettings_m_DhcpEnabled", ctypes.c_uint8),
              ("m_EthernetSettings_m_TcpPort", ctypes.c_uint16),
              ("m_EthernetSettings_m_LinkStatus", ctypes.c_uint8),
              ("m_Reserved", ctypes.c_uint8 * 9720),
              ("m_OemData", ctypes.c_uint8 * 4096)]

def AVS_Init(x):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    paramflags = (1, "port",),
    AVS_Init = prototype(("AVS_Init", lib), paramflags)
    return AVS_Init(x)

def AVS_GetNrOfDevices():
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int)
    AVS_GetNrOfDevices = prototype(("AVS_GetNrOfDevices", lib),)
    return AVS_GetNrOfDevices()

def AVS_GetList(listsize, requiredsize, IDlist):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(AvsIdentityType))
    paramflags = (1, "listsize",), (2, "requiredsize",), (2, "IDlist",),
    AVS_GetList = prototype(("AVS_GetList", lib), paramflags)
    return AVS_GetList(listsize)

def AVS_Activate(deviceID):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(AvsIdentityType))
    paramflags = (1, "deviceId",),
    AVS_Activate = prototype(("AVS_Activate", lib), paramflags)
    return AVS_Activate(deviceID)

def AVS_UseHighResAdc(handle, enable):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool)
    paramflags = (1, "handle",), (1, "enable",),
    AVS_UseHighResAdc = prototype(("AVS_UseHighResAdc", lib), paramflags)
    return AVS_UseHighResAdc(handle, enable)

def AVS_PrepareMeasure(handle, measconf):
    lib = ctypes.CDLL(LIBAVS_PATH)
    datatype = ctypes.c_byte * 41
    data = datatype()
    temp = datatype()
    temp = struct.pack("HHfIIBBHBBBBBHIIfH", measconf.m_StartPixel,
                                             measconf.m_StopPixel,
                                             measconf.m_IntegrationTime,
                                             measconf.m_IntegrationDelay,
                                             measconf.m_NrAverages,
                                             measconf.m_CorDynDark_m_Enable,
                                             measconf.m_CorDynDark_m_ForgetPercentage,
                                             measconf.m_Smoothing_m_SmoothPix,
                                             measconf.m_Smoothing_m_SmoothModel,
                                             measconf.m_SaturationDetection,
                                             measconf.m_Trigger_m_Mode,
                                             measconf.m_Trigger_m_Source,
                                             measconf.m_Trigger_m_SourceType,
                                             measconf.m_Control_m_StrobeControl,
                                             measconf.m_Control_m_LaserDelay,
                                             measconf.m_Control_m_LaserWidth,
                                             measconf.m_Control_m_LaserWaveLength,
                                             measconf.m_Control_m_StoreToRam )

# copy bytes from temp to data, otherwise you will get a typing error below
    x = 0
    while (x < 41):
        data[x] = temp[x]
        x += 1
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_byte * 41)
    paramflags = (1, "handle",), (1, "measconf",),
    AVS_PrepareMeasure = prototype(("AVS_PrepareMeasure", lib), paramflags)
    return AVS_PrepareMeasure(handle, data)

def AVS_Measure(handle, dummyhandle, nummeas):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint16)
    paramflags = (1, "handle",), (1, "dummyhandle",), (1, "nummeas"),
    AVS_Measure = prototype(("AVS_Measure", lib), paramflags)
    return AVS_Measure(handle, 0, nummeas)

def AVS_StopMeasure(handle):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    paramflags = (1, "handle",),
    AVS_StopMeasure = prototype(("AVS_StopMeasure", lib), paramflags)
    return AVS_StopMeasure(handle)

def AVS_PollScan(handle):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_int)
    paramflags = (1, "handle",),
    AVS_PollScan = prototype(("AVS_PollScan", lib), paramflags)
    return AVS_PollScan(handle)

def AVS_GetScopeData(handle, timelabel, spectrum):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint32),\
        ctypes.POINTER(ctypes.c_double * NPIXEL))
    paramflags = (1, "handle",), (2, "timelabel",), (2, "spectrum",),
    AVS_GetScopeData = prototype(("AVS_GetScopeData", lib), paramflags)
    return AVS_GetScopeData(handle)

def AVS_GetParameter(handle, size, reqsize, deviceconfig):
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_uint32,\
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(DeviceConfigType))
    paramflags = (1, "handle",), (1, "size",), (2, "reqsize",), (2, "deviceconfig",),
    AVS_GetParameter = prototype(("AVS_GetParameter", lib), paramflags)
    return AVS_GetParameter(handle, size)

def AVS_SetParameter(handle, deviceconfig):
    lib = ctypes.CDLL(LIBAVS_PATH)
    datatype = ctypes.c_byte * 63484
    data = datatype()
    temp = datatype()
    temp = struct.pack("HH64B" +
                       "BH5f?8ddd2ff2ff30H" +      # Detector
                       "HBf4096fBI" +              # Irradiance
                       "HBf4096f" +                # Reflectance
                       "4096f" +                   # SpectrumCorrect
                       "?HHfIIBBHBBBBBHIIfHH12B" + # StandAlone
                       "5f5f5f" +                  # Temperature
                       "?f2f" +                    # TecControl
                       "2f2f10f10f " +             # ProcessControl
                       "IIIBHB" +                  # EthernetSettings
                       "9720B" +                   # Reserved
                       "4096B",                    # OemData
                       deviceconfig.mLen,
                       deviceconfig.m_ConfigVersion,
                       deviceconfig.m_aUserFriendlyId,
                       deviceconfig.m_Detector_m_SensorType,
                       deviceconfig.m_Detector_m_NrPixels,
                       deviceconfig.m_Detector_m_aFit,
                       deviceconfig.m_Detector_m_NLEnable,
                       deviceconfig.m_Detector_m_aNLCorrect,
                       deviceconfig.m_Detector_m_aLowNLCounts,
                       deviceconfig.m_Detector_m_aHighNLCounts,
                       deviceconfig.m_Detector_m_Gain,
                       deviceconfig.m_Detector_m_Reserved,
                       deviceconfig.m_Detector_m_Offset,
                       deviceconfig.m_Detector_m_ExtOffset,
                       deviceconfig.m_Detector_m_DefectivePixels,
                       deviceconfig.m_Irradiance_m_IntensityCalib_m_Smoothing_m_SmoothPix,
                       deviceconfig.m_Irradiance_m_IntensityCalib_m_Smoothing_m_SmoothModel,
                       deviceconfig.m_Irradiance_m_IntensityCalib_m_CalInttime,
                       deviceconfig.m_Irradiance_m_IntensityCalib_m_aCalibConvers,
                       deviceconfig.m_Irradiance_m_CalibrationType,
                       deviceconfig.m_Irradiance_m_FiberDiameter,
                       deviceconfig.m_Reflectance_m_Smoothing_m_SmoothPix,
                       deviceconfig.m_Reflectance_m_Smoothing_m_SmoothModel,
                       deviceconfig.m_Reflectance_m_CalInttime,
                       deviceconfig.m_Reflectance_m_aCalibConvers,
                       deviceconfig.m_SpectrumCorrect,
                       deviceconfig.m_StandAlone_m_Enable,
                       deviceconfig.m_StandAlone_m_Meas_m_StartPixel,
                       deviceconfig.m_StandAlone_m_Meas_m_StopPixel,
                       deviceconfig.m_StandAlone_m_Meas_m_IntegrationTime,
                       deviceconfig.m_StandAlone_m_Meas_m_IntegrationDelay,
                       deviceconfig.m_StandAlone_m_Meas_m_NrAverages,
                       deviceconfig.m_StandAlone_m_Meas_m_CorDynDark_m_Enable,
                       deviceconfig.m_StandAlone_m_Meas_m_CorDynDark_m_ForgetPercentage,
                       deviceconfig.m_StandAlone_m_Meas_m_Smoothing_m_SmoothPix,
                       deviceconfig.m_StandAlone_m_Meas_m_Smoothing_m_SmoothModel,
                       deviceconfig.m_StandAlone_m_Meas_m_SaturationDetection,
                       deviceconfig.m_StandAlone_m_Meas_m_Trigger_m_Mode,
                       deviceconfig.m_StandAlone_m_Meas_m_Trigger_m_Source,
                       deviceconfig.m_StandAlone_m_Meas_m_Trigger_m_SourceType,
                       deviceconfig.m_StandAlone_m_Meas_m_Control_m_StrobeControl,
                       deviceconfig.m_StandAlone_m_Meas_m_Control_m_LaserDelay,
                       deviceconfig.m_StandAlone_m_Meas_m_Control_m_LaserWidth,
                       deviceconfig.m_StandAlone_m_Meas_m_Control_m_LaserWaveLength,
                       deviceconfig.m_StandAlone_m_Meas_m_Control_m_StoreToRam,
                       deviceconfig.m_StandAlone_m_Nmsr,
                       deviceconfig.m_StandAlone_m_Reserved,
                       deviceconfig.m_Temperature_1_m_aFit,
                       deviceconfig.m_Temperature_2_m_aFit,
                       deviceconfig.m_Temperature_3_m_aFit,
                       deviceconfig.m_TecControl_m_Enable,
                       deviceconfig.m_TecControl_m_Setpoint,
                       deviceconfig.m_TecControl_m_aFit,
                       deviceconfig.m_ProcessControl_m_AnalogLow,
                       deviceconfig.m_ProcessControl_m_AnalogHigh,
                       deviceconfig.m_ProcessControl_m_DigitalLow,
                       deviceconfig.m_ProcessControl_m_DigitalHigh,
                       deviceconfig.m_EthernetSettings_m_IpAddr,
                       deviceconfig.m_EthernetSettings_m_NetMask,
                       deviceconfig.m_EthernetSettings_m_Gateway,
                       deviceconfig.m_EthernetSettings_m_DhcpEnabled,
                       deviceconfig.m_EthernetSettings_m_TcpPort,
                       deviceconfig.m_EthernetSettings_m_LinkStatus,
                       deviceconfig.m_Reserved,
                       deviceconfig.m_OemData)
    x = 0
    while (x < 63484):
        data[x] = temp[x]
        x += 1
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_byte * 63484)
    paramflags = (1, "handle",), (1, "deviceconfig",),
    AVS_SetParameter = prototype(("AVS_SetParameter", lib), paramflags)
    return AVS_SetParameter(handle, data)

#%%---------------------------------------------------------------------------
# V0.5: Introduce AVS_SetDigOut
def AVS_SetDigOut(handle, portID, enable):
    """Sets state of digital output.
    For SRS: control external shutter with TTL (5.0 V) signal at port 3"""
    lib = ctypes.CDLL(LIBAVS_PATH)
    # PROTOTYPE ordering: 1.output type  2.input type
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_bool)
    # ctypes notation: 1=INPUT parameter, 2=OUTPUT parameter
    paramflags = (1, "handle",), (1, "portID",), (1, "enable"),
    AVS_SetDigOut = prototype(("AVS_SetDigOut", lib), paramflags)
    return AVS_SetDigOut(handle, portID, enable)

# V0.5: Introduce AVS_GetAnalogIn
def AVS_GetAnalogIn(handle, inputID, volts):
    """Get Analog Input from the inputID object, with output value in volts."""
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float))
    paramflags = (1, "handle",), (1, "inputID",), (2, "volts"),
    AVS_GetAnalogIn = prototype(("AVS_GetAnalogIn", lib), paramflags)
    return AVS_GetAnalogIn(handle, inputID)

# V0.2: Introduce AVS_Deactivate
def AVS_Deactivate(handle):
    """De-activates selected spectrometer for communication"""
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    paramflags = (1, "handle",),
    AVS_Deactivate = prototype(("AVS_Deactivate", lib), paramflags)
    return AVS_Deactivate(handle)

# V0.2: Introduce AVS_Done
def AVS_Done():
    """Closes port and releases memory"""
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int)
    AVS_Done = prototype(("AVS_Deactivate", lib),)
    return AVS_Done()

# V0.5: Introduce AVS_Getlambda
def AVS_GetLambda(handle, alambda):
    """Returns the wavelength values corresponding to the pixels.
    The second argument alambda should be a NPIXEL-long empty list/array."""
    lib = ctypes.CDLL(LIBAVS_PATH)
    prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double * NPIXEL))
    paramflags = (1, "handle",), (2, "alambda",),
    AVS_GetLambda = prototype(("AVS_GetLambda", lib), paramflags)
    return AVS_GetLambda(handle)

