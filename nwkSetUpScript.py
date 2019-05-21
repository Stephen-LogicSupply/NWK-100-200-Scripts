import serial
import time
import logging
from serial.tools import list_ports
import sys

logging.basicConfig(filename='4G_setup.log', level=logging.DEBUG)
_logger = logging.getLogger("nwksetup")

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

_logger.addHandler(ch)


def read_lines(ser):
    """ 
    Function that reads two lines

    ::param ser::  Com Object for 4G Modem
    ::type ser:: Open serial.Serial com object

    ::returns:: None
    """
    for loop in range(0, 2):
        time.sleep(1)
        read_line = str(ser.readline())
        _logger.info(read_line)


def find_port():
    """
    Finds if the inserted modem is an NWK100 or NWK200, and gets its port

    ::returns:: modem, system

    ::param modem:: The COM port the modem is attached to
    ::type modem:: string variable

    ::param system::  The name of the detected modem type
    ::type system:: string variable
    """
    coms = []
    open_ports = []
    system = ""

    native_com_list = list_ports.comports(True)

    # This for statement identifies if the card is an NWK100 or NWK200
    for com in native_com_list:
        _logger.debug("%s found", com)
        if "X7 LTE-A NMEA Port" in com.description:
            system = 1
        coms.append(com.device)

    if system == 1:
        system = "nwk200"
        _logger.info("nwk200 card found.")
    else:
        system = "nwk100"
        _logger.info("nwk100 card found. NOTE: If user is expecting an nwk200 card then system has failed detection.")

    # Search through potential port names for open COM ports
    for port in range(1, 256):
        com_check = "COM" + str(port)
        try:
            s = serial.Serial(com_check)
            s.close()
            open_ports.append(com_check)
            _logger.debug("%s port is populated", com_check)
        except (OSError, serial.SerialException):
            _logger.debug("%s port is not populated", com_check)
        pass

    modem = list(set(open_ports) - set(coms))

    # Find the com port that has the modem
    if len(modem) > 1:
        for test_port in modem:
            test_ser = open_serial_connection(test_port)
            test_ser.write(b"ATE1\r\n")
            if str(test_ser.readline()) == str(b'ATE1\r\r\n'):
                modem[0] = test_port

    return modem[0], system


def nwk100_setup(ser):
    """
    Send the needed commands to set up the nwk100 modem
    Command reference found here: http://apps.richardsonrfpd.com/Mktg/Tech-Hub/pdfs/StandardATCommands.pdf

    ::param ser:: Com Object for 4G Modem
    ::type ser:: Open serial.Serial com object

    ::returns:: None
    """
    ser.write(b"ATE1\r\n")
    read_lines(ser)

    ser.write(b"AT+UBMCONF=1\r\n")
    read_lines(ser)

    ser.write(b"AT+CFUN=4\r\n")
    read_lines(ser)

    ser.write(b'AT+CGDCONT=1,"IP","broadband"\r\n')
    read_lines(ser)

    ser.write(b'AT+UCGDFLT=1,"IP","broadband"\r\n')
    read_lines(ser)

    ser.write(b"AT+CFUN=1\r\n")
    read_lines(ser)
    read_lines(ser)
    time.sleep(5)

    ser.write(b"AT+CPIN?\r\n")
    read_lines(ser)
    read_lines(ser)

    ser.write(b"AT+COPS?\r\n")
    read_lines(ser)
    read_lines(ser)

    ser.write(b'AT+CGACT=1,1')
    read_lines(ser)
    read_lines(ser)
    read_lines(ser)

    ser.close(ser)


def nwk200_setup(ser):
    """
    Send the needed commands to set up the nwk200 modem
    Command reference found here: https://source.sierrawireless.com/resources/airprime/minicard/74xx/4117727-airprime-em
    74xx-mc74xx-at-command-reference/

    ::param ser:: Com Object for 4G Modem
    ::type ser:: Open serial.Serial com object

    ::returns:: None
    """

    provider = ""
    while True:
        selection = input("Select a provider:\n1.)AT&T\n2.)Verizon\n3.)Exit Setup")

        if selection == str(1):
            provider = "ATT"
            _logger.info("User selected: ATT")
            break
        elif selection == str(2):
            _logger.info("User selected: VERIZON")
            provider = "VERIZON"
            break
        elif selection == str(3):
            _logger.info("Configuration terminated by user")
            sys.exit(0)

    ser.write(b"ATE1\r\n")
    read_lines(ser)

    ser.write(b'AT!ENTERCND="A710"\r\n')
    read_lines(ser)

    ser.write(b'AT!USBCOMP=1,1,100D\r\n')
    read_lines(ser)

    ser.write(b'AT!IMPREF="' + provider + b'"\r\n')
    read_lines(ser)

    ser.write(b'AT!RESET\r\n')
    ser.close(ser)


def open_serial_connection(port):
    """
    Opens the serial connection and establishes parameters

    ::param port:: COM port for the modem
    ::type port:: String variable

    ::returns:: ser

    ::param ser:: Com Object for 4G Modem
    ::type ser:: Open serial.Serial com object
    """
    _logger.info("Setting parameters for port: %s", str(port))
    ser = serial.Serial(port)

    ser.close()
    ser.open()
    ser.baudrate = 115200
    ser.bytesize = 8
    ser.Parity = 'N'
    ser.stopbits = 1
    ser.timeout = 15

    return ser


def main():

    info = find_port()

    card = info[1]
    port = info[0]

    ser = open_serial_connection(port)

    _logger.info('Modem Port : %s', ser.name)
    _logger.info('Device Opening : %s', str(ser.isOpen()))

    if card == "nwk100":
        nwk100_setup(ser)
    elif card == "nwk200":
        nwk200_setup(ser)
    else:
        _logger.warning('No 4G modem detected. Please ensure a 4G modem is installed in your machine.')

    print("Setup complete!")


if __name__ == "__main__":
    main()
