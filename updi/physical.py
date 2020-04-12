"""
    Serial driver for UPDI stack
"""
import logging
import time
import serial

import updi.constants as constants


class UpdiPhysical(object):
    """
        PDI physical driver using a given COM port at a given baud
    """

    def __init__(self, port, baud=115200):
        """
            Initialise the COM port
        """

        self.logger = logging.getLogger("phy")
        self.port = port
        self.baud = baud
        self.ser = None
        self.initialise_serial(self.port, self.baud)
        # send an initial break as handshake
        self.send([constants.UPDI_BREAK])

    def initialise_serial(self, port, baud):
        """
            Standard COM port initialisation
        """
        self.logger.info("Opening {} at {} baud".format(port, baud))
        self.ser = serial.Serial(port, baud, parity=serial.PARITY_EVEN, timeout=1, stopbits=serial.STOPBITS_TWO)

    def _loginfo(self, msg, data):
        if data and isinstance(data[0], str):
            i_data = [ord(x) for x in data]
        else:
            i_data = data
        data_str = "[" + ", ".join([hex(x) for x in i_data]) + "]"
        self.logger.info(msg + ' : ' + data_str)

    def send_double_break(self):
        """
            Sends a double break to reset the UPDI port
            BREAK is actually just a slower zero frame
            A double break is guaranteed to push the UPDI state
            machine into a known state, albeit rather brutally
        """

        self.logger.info("Sending double break")

        # Re-init at a lower baud
        # At 300 bauds, the break character will pull the line low for 30ms
        # Which is slightly above the recommended 24.6ms
        self.ser.close()

        temporary_serial = serial.Serial(self.port, 300, stopbits=serial.STOPBITS_ONE, timeout=1)

        # Send two break characters, with 1 stop bit in between
        temporary_serial.write([constants.UPDI_BREAK, constants.UPDI_BREAK])

        # Wait for the double break end
        temporary_serial.read(2)

        # Re-init at the real baud
        temporary_serial.close()
        self.initialise_serial(self.port, self.baud)

    def send(self, command):
        """
            Sends a char array to UPDI with NO inter-byte delay
            Note that the byte will echo back
        """
        self.logger.info("send %d bytes", len(command))
        self._loginfo("data: ", command)

        self.ser.write(command)
        # it will echo back.
        echo = self.ser.read(len(command))

    def receive(self, size):
        """
            Receives a frame of a known number of chars from UPDI
        """
        response = bytearray()
        timeout = 1

        # For each byte
        while size and timeout:

            # Read
            character = self.ser.read()

            # Anything in?
            if character:
                response.append(ord(character))
                size -= 1
            else:
                timeout -= 1

        self._loginfo("receive", response)
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
            self.logger.info("Closing port '%s'", self.port)
            self.ser.close()
