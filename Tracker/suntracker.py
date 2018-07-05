# Libraries for operating the ADC from the Rpi
import Adafruit_ADS1x15
import RPi.GPIO as GPIO
# Import our SRS libraries including SunPosition function
from SRSpci import SRStools as SRS
from datetime import datetime
import time
# Read GPS strings from the serial port
import serial

#%% GPS parsing functions
def datetime_gps(gpsstring):
    '''Parse Date and Time (UTC) from a GPS NMEA-0183 RMC type sentence.

    Parameters
    ---------
    gpsstring: str
        String read from the serial-attached GPS device, formatted with the
        NMEA-0183 standard.

    Returns
    -------
    Date: datetime
        Full date and time (UTC) reading from the GPS RMC sentence.
    '''
    S = gpsstring.split(',')
    if S[0] == '$GPRMC':
        Hgps = S[1]
        Dgps = S[9]
        return  datetime.strptime( Dgps+Hgps, '%d%m%y%H%M%S.%f' )
    else:
        pass

def position_gps(gpsstring):
    '''Parse antenna position from a GPS NMEA-0183 GGA type sentence.

    Parameters
    ---------
    gpsstring: str
        String read from the serial-attached GPS device, formatted with the
        NMEA-0183 standard.

    Returns
    -------
    Site_position: list of floats
        Latitude, Longitude and Altitude (m asl) reading from the GPS GGA sentence.
    '''
    S = gpsstring.split(',')
    if S[0] == '$GPGGA':
        # Return a list containing: Latitude, Longitude, Height (m asl)
        return [ float(S[2]), float(S[4]), float(S[9]) ]
    else:
        pass

#%% Tracker motors functions
def setStep(motor, w1, w2, w3, w4):
	if (motor  == "RA"):
		GPIO.output(RA[0], w1)
		GPIO.output(RA[1], w2)
		GPIO.output(RA[2], w3)
		GPIO.output(RA[3], w4)
	elif (motor == "DEC"):
		GPIO.output(DEC[0], w1)
		GPIO.output(DEC[1], w2)
		GPIO.output(DEC[2], w3)
		GPIO.output(DEC[3], w4)

def forward(motor, delay, steps):
    '''Move one of the tracker's motors (''RA'' or ''DEC'') forward by STEPS,
    waiting a certain DELAY between each movement.'''
    for i in range(0, steps):
        setStep(motor, 1, 1, 0, 0);  time.sleep(delay)
        setStep(motor, 0, 1, 1, 0);  time.sleep(delay)
        setStep(motor, 0, 0, 1, 1);  time.sleep(delay)
        setStep(motor, 1, 0, 0, 1);  time.sleep(delay)
    for pin in RA:
        GPIO.output(pin, False)
    for pin in DEC:
        GPIO.output(pin, False)

def backward(motor, delay, steps):
    '''Move one of the tracker's motors (''RA'' or ''DEC'') backwards by STEPS,
    waiting a certain DELAY between each movement.'''
    for i in range(0, steps):
        setStep(motor, 1, 0, 0, 1);  time.sleep(delay)
        setStep(motor, 0, 0, 1, 1);  time.sleep(delay)
        setStep(motor, 0, 1, 1, 0);  time.sleep(delay)
        setStep(motor, 1, 1, 0, 0);  time.sleep(delay)
    for pin in RA:
        GPIO.output(pin, False)
    for pin in DEC:
        GPIO.output(pin, False)

#%% Sensor functions
def biascorrection( value, gain):
    '''Define the bias level for the photodiode, depending on the GAIN value.'''
    if   gain == 2./3.:
        coeffs = [ 4, 23, -4, 29 ]
    elif gain == 1:
        coeffs = [ 6, 34, -7, 43 ]
    elif gain == 2:
        coeffs = [ 11, 67, -14, 86 ]
    elif gain == 4:
        coeffs = [ 22, 133, -28, 171 ]
    elif gain == 8:
        coeffs = [ 44, 265, -57, 341 ]
    elif gain == 16:
        coeffs = [ 87, 531, -114, 684 ]
    else:
        print( "GAIN value not valid" )
    return [ value[c] + coeffs[c] for c in range(4) ]

#%%___FUNZIONI MOVIMENTO DI UN INTERVALLO___#
fromAngleToStepsRA  = 543.7  # 360 degrees=155 turns of handle
fromAngleToStepsDEC = 173.6  # 360 degrees=62 turns of handle + ingranaggio riduttore
def moveOfInterval(initDEC, initRA, moveDEC, moveRA):
    '''
    Move the tracker's head from an initial (DEC, RA) position to a new one
    (DEC + d, RA + r). '''
    global turnDn, turnRt, swing
    #1 grado= 620 cicli
    delay_time = 0.005
    print("Moving ", moveDEC, "degrees in DEC and ", moveRA, " degrees in RA")
    initDEC = initDEC + moveDEC
    initRA  = initRA  + moveRA

    if(moveDEC > 0):
        if(turnDn == 0):
            nstep  = int( abs(fromAngleToStepsDEC * moveDEC) )
        else:
            nstep  = int( abs(fromAngleToStepsDEC * moveDEC) + swing)
            turnDn = 0
        print("Rising by " + str(nstep) + " steps")
        print("DEC minimum moving time: " + str(4 * delay_time * nstep) + " s")
        backward("DEC",delay_time,nstep)

    elif (moveDEC < 0):
        moveDEC = -moveDEC
        if(turnDn == 1):
            nstep  = int( abs(fromAngleToStepsDEC * moveDEC) )
        else:
            nstep  = int( abs(fromAngleToStepsDEC * moveDEC) + swing)
            turnDn = 1
        print("Moving down by " + str(nstep) + " steps")
        print("DEC minimum moving time: " + str(4 * delay_time * nstep) + " s")
        forward("DEC", delay_time, nstep)
    print("\nDEC movement terminated.\n")

    if moveRA > 0:
        if(turnRt == 0):
            nstep  = int( abs(fromAngleToStepsRA * moveRA) )
        else:
            nstep  = int( abs(fromAngleToStepsRA * moveRA) + swing )
            turnRt = 0
        print("Clockwise movement by " + str(nstep) + " steps")
        print("RA minimum moving time: " + str(4 * delay_time * nstep) + " s")
        backward("RA", delay_time, nstep)

    elif moveRA < 0:
        moveRA = -moveRA
        if(turnRt == 1):
            nstep  = int( abs(fromAngleToStepsRA*moveRA) )
        else:
            nstep  = int( abs(fromAngleToStepsRA * moveRA) + swing )
            turnRt = 1
        print("Clockwise movement by " + str(nstep) + " steps")
        print("RA minimum moving time: " + str(4 * delay_time * nstep) + " s")
        forward("RA", delay_time, nstep)
    print ("\nRA movement terminated.\n")

    print("New position: DEC angle=" + str(initDEC) + \
         " deg, RA angle=" + str(initRA) + " deg.")
    return initDEC, initRA


def moveToPosition(initDEC,initRA,finalDEC,finalRA):
  diffDEC=finalDEC-initDEC
  diffRA=finalRA-initRA
  return moveOfInterval(initDEC,initRA,diffDEC,diffRA)

#%% SETUP MOTORI - SENSORE
adc = Adafruit_ADS1x15.ADS1115()
GAIN = 2
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
# Identify GPIO pins for the RA movement (right-left or vv)
RA  = [31, 33, 35, 37]
# Identify GPIO pins for the DEC movement (up-down or vv)
DEC = [32, 36, 38, 40]

qcdstep = 20
qcdelay = 0.01

for pin in RA:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin,False)
for pin in DEC:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin,False)

vertical   = 0
horizontal = 0
tolerance  = 100

#variabili per risolvere il gioco dei motori quando invertono il giro
turnDn = 0
turnRt = 0
swing = 19

#____RECUPERO SEGNALE GPS____#
ser=serial.Serial('/dev/ttyACM0')
print('Searching for GPS signal. Beginning to extract information... ')

# Initial setup: find site location through GPS data
Site = []
while not Site:
    try:
        string = ser.readline()
        string = string.decode("utf-8")
        Site = position_gps(string)
        print('Got site coordinates.')
    except:
        print('Unable to reach a stable GPS connection. Retrying in 10 sec.')
        time.sleep(10)

# Initial setup: get date/time (UT) through GPS data
Date = []
while not Date:
    try:
        RMC_line = ser.readline()
        RMC_line = RMC_line.decode("utf-8").split(",")
        Date = datetime_gps(RMC_line)
        print('Got GPS date and time (UTC)')
    except:
        print('Unable to reach a stable GPS connection. Retrying in 10 sec.')
        time.sleep(10)

SZA, Azim, SunEarthDst = SRS.sunPosition(Date, Site[:2], Height=Site[2])
print( "Sun Altitude (deg): ", (90.-SZA), "; Azimuth (deg): ", Azim )

print("Immetti puntamento iniziale della montatura (3 deg precisione)")
altit_deg=float(input("Declinazione (Orizzonte=0,Zenit=90): "))
azim_deg=float(input("Ascensione retta (N=0,E=90,S=180,O=270): "))

#%% TRACKER MOVEMENT PROGRAM START
print("Moving from initial: DEC ",altit_deg,", RA ",azim_deg,\
    "\nto estimated Sun pos.: DEC ",90.-SZA,", RA ",Azim)
altit_deg, azim_deg = moveToPosition(altit_deg, azim_deg, 90.-SZA, Azim)
print('Currently reading QPD values: press Ctrl+c to stop program execution.')
print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*range(4)))
print('-' * 37)
# Main loop.
try:
  while True:
    # Read all the ADC channel values in a list.
    values = [0]*4
    for i in range(4):
      try:
        values[i] = adc.read_adc(i, gain=GAIN)
      except IOError:
        pass
        print ("I/O Error") # Take into account sporadic ADC problems
    # Correct bias on voltage readings, applying a gain
    values = biascorrection( values, GAIN )
    vertical   = (values[0] + values[2]) - (values[1] + values[3])
    horizontal = (values[1] + values[2]) - (values[0] + values[3])
    total_rad  = sum(values)
    print( '| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values) + "vert " +\
        str(vertical) + ", horiz " + str(horizontal) + ", tot " + str(total_rad) )

    # Are we seeing Sun? Yes -> fine movement, No -> follow ephemerides
    nstep = 0
    if total_rad < 3000:
      print ("Can't see the Sun, following ephemerides.")
      d = datetime.datetime.now()
      SZA, Azim = SRS.sunPosition(Date, Site[:2], Height=Site[2])[0:2]
      print( "Moving from current: DEC ", altit_deg, "RA ", azim_deg,\
          "\nto estimated Sun position: DEC ", 90.-SZA, "RA ", Azim )
      altit_deg, azim_deg =\
          moveToPosition( altit_deg, azim_deg, 90.-SZA, Azim )
      time.sleep(10)
    else:
      if vertical > tolerance:
        if turnDn == 1:
          nstep = min( 50, int(abs(qcdstep*vertical/tolerance)/8) )
        else:
          nstep=min(50,int(abs(qcdstep*vertical/tolerance)/8+swing))
          turnDn=1
        print ("scendo "+str(nstep)+" step,",float(nstep/fromAngleToStepsDEC),"gradi")
        forward("DEC",qcdelay,nstep)
        altit_deg=altit_deg-float(nstep/fromAngleToStepsDEC)
        print("Movimento fine DEC-")

      elif (vertical<-tolerance):
        if(turnDn==0):
          nstep=min(50,int(abs(qcdstep*vertical/tolerance)/8))
        else:
          nstep=min(50,int(abs(qcdstep*vertical/tolerance)/8+swing))
          turnDn=0
        print("salgo " + str(nstep) + " step,", float(nstep/fromAngleToStepsDEC), "gradi")
        backward("DEC",qcdelay,nstep)
        altit_deg=altit_deg-float(nstep/fromAngleToStepsDEC)
        print("Movimento fine DEC+")

      #movimento orizzontale
      if (horizontal>tolerance):
        if(turnRt==0):
          nstep=min(50,int(abs(qcdstep*horizontal/tolerance)/4))
        else:
          nstep=min(50,int(abs(qcdstep*horizontal/tolerance)/4+swing))
          turnRt=0
        print("antiorario " + str(nstep) + " step,", float(nstep/fromAngleToStepsRA), "gradi")
        forward("RA", qcdelay, nstep)
        azim_deg=azim_deg-float(nstep/fromAngleToStepsRA)
        print("Movimento fine RA-")

      elif (horizontal<-tolerance):
        if(turnRt==1):
          nstep=min(50,int(abs(qcdstep*horizontal/tolerance)/4))
        else:
          nstep=min(50,int(abs(qcdstep*horizontal/tolerance)/4+swing))
          turnRt=1
        print ("orario "+str(nstep)+" step,",float(nstep/fromAngleToStepsRA),"gradi")
        backward("RA", qcdelay, abs(nstep))
        azim_deg=azim_deg+float(nstep/fromAngleToStepsRA)
        print("Movimento fine RA+")
      else:
        #Sole centrato, le coord della montatura coincidono con quelle del Sole
        d = datetime.datetime.now()
        SZA, Azim = SRS.sunPosition(Date, Site[:2], Height=Site[2])[0:2]
        #print ("Scostamento DEC:",altit_deg-sun_altit_deg,"RA",azim_deg-sun_azim_deg)
        altit_deg = 90. - SZA
        azim_deg  = Azim
        #print("Coord telescopio",altit_deg,"DEC",azim_deg,"RA")
        time.sleep(0.5)

finally:
  GPIO.cleanup()
