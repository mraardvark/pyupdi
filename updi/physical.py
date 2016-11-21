
import logging
import time
import serial

import updi.constants as constants

class UpdiPhysical(object):
    """
        PDI physical driver using a given COM port at a given baud
    """

    def __init__(self, port, baud=100000):
        """
            Initialise the COM port
        """

        self.logger = logging.getLogger("phy")

        # Inter-byte delay
        self.ibdly = 0.0001
        self.port = port
        self.baud = baud
        self.ser = None
        self.initialise_serial(self.port, self.baud)

    def initialise_serial(self, port, baud):
        """
            Standard COM port initialisation
        """

        self.logger.info("Opening {} at {} baud".format(port, baud))
        self.ser = serial.Serial(port, baud, parity=serial.PARITY_EVEN, timeout=1)

    def send_double_break(self):
        """
            Sends a double break to reset the UPDI port
            BREAK is actually just a slower zero frame
            A double break is guaranteed to push the UPDI state
            machine into a known state, albeit rather brutally
        """

        self.logger.info("Sending double break")

        # Re-init at a lower baud
        self.ser.close()
        temporary_serial = serial.Serial(self.port, 1000)

        # Send a break
        temporary_serial.write([constants.UPDI_BREAK])

        # Wait
        time.sleep(0.05)

        # Send another
        temporary_serial.write([constants.UPDI_BREAK])
        time.sleep(0.001)

        # Re-init at the real baud
        temporary_serial.close()
        self.initialise_serial(self.port, self.baud)

    def send(self, command):
        """
            Sends a char array to UPDI with inter-byte delay
            Note that the byte will echo back
        """
        self.logger.info("send: {}".format(command))

        for character in command:

            # Send
            self.ser.write([character])

            # Echo
            self.ser.read()

            # Inter-byte delay
            time.sleep(self.ibdly)

    def receive(self, size):
        """
            Receives a frame of a known number of chars from UPDI
        """
        response = []
        timeout = 1

        # For each byte
        while size and timeout:

            # Read
            character = self.ser.read()

            # Anything in?
            if character != "":
                response.append(ord(character))
                size -= 1
            else:
                timeout -= 1

        self.logger.info("receive: {}".format(response))
        return response

    def sib(self):
        """
            System information block is just a string coming back from a SIB command
        """
        self.send([
            constants.UPDI_PHY_SYNC,
            constants.UPDI_KEY | constants.UPDI_KEY_SIB | constants.UPDI_SIB_16BYTES])
        return self.ser.readline()

    def __del__(self):
        if self.ser:
            self.logger.info("Closing {}".format(self.port))
            self.ser.close()
