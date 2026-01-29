import serial, time, sys
import serial.tools.list_ports

# --------------- SERIAL VARIABLES
ser_Arduino = None
ARDUINO_PORT1 = "COM3"
ARDUINO_PORT2 = "COM5"
ARDUINO_PORT3 = "COM9"


# --------------- SERIAL MIT SERVO
def open_first_available(baud=115200, timeout=2, ports=(ARDUINO_PORT1, ARDUINO_PORT2, ARDUINO_PORT3)):
    last = None
    print(serial_ports())
    for p in ports:
        try:
            ser = serial.Serial(p, baudrate=baud, timeout=timeout)
            print(f"[SERIAL] Verbunden: {p}")
            time.sleep(1)
            return ser
        except Exception as e:
            last = e
    raise RuntimeError(f"Kein Port aus {ports} verfügbar: {last}")

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = list(serial.tools.list_ports.comports())
        #ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for p in ports:
        try:
            print(p)
            #s = serial.Serial(port)
            #s.close()
            #result.append(port)
            
        except (OSError, serial.SerialException):
            pass
    return result

"""
def send_modes(ends=None, elec=None, noise=None, linear=None):
    try:
        ser_Arduino = open_first_available(baud=115200, timeout=5)
        if ends:
            ser_Arduino.write(b"ENDS\n")
            time.sleep(0.2)
        if elec:
            ser_Arduino.write(b"ELEC\n")
            time.sleep(0.2)
        if noise:
            ser_Arduino.write(b"NOISE\n")
            time.sleep(0.2)
        if linear:
            ser_Arduino.write(b"LINEAR\n")
            time.sleep(0.2)


    except Exception as e:
        print("Serial Fehler bei Modes: ", e)
    
    ser_Arduino.close()"""