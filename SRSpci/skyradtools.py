# -*- coding: utf-8 -*-
"""
Created on Thu Apr 19 18:26:48 2018

Tools for importing into a Python workspace Skyrad and Sunrad datasets.

@author: valerio
"""
import numpy as np
from datetime import datetime, timedelta
#%%---------------------------------------------------------------------------
def dateconvert( Date ):
    """
    Support function for the importskyrad() one.
    Take a [4x1] or [1x4] array of floats (Year, Month, Day, Hour)
    and convert it to a DATETIME object.
    """
    Minutes    = np.zeros(6)
    Minutes[4] = np.round( Date[3]%1*60. ).astype(int)
    return datetime( *Date.astype(int) ) + timedelta( *Minutes )

def importskyrad( File ):
    """
    Import some of the SKYRAD.pack data products into the workspace.

    Parameters
    ----------
    File : string
        Filename string, expressed as a relative or absolute path, for the
        current SKYRAD.pack data product.
        Actually, function accepts only PAR and VOL products.
        Although, separate runs are necessary to open each data product.

    Returns
    -------
    Date  : list of datetime objects
        Date/time list of each retrieval, extracted from the Tag line.
    Error : ndarray
        Observation error
    Data  : list of ndarrays
        Contains lists with extracted content depending on the product type.
    """
    Date, Data, Error = [ [], [], [] ];   # l = 0
    infile = open( File, 'r' )
    if not infile.read():
        pass
    else:
        infile.seek(0)
        for line in infile:
            Tag = line.count( ')' )
            S = line.split()
            if Tag > 0:
                Y = int( S[1] );   M =   int( S[2] )
                D = int( S[3] );   H = float( S[4] )
                Date.append( np.array( (Y,M,D,H) ) )
                Error.append( float( S[12] ) )
                # Update retrieval counter when a TAG line is read
                # l += 1

            # Determine from FILE extension the product type (PAR/VOL)
            elif ( Tag == 0 ) & ( File.endswith('par') | File.endswith('vol') ):
                Data.append( [ float(x) for x in S ] )

        # Slice the DATA list in N chunks, where N is the # of retrievals
        L = len(Data)/len(Date)
        Data = [ Data[ i:i+L ] for i in range(0, len(Data), L) ]
        Date = [ dateconvert( Date[k] ) for k in range( len(Date) ) ]

    infile.close()
    return Date, Error, Data

def formatdata( Data, product='par' ):
    """
    Function designed to give a standard format (data blocks) to SKYRAD data
    extracted by the **importskyrad** function

    Parameters
    ----------
    Data  : list of ndarrays
        Contains lists with extracted content depending on the product type.
    product : string, optional
        SKYRAD product type: 'par' or 'vol'

     Returns
    -------
    Depending on the product type, return 2 (vol) or 4 (par) ndarrays containing:

    *par: aerosol optical depth(AOD), single scattering albedo (SSA),
     complex refractive index (CRI), wavelengths (WL) in nanometers
    *vol: particle size distribution (PSD) and relative size classes

    """
    if product == 'par':
        # Initialize the lists to be filled in the loops
        Block1, Block2, Block3 = [ [], [], [] ]
        AOD,    SSA,    RefIdx = [ [], [], [] ]

        for j in range( len(Data) ):
            # Use the number of Wavelengths output by the SKYRAD analysis
            for k in range( len(Data[0]) ):
                Block1.append( Data[j][k][1] )
                Block2.append( Data[j][k][3] )
                Block3.append( [ Data[j][k][l] for l in (4,5) ] )
            # Turn each data block (L rows<->L wavelengths) into an ARRAY
            AOD.append( np.array( Block1 ) )
            SSA.append( np.array( Block2 ) )
            RefIdx.append( np.array( Block3 ) )
            Block1, Block2, Block3 = [ [], [], [] ]
        # Express wavelengths in nanometers
        WL = [ int( Data[0][l][0]*1e3 ) for l in range( len( Data[0] ) ) ]
        # Give as output ARRAYS
        return np.array(AOD), np.array(SSA), np.array(RefIdx), WL

    elif product == 'vol':
        # Initialize the lists to be filled in the loops
        Block = [];     VolDist = []
        for j in range( len(Data) ):
            # Use the number of Wavelengths output by the SKYRAD analysis
            for k in range( len(Data[0]) ):
                Block.append( Data[j][k][0] )

            VolDist.append( np.array( Block ) )
            Block = []

        Sizes = [ Data[0][l][0] for l in range( len( Data[0] ) ) ]
        return np.array(VolDist), np.array(Sizes)

def importsunrad( File ):
    """
    Import to the workspace the SUNRAD.pack data products, raw (DT2) or retri-
    ved (OPT). (WL = wavelengths set of the instrument)
     - From the former we extract the timestamps and the actual measured
    current for each wavelength channel, i.e. only the V1(WL), as raw data are
    arranged as triplets
     - From the OPT retrievals timestamps, AOD(WL), ALF(VIS) and BET(VIS) are
     extracted

    Please consult the SUNRAD.pack documentation for further details.

    Parameters
    ----------
    File : string
        Filename string, expressed as a relative or absolute path, for the
        current SUNRAD.pack data product.
        Actually, function accepts both DT2 and OPT products.
        Although, separate runs are necessary to open each data product.

    Returns
    -------
    Wvlgt : list of floats
        Wavelength channels of the instrument (DT2 file) or subset used for the
        SUNRAD inversion (OPT file), expressed in [micrometers]
    Date : list of datetime objects
        Date/time list of each retrieval, extracted from the Tag line.
    Vout : ndarray
        Depending on the product type, each line contains data of:
         - DT2: measured currents (in Ampere) at the Prede POM photodiode.
         - OPT: estimated AOD at each wavelength (**Wvlgt**) and Angstrom
         Alpha and Beta parameters (interpolated from the VIS channels)
    """
    # Determine product type by the file extension
    Ftype = File[-3:]

    # Load the file header to get some info on what the data file contains
    F = open( File, 'r' )
    Header = F.readline().split();        Header = Header[2:]

    # Header info and timestamp formats are different between the two products
    if Ftype.lower() == 'dt2':
        DFMT = '%y%m%d %H:%M:%S';      Del = ' ' # Column separator: 1 blank
        Nwvl = len(Header);           Step = 3
        Cols = np.arange(2, len(Header), 3)
    elif Ftype.lower() == 'opt':
        DFMT = '%d/%m/%y %H:%M:%S';    Del = '   ' # Column separator: 3 blanks
        Nwvl =  len(Header) - 7;      Step = 1
        Cols = np.arange(1, 1+Nwvl).tolist() + [ Nwvl+4, Nwvl+5 ]

    # Return the actual Wavelength set, expressed in [micrometers]
    Wvlgt = [ float( Header[l][-6:-1] ) for l in range(0,Nwvl,Step) ]

    # Return empty variables if the data product is empty (DT2)
    if not F.readline():
        Date, Vout = [ [], [] ]
        F.close()
    else:
        # Load date/time data as strings, then convert to datetime format
        mdate, mtime = np.loadtxt( File, delimiter=' ', skiprows=1, \
                usecols={0,1}, unpack=True, dtype='string' )
        if isinstance( mdate, np.ndarray ):
            Date = [ datetime.strptime(mdate[l] + ' ' + mtime[l],  DFMT) \
                    for l in range(len(mdate)) ]
        elif isinstance( mdate, str ):
            Date = [ datetime.strptime(mdate + ' ' + mtime,  DFMT) ]

        # Load Vout data, using only the first measurement of the triplets
        Vout = np.loadtxt( File, delimiter=Del, skiprows=1, usecols=Cols,\
                unpack=False, dtype='float' )

    return Wvlgt, Date, Vout
