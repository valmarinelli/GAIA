# -*- coding: utf-8 -*-
"""
Set of functions that enable the SRS python command interface (SRSpci) to
elaborate raw spectral data and obtain the spectral aerosol optical depth (AOD).

To see versions and changelog, open the __init__.py

"""
import numpy as np
from datetime import datetime, timedelta
#%%---------------------------------------------------------------------------
def datenum( dt ):
    """ DATENUM function emulates the corresponding MATLAB/OCTAVE one """
    if isinstance(dt, datetime):
        dt = [dt]
    elif isinstance(dt, np.ndarray):
        dt = [ dt[k] for k in range(len(dt)) ]

    Dnum = []
    for j in range( len(dt) ):
        mdn = dt[j] + timedelta(days = 366)
        frac_seconds = ( dt[j] - datetime( dt[j].year,dt[j].month,dt[j].day,\
        0,0,0) ).seconds / (24.0 * 60.0 * 60.0)
        frac_microseconds = dt[j].microsecond / (24.0 * 60.0 * 60.0 * 1.0e6)
        Dnum.append( mdn.toordinal() + frac_seconds + frac_microseconds )

    if len(dt) == 1:
        return Dnum[0]
    else:
        return np.array(Dnum)
#%%---------------------------------------------------------------------------
def sunPosition( Date, Site, Height=100., Pres=999, Tamb=999 ):
    """
    Obtain Sun position, in terms of its Zenith and Azimuth angles,
    for any position on Earth surface, given the right LATITUDE (North
    positive) and LONGITUDE (East positive).

    Based on the Michalsky algorithm, includes corrections suggested by
    Spencer (1989) (accuracy: ~0.01 deg). Furthermore, corrections due to
    atmospheric refraction are included for the Zenith angle calculation.

    Acknowledgments: part of the algorithm has been adapted from the original
    version for R:
    http://stackoverflow.com/questions/8708048/position-of-the-sun-given-time-of-day-latitude-and-longitude

    Parameters
    ----------
    Date : list of datetime objects
        It can be a single time value or a list of time objects.
        It is important that it is used UTC (GMT) instead of local time.
    Site : list of floats (2)
        This list must contain two values:
        - Norh latitude of the instrument's position, in degrees.
        - East longitude of the instrument's position, in degrees.
    Height : float, optional
        Elevation of the measurement site, in [meters] above mean sea level.
        This is necessary ONLY if there are no measured pressure values.
    Pres : float, optional
        Atmospheric pressure in [bar], measured at the observating site or
        estimated according to the Standard Atmosphere value (if Pres=0)
    Tamb : float, optional
        Ambient (daily) temperature in [Celsius], measured at the observating
        site or estimated according to standard atmospheric values (if Tamb=999)

    Returns
    -------
    Zang : ndarray
        Solar Zenith Angle calculated for the current date, time and
        geographical position.
    Azim : ndarray
        Solar Azimuth calculated for the current date, time and geographical
        position.
    SunR : ndarray
        Calculated Sun-Earth distance with Michalsky algorithm, expressed in
        Astronomical Unit (AU)
    """
    # Input to the Astronomical Almanac: Modified Julian Date, calculated as
    # the difference between the JD and the J2000 epoch (2000-01-01 12:00 UTC).
    # Also used as output while debugging.
    # The Julian Date for J2000 Epoch is 2451545.0, but in this case we
    # compensate also for the difference introduced by the
    # DATENUM function, whose reference start time is 00:00, 1 Jan, 0 AD
    Time = datenum( Date ) - 730486.5
    Hour = datenum( Date ) % 1 * 24.
    if isinstance(Date, datetime): Date = [Date]

    # Ecliptic coordinates:
    # 1. Mean longitude (degrees)
    mnlong = (280.460 + 0.9856474 * Time) % 360
    if isinstance(mnlong, float):
        if mnlong<0.: mnlong += 360.
    else: mnlong[mnlong<0.] += 360.
    # 2. Mean anomaly (radians)
    mnanom = np.deg2rad( (357.528 + 0.9856003 * Time) % 360 )
    # 3. Ecliptic longitude (radians) -- CORRECTED in Ver. 0.9
    eclong = np.deg2rad( (mnlong + 1.915 * np.sin(mnanom) + 0.020 * \
             np.sin(2 * mnanom)) % 360 )
    if isinstance(eclong, float):
        if eclong<0.: eclong += 2 * np.pi
    else: eclong[eclong<0.] += 2 * np.pi
    # 4. Obliquity of ecliptic (radians)
    oblqec = np.deg2rad( 23.439 - 4.0e-7 * Time )
    if isinstance(oblqec,float): oblqec = [ oblqec ];  eclong = [ eclong ]

    # Celestial coordinates:
    # Right ascension and declination (radians)
    ra = np.zeros(len(Date))
    for l in range(len(Date)):
        num = np.cos(oblqec[l]) * np.sin(eclong[l])
        den = np.cos(eclong[l])
        if den<0: ra[l] = np.arctan(num / den) + np.pi
        elif (den>=0) & (num<0): ra[l] = np.arctan(num / den) + 2. * np.pi
        else: ra[l] = np.arctan(num / den)
    dec = np.arcsin( np.sin(oblqec) * np.sin(eclong) )

    # Local coordinates:
    # 1. Greenwich mean sidereal time
    gmst = ( 6.697375 + 0.0657098242 * Time + Hour ) % 24
    # 2. Local mean sidereal time
    lmst = np.deg2rad( ( (gmst + Site[1] / 15.) % 24 ) * 15. )
    # 3. Hour angle
    ha = lmst - ra
    for l in range(len(Date)):
        if   ha[l] < -np.pi: ha[l] = ha[l] + 2. * np.pi
        elif ha[l] >  np.pi: ha[l] = ha[l] - 2. * np.pi
    # 4. Turn Latitude in radians to simplify input for trigonometric functions
    lat = np.deg2rad(Site[0])

    # Calculate the Elevation and Azimuth angles (radians)
    elev = np.arcsin( np.sin(dec) * np.sin(lat) + \
        np.cos(dec) * np.cos(lat) * np.cos(ha) )
    azim = np.arcsin( -np.cos(dec) * np.sin(ha) / np.cos(elev) )

    PosCond = np.sin(dec) - np.sin(elev) * np.sin(lat) >= 0
    for l in range(len(Date)):
        if PosCond[l] & (np.sin(azim[l]) < 0): azim[l] += 2 * np.pi
        elif (not PosCond[l]): azim[l] = np.pi - azim[l]

    # Correct the Elevation Angle values due to atmosperic refraction effect.
    # 1. Absolute air temperature  at ground (kelvin)
    # For out-of-range values, use a standard value
    if (Tamb < -99) | (Tamb > 90): T = 25. + 273.15
    else: T = Tamb + 273.15              # Otherwise, use the measured value(s)

    # 2. Air pressure-temperature ratio. The former is expressed in bar.
    # Default: use standard Mid-Latitudes atmosphere
    if Pres == 999: pTratio = stdatm(Date, Height)[1] / T * 1000
    else: pTratio = Pres / T * 1000      # Otherwise, use the measured value(s)

    if isinstance(pTratio,float): pTratio = np.repeat( pTratio, len(elev) )

    correction = np.zeros(len(elev))
    # 3. Correcting small elevation/high SZA values
    g1 = (np.rad2deg(elev) < 15) & (np.rad2deg(elev) >= -2.5)
    correction[g1] = pTratio[g1] * (0.1594 + 0.0196 * elev[g1] + \
    0.00002 * elev[g1]**2) / (1. + 0.505 * elev[g1] + 0.0845 * elev[g1]**2)
    # 4. Correction for average and high elevations
    g2 = (np.rad2deg(elev) >= 15) & (np.rad2deg(elev) < 90)
    correction[g2] = 0.00452 * pTratio[g2] / np.tan( elev[g2] )

    # Sun-Earth distance in AU (Michalsky's paper)
    SunR = 1.00014-0.01671*np.cos(mnanom)-0.00014*np.cos(2.*mnanom)

    # Output the SZA (as complement to the Elev.), Azimuth
    return 90. - np.rad2deg(elev) - correction, np.rad2deg(azim), SunR

def sunrad_spa( Date, Site, Height=100., Pres=999, Tamb=999 ):
    """
    Obtain Sun position, in terms of its Zenith and Azimuth angles,
    for any position on Earth surface, given the right LATITUDE (North
    positive), LONGITUDE (East positive) and ELEVATION above sea level (meters).

    Based on the Blanco-Muriel et al. (2001) algorithm, mimicking the SUNRAD
    version 2.0 behaviour, includes corrections due to atmospheric refraction,
    included within the Zenith angle calculation procedure.

    Parameters
    ----------
    Date : list of datetime objects
        It can be a single datetime value or a list of datetime objects.
        It is important that it is used UTC instead of local time.
    Site : list of floats (2)
        This list must contain two values:
        - Norh latitude of the instrument's position, in degrees.
        - East longitude of the instrument's position, in degrees.
    Height : float, optional
        Elevation of the measurement site, in [meters] above mean sea level.
        This is necessary ONLY if there are no measured pressure values.
    Pres : float, optional
        Atmospheric pressure in [bar], measured at the observating site or
        estimated according to the Standard Atmosphere value (if Pres=0).
    Tamb : float, optional
        Ambient (daily) temperature in [Celsius], measured at the observating
        site or estimated according to standard atmospheric values (if Tamb=999)

    Returns
    -------
    Zang : ndarray
        Solar Zenith Angle calculated for the current date, time and
        geographical position.
    Azim : ndarray
        Solar Azimuth calculated for the current date, time and geographical
        position.
    SunR : ndarray
        Calculated Sun-Earth distance with Michalsky algorithm, expressed in
        Astronomical Unit (AU)
    """
    if isinstance(Date, datetime): Date = [Date]
    # Smart initialization of some in-loop variables
    jEpoch, Zang, Azim, corrZ, elev = np.zeros( (5,len(Date)) )
    # Convert Latitude into radians, to improve readability into formulas
    lat = np.deg2rad(Site[0])
    # To correct the Elevation Angle values due to atmosperic refraction effect,
    # we need: 1. Absolute air temperature  at ground (kelvin)
    # Default: use an ambient temperature of 25 Celsius
    if (Tamb == 999): T = 298.15
    else: T = Tamb + 273.15          # In case, use the measured value(s)
    # 2. Air pressure-temperature ratio. The former is expressed in bar.
    # Default: use standard Mid-Latitudes atmosphere
    if (Pres == 999): pTratio = stdatm(Date, Height)[1] / T * 1000
    else: pTratio = Pres / T * 1000  # In case, use the measured value(s)

    if isinstance(pTratio,float): pTratio = np.repeat( pTratio, len(Date) )

    for l in range(len(Date)):
        # Let's introduce some variables to improve code readability
        Y = Date[l].year;     m = Date[l].month;
        D = Date[l].day;      M = (m - 14.)/12.;
        H = Date[l].hour + Date[l].minute/60. + Date[l].second/3600.
        # Julian Day difference with J2000, as in the Astronomical Almanac
        # Ver 0.9: MODIFIED original formula, corrected apparent error in
        # predicting JD value (-1 day) and removed redundant math operations
        jEpoch[l] = 365.25 * (Y + 4800. + M) + 366. - (3. * ((Y + 4900. + M)\
                    /100.))/4. + D - 2483620.5 + H/24.

        # Ecliptic coordinates of the Sun
        Omega = 2.1429000 - 0.001039459400 * jEpoch[l]
        Mlong = 4.8950630 + 0.017202791698 * jEpoch[l] # Mean Longitude
        Manom = 6.2400600 + 0.017201969900 * jEpoch[l] # Mean Anomaly
        # Ecliptic Longitude
        EclLon = Mlong + 0.03341607 * np.sin(Manom) + 3.4894e-4 * np.sin(2*Manom)\
            - 1.134e-4 - 2.03e-5 * np.sin(Omega)
        # Obliquity of the Ecliptic
        EclObl = 0.4090928 - 6.2140e-9 * jEpoch[l] + 3.96e-5 * np.cos(Omega)

        # Convert from ecliptic to celestial coordinates
        # Right Ascension
        RtAsc  = np.arctan( (np.cos(EclObl) * np.sin(EclLon) )/ np.cos(EclLon) )
        if RtAsc < 0: RtAsc += 2. * np.pi
        # Declination
        Decl   = np.arcsin( np.sin(EclObl) * np.sin(EclLon) )
        # Greenwich Mean Sidereal Time
        gmst   = 6.6974243242 + 0.0657098283 * jEpoch[l] + H
        # Hour Angle: Local Mean Sidereal Time - Right Ascension
        HrAng  = np.deg2rad(gmst * 15. + Site[1]) - RtAsc

        # Azimuth angle
        Azim[l] = np.arctan( -np.sin(HrAng) / ( np.tan(Decl) * np.cos(lat) -\
                  np.cos(HrAng) * np.sin(lat) ) )
        if Azim[l] < 0: Azim[l] += 2. * np.pi
        # Solar Zenith Angle: first approximation
        Zang[l] = np.arccos( np.cos(lat) * np.cos(HrAng) * \
                  np.cos(Decl) + np.sin(Decl) * np.sin(lat) )
        # Parallax correction: depends on Earth mean radius and Earth-Sun distance (1 AU)
        Paralx = 63701.01 / 149597890. * np.sin(Zang[l])
        # Solar Zenith Angle corrected for parallax
        Zang[l]= np.rad2deg(Zang[l] + Paralx)
        # Sun-Earth distance in AU (Michalsky's paper)
        SunR = 1.00014-0.01671*np.cos(Manom)-0.00014*np.cos(2.*Manom)

        # Correcting small elevation/high SZA values
        elev[l] = 90 - Zang[l]
        if   (elev[l] < 15) & (elev[l] >= -2.5):
            corrZ[l] = pTratio[l] * (0.1594 + 0.0196 * elev[l] + 0.00002 \
            * elev[l]**2) / (1. + 0.505 * elev[l] + 0.0845 * elev[l]**2)
        # Correcting average and high elevations
        elif (elev[l] >= 15) & (elev[l] < 90):
            corrZ[l] = 0.00452 * pTratio[l] / np.tan(np.deg2rad(elev[l]))

    return Zang - corrZ, np.rad2deg(Azim), SunR
#%%---------------------------------------------------------------------------
def stdatm(Date, Height):
    """
    Calculate atm. Pressure value according to the International Standard
    Atmosphere for Summer or Winter at Mid Latitudes

    Parameters
    ----------
    Date : datetime object or string
        Input is accepted in one of these formats:
         1. single datetime value. UTC-referenced values are required
         2. season (``winter``/``summer``) referred to the Northern Hemisphere
         3. other formats are accepted, but produce generic std. P value
    Height : float
        Elevation of the measurement site, in [meters] above mean sea level.

    Returns
    -------
    Pres : float
        Standard atmospheric pressure value at the given altitude in [bar]
    Season : int
        Numerical code representing the actual season of measurement:
         0 is the northern hemisphere "Winter" (from October to March)
         1 is the northern hemisphere "Summer" (from April to September)
         2 if the input Date was not in a valid format (std. atmosphere used)
    """
    if   isinstance(Date, datetime):
        Season = 1 * (4 <= Date.month <= 9)  # Sort of "step function"
    elif isinstance(Date, str):
        if   Date.lower() in [ 'winter', 'win', 'w' ]: Season = 0
        elif Date.lower() in [ 'summer', 'sum', 's' ]: Season = 1
        else: Season = 2
    else: Season = 2

    if Season == 0:
        # Winter Std Atmosphere for Mid Latitudes
        return Season, 1.0180 * np.exp( -1.28e-4 * Height )
    elif Season == 1:
        # Summer Std Atmosphere for Mid Latitudes
        return Season, 1.0133 * np.exp( -1.1859e-4 * Height )
    else:
        # If Date is not in a valid format, use the US standard atmosphere
        return Season, 1.01325 * np.exp( -1.184e-4 * Height )

def airmass(zang, O3=False, Lat=45.):
    """
    Compute Air Mass Factor (AMF) for several atmospheric components.
    To maintain compatibility with the EuroSkyRad network measurements, same
    scheme as the actual SUNRAD module is used:

        - Komhyr (1989) formula for Ozone [3] component
        - Kasten and Young (1989) formula for the rest of components:
          molecular (Rayleigh)[1], NO2 [2], Water Vapour [4] and Aerosols [5].

    **Note**: numbers within brackets [#] denote the corresponding component
    as labelled within the SUNRAD code (i.e. IM value).

    Parameters
    ----------
    zang : float
        Solar Zenith Angle, possibly calculated by the **sunPosition**
        function included within the present package.
    O3 : boolean, optional
        Default value is ``False``, change if you need the Ozone air mass factor
    Lat : float, optional
        Latitude of the measurement site, in [N degrees]. It is needed just
        in case of Ozone AMF calculation (``O3=True``). Default value: 45 deg.

    Returns
    -------
    AMF : float
        Contribution of the selected gaseous component to the total AMF
    """
    Z = np.deg2rad(zang)
    if O3:
        O3layer = 26. - 0.1 * (Lat**2)**0.5  # Non-negative value for Latitude
        factor = ( 6371.229**2. ) / ( 6371.229 + O3layer )**2.
        return 1. / ( 1. - factor * ( np.sin(Z)**2. )**0.5 )
    else:
        return 1. / ( np.cos(Z) + 0.50572 * ( 96.07995 - zang )**-1.6364 )

def Guyairmass(zang, C):
    """
    Air Mass Factor computed with Gueymard (2001) formulas

    Parameters
    ----------
    zang : float
        Solar Zenith Angle, possibly calculated by the sunPosition+atmos_correct
        functions included within the present package.
    C : integer
        Label associated to a single gaseous attenuating component:
            [1] molecular (Rayleigh) scattering
            [2] NO2 absorption
            [3] Ozone absorption
            [4] Water Vapour or Aerosols (same set of coefficients)

    Returns
    -------
    AMF : float
        Contribution of the selected gaseous component to the total AMF
    """
    a = [ [ 0.45665, 0.07, 96.4836, -1.6970 ], \
          [ 268.45 , 0.5 , 115.420, -3.2922 ], \
          [ 60.230 , 0.5 , 117.960, -3.4536 ], \
          [ 0.031141, 0.1, 92.4710, -1.3814 ] ]
    Z = np.deg2rad(zang)
    return \
    1. / ( np.cos(Z) + a[C-1][0] * (zang**a[C-1][1]) * (a[C-1][2] - zang)**a[C-1][3] )

#%%---------------------------------------------------------------------------
def rayleigh_OD(WaveLgt, Lat, Height, Pres=0 ):
    """
    Estimate the Optical Depth due to the molecular (Rayleigh) scattering.
    Calculation is made by the Bodhaine (1999) formulas, as in SUNRAD.pack

    Parameters
    ----------
    WaveLgt : array_like
        Single value or set of wavelengths, in [nanometers]
    Lat : float
        Latitude of the measurement site
    Height : float
        Elevation of the measurement site, in [meters] above mean sea level.
    Pres : float, optional
        Atmospheric pressure in [bar], measured at the observating site or
        estimated according to the Standard Atmosphere value (if Pres=0)

    Returns
    -------
    Tau_R : ndarray
        Rayleigh scattering contribution to the total atmospheric Optical Depth
    """
    # Up-to-date value (2017) of CO2 concentration [Original: 360 ppm]
    CO2ppm = 0.000400
    N_avog = 6.0221367e+23     # Avogadro's number
    WL = WaveLgt/1000          # Convert wavelengths in microns

    if Pres == 0:
        Pres = stdatm(0, Height)[1] # Standard atmospheric value in [bar]

    Ma_dry = 15.0556 * CO2ppm + 28.9595     # Mean molecular weight of dry air
    Zc = 0.73737 * Height + 5517.56   # Effective mass-weighted column altitude
    TwoPhi = 2.0 * np.deg2rad(Lat)    # Argument of Gravity accel. formulas
    grav_0 = 980.6160 * ( 1. - 0.0026373 * np.cos(TwoPhi) + \
            5.9e-6 * ( np.cos(TwoPhi) )**2 ) # The sea level accel. of gravity

    # The effective acc. of gravity, where its value needs to be representative
    # of the mass-weighted column of air molecules above the site
    grav = grav_0 - ( 3.085462e-4 + 2.27e-7 * np.cos(TwoPhi) ) * Zc + \
        ( 7.254e-11 + 1.0e-13 * np.cos(TwoPhi) ) * Zc**2 - \
        ( 1.517e-17 + 6.0e-20 * np.cos(TwoPhi) ) * Zc**3
    # Scattering Cross Section (in cm2 units)
    sig_s = ( 1.0455996 - 341.29061 / WL**2 - 0.90230850 * WL**2 ) \
          / ( 1. + 0.0027059889 / WL**2 - 85.968563 * WL**2 ) * 1e-28

    return sig_s * Pres * 1e6 * N_avog / ( Ma_dry * grav )

def ozone_OD(WaveLgt, Height, O3col=999, Tamb=999, Season=2 ):
    """
    Estimate the Optical Depth due to the Ozone absorption bands.
    Most of the algorithm is based on the SUNRAD.pack (ver. 0.94) implementation
    of the Gueymard (2001) formulas describing the ozone optical depth dependence
    on ground (ambient) measured parameters (TOC,T).

    Parameters
    ----------
    WaveLgt : ndarray
        Full set of spectrometer's wavelengths, in [nanometers]
    Height : float
        Elevation of the measurement site, in [meters] above mean sea level.
    O3col : float, optional
        Ozone effective pathlength (i.e. total column amount) measured in
        [atm-cm] units. The **default** value is evaluated for a standard
        Mid-Latitude Winter/Summer atmosphere. Actual season must be specified
        with the **Season** argument
    Tamb : float, optional
        Ambient (daily) temperature in [Celsius], measured at the observating
        site or estimated according to standard atmospheric values (if Tamb=999)
    Season : integer, optional
        Though optional, it is **highly recommended**. The code represents the
        actual season of measurement, and is given by the stdatm function:
          0 is the northern hemisphere "Winter" (from October to March)
          1 is the northern hemisphere "Summer" (from April to September)
          2 if the input Date was not in a valid format (std. atmosphere used)
    Returns
    -------
    Tau_Oz : ndarray
        Ozone absorption contribution to the total atmospheric Optical Depth
    """
    H  = Height/1000.          # Site altitude in [km asl]

    # 1. Initialize useful lambda functions
    AoCoeff = lambda a1, a2, a3, a4, x: (a1 + a2 * x + a3 * x**2) / (1. + a4 * x)
    Tground = lambda x,y: ( x + 273.15 - min(49.42, 70.24 - 23.428 * y +\
            2.523 * y**2) ) / (1. - min(0.1878, 0.26073 - 0.082424 * y +\
            9.098e-3 * y**2) )

    # 2. Read Ozone absorption coefficient values at ref, temperature Tro=228K
    Gueymard_table = np.loadtxt('gueymard_crsec_table.dat')
    Guey_wvl = Gueymard_table[:,0] # Original Gueymard's wvl grid
    AoTro_gm = Gueymard_table[:,3] # Original Ao values from Gueymard's table
    AoTro = np.interp(WaveLgt, Guey_wvl, AoTro_gm)

    # 3. Calculate the total ozone column in [atm-cm]=[10^-3 DU] and the
    #    effective ozone temperature (Teo) using the actal daily-avgd. Tamb
    if Season == 0: # Winter: use MLW values
        c0  = 0.3768
        c11 = 220.46;  c12 = 1.67
        c21 = 142.68;  c22 = 0.28498
    elif Season == 1: # Summer: use MLS values
        c0  = 0.3316
        c11 = 232.12;  c12 = 2.42
        c21 = 332.41;  c22 = - 0.34467
    else : # Season == 2 or any other undefined season: use USSA+avg. values
        c0  = 0.3434
        c11 = 226.29;  c12 = 2.045

    if O3col == 999:
        O3col = c0 * (1. - 8.98e-3 * H)

    if Tamb == 999:
            Teo = c11 - c12 * H
    elif Tamb != 999:
            Teo = c21 + c22 * Tground(Tamb, H)

    Ao3 = np.copy(AoTro) # Initialize Ao3 as a copy of AoTro
    WL = WaveLgt/1000.  # Support variable, Wavelengths in [micrometers]
    for w in range(len(WaveLgt)):
        if WaveLgt[w] < 310.:
            Ao3[w] = max( 0, AoTro[w] + (Teo - 228.) * \
                AoCoeff(0.25326  , -1.7253  , 2.92850, -3.5890, WL[w]) + \
                AoCoeff(9.6635e-3, -0.063685, 0.10464, -3.6879, WL[w]) * \
                (Teo - 228.)**2 )
        elif 310. <= WaveLgt[w] < 344.:
            Ao3[w] = max( 0, AoTro[w] + (Teo - 228.) * \
                AoCoeff(0.396260, -2.3272  , 3.41760, 0, WL[w]) + \
                AoCoeff(0.018268, -0.063685, 0.10464, 0, WL[w]) * \
                (Teo - 228.)**2 )
        # Within 344<=WVL<407 and for WVL>560, no Temperature correction is needed
        elif 407. <= WaveLgt[w] < 560.:
            Ao3[w] = max( 0, AoTro[w] * ( 1. + 0.0037083 * (Teo - 228.) * \
                    np.exp(28.04 * (0.4474 - WL[w])) ) )
    return Ao3 * O3col

# Ver. 0.9.5: introducing no2_OD
def no2_OD(WaveLgt, Height, Tamb=999, Season=2 ):
    """
    Estimate the Optical Depth due to the NO2 absorption bands.
    Most of the algorithm is based on the SUNRAD.pack (ver. 0.94) implementation
    of the Gueymard (2001) formulas describing the NO2 optical depth dependence
    on ground (ambient) temperature.

    Parameters
    ----------
    WaveLgt : ndarray
        Full set of spectrometer's wavelengths, in [nanometers]
    Height : float
        Elevation of the measurement site, in [meters] above mean sea level.
    Tamb : float, optional
        Ambient (daily) temperature in [Celsius], measured at the observating
        site or estimated according to standard atmospheric values (if Tamb=999)
    Season : integer, optional
        Though optional, it is **highly recommended**. The code represents the
        actual season of measurement, and is given by the stdatm function:
          0 is the northern hemisphere "Winter" (from October to March)
          1 is the northern hemisphere "Summer" (from April to September)
          2 if the input Date was not in a valid format (std. atmosphere used)
    Returns
    -------
    Tau_NO2 : ndarray
        Ozone absorption contribution to the total atmospheric Optical Depth
    """
    H  = Height/1000. # Site altitude in [km asl]
    # Initialize useful lambda function
    Tground = lambda x,y: ( x + 273.15 - min(49.42, 70.24 - 23.428 * y +\
            2.523 * y**2) ) / (1. - min(0.1878, 0.26073 - 0.082424 * y +\
            9.098e-3 * y**2) )

    # Read NO2 absorption coefficient values at ref, temperature Trn=243.2K
    Gueymard_table = np.loadtxt('gueymard_crsec_table.dat')
    Guey_wvl = Gueymard_table[:,0] # Original Gueymard's wvl grid
    AoTrn_gm = Gueymard_table[:,4] # Original Ao values from Gueymard's table
    AoTrn = np.interp(WaveLgt, Guey_wvl, AoTrn_gm)

    # Estimate the reduced NO2 path length in [atm-cm] and
    if Season == 0: # Winter: use MLW values
        NO2col = 1.99e-4
        c11 = 220.46;  c12 = 1.67
        c21 = 142.68;  c22 = 0.28498
    elif Season == 1: # Summer: use MLS values
        NO2col = 2.18e-4
        c11 = 232.12;  c12 = 2.42
        c21 = 332.41;  c22 = - 0.34467
    else : # Season == 2 or any other undefined season: use USSA+avg. values
        NO2col = 2.04e-4
        c11 = 226.29;  c12 = 2.045

    if Tamb == 999:
            Ten = c11 - c12 * H
    elif Tamb != 999:
            Ten = c21 + c22 * Tground(Tamb, H)

    Aon = np.copy(AoTrn) # Initialize Aon as a copy of AoTrn
    WL = WaveLgt/1000.  # Support variable, Wavelengths in [micrometers]
    for w in range(len(WaveLgt)):
        if WaveLgt[w] < 625.:
            Aon[w] = max( 0, 1. + (Ten - 243.2) * np.polyval([-42.635, \
                96.615, -86.136, 37.821, -8.1829, 0.69773], WL[w]) )
        else :
            Aon[w] = max( 0, 1. + (Ten - 243.2) * \
                np.polyval([-0.04985, 0.03539], WL[w]) )
    return Aon * NO2col

# Ver. 0.9.5: introducing wv_MTau
def wv_MTau(WaveLgt, Height, Pres=0, Season=2 ):
    """
    Estimate the Optical Depth due to the water vapour (WV) absorption bands.
    Most of the algorithm is based on the SUNRAD.pack (ver. 0.94) implementation
    of the Gueymard (2001) formulas describing the WV optical depth dependence
    on wavelength and atmospheric pressure.

    Parameters
    ----------
    WaveLgt : ndarray
        Full set of spectrometer's wavelengths, in [nanometers]
    Height : float
        Elevation of the measurement site, in [meters] above mean sea level.
    Pres : float, optional
        Atmospheric pressure in [bar], measured at the observating site or
        estimated according to the Standard Atmosphere value (if Pres=0)
    Season : integer, optional
        Though optional, it is **highly recommended**. The code represents the
        actual season of measurement, and is given by the stdatm function:
          0 is the northern hemisphere "Winter" (from October to March)
          1 is the northern hemisphere "Summer" (from April to September)
          2 if the input Date was not in a valid format (std. atmosphere used)
    Returns
    -------
    Tau_NO2 : ndarray
        Ozone absorption contribution to the total atmospheric Optical Depth
    """
    global Site, Zang
    if Pres == 0:
        Pres = stdatm(0, Height)[1] # Standard atmospheric value in [bar]
    # Air pressure ratio: actual / standard (p0 = 1 atm)
    P = Pres / 1.01325
    WVL = WaveLgt / 1.0e3  # Convert Wvlt in microns

    # Read reference WV absorption coefficient values
    Gueymard_table = np.loadtxt('gueymard_crsec_table.dat')
    Guey_wvl = Gueymard_table[:,0] # Original Gueymard's wvl grid
    AoWv_gm = Gueymard_table[:,2] # Original Ao values from Gueymard's table
    AoWv = np.interp(WaveLgt, Guey_wvl, AoWv_gm)

    # Estimate the WV path length in [atm-cm]
    if Season == 0: # Winter: use MLW values
        WVcol = 2.9816 * np.exp(-0.552e-3 * Height)
    elif Season == 1: # Summer: use MLS values
        WVcol = 0.9108 * np.exp(-0.529e-3 * Height)
#    else : # Season == 2 or any other undefined season: use USSA+avg. values
#        WVcol = 1.419 * np.exp( )

    IRwvl = WVL > 0.67
    kw = np.ones(len(WVL))
    Q  = -0.02454 + 0.037533 * WVL[IRwvl]
    kw[IRwvl] = (0.98449 + 0.023889 * WVL[IRwvl]) * WVcol**Q
    fw = kw * ( 0.394 - 0.26946 * WVL + (0.46478 + 0.23757 * WVL) * P )
    n  = 0.88631 + 0.025274 * WVL - 3.5949 * np.exp(-4.5445 * WVL)
    c  = 0.53851 + 0.003262 * WVL + 1.5244 * np.exp(-4.2892 * WVL)

    h  = (0.525 + 0.246 * AoWv * WVcol)**0.45
    h[AoWv<0.01] = 0.624 * AoWv[AoWv<0.01] * WVcol[AoWv<0.01]**0.457

    AMF = airmass(Zang, Lat=Site[0])
    Bwv = h * np.exp(0.1916 - 0.0785 * AMF + 4.706e-4 * AMF**2)
    return ( (AMF*WVcol)**1.05 * fw**n * Bwv * AoWv )**c
