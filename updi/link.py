
import logging

from updi.physical import UpdiPhysical
import updi.constants as constants

class UpdiDatalink(object):
    """
        UPDI data link class handles the UPDI data protocol within the device
    """

    def __init__(self, comport, baud):
        self.logger = logging.getLogger("link")

        # Create a UPDI physical connection
        self.updi_phy = UpdiPhysical(comport, baud)

        # Initialise
        self.init()

        # Check
        if not self.check():
            # Send double break if all is not well, and re-check
            self.updi_phy.send_double_break()
            self.init()
            if not self.check():
                raise Exception("UPDI initialisation failed")

    def init(self):
        """
            Set the inter-byte delay bit and disable collision detection
        """
        self.stcs(constants.UPDI_CS_CTRLB, 1 << constants.UPDI_CTRLB_CCDETDIS_BIT)
        self.stcs(constants.UPDI_CS_CTRLA, 1 << constants.UPDI_CTRLA_IBDLY_BIT)

    def check(self):
        """
            Check UPDI by loading CS STATUSA
        """
        if self.ldcs(constants.UPDI_CS_STATUSA) != 0:
            self.logger.info("UPDI init OK")
            return True
        self.logger.info("UPDI not OK - reinitialisation required")
        return False

    def ldcs(self, address):
        """
            Load data from Control/Status space
        """
        self.logger.info("LDCS from 0x{0:02X}".format(address))
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_LDCS | (address & 0x0F)])
        response = self.updi_phy.receive(1)
        if len(response) != 1:
            # Todo - flag error
            return 0x00
        return response[0]

    def stcs(self, address, value):
        """
            Store a value to Control/Status space
        """
        self.logger.info("STCS to 0x{0:04X}".format(address))
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_STCS | (address & 0x0F), value])

    def ld(self, address):
        """
            Load a single byte direct from a 16-bit address
        """
        self.logger.info("LD from 0x{0:04X}".format(address))
        self.updi_phy.send(
            [constants.UPDI_PHY_SYNC, constants.UPDI_LDS | constants.UPDI_ADDRESS_16 | constants.UPDI_DATA_8, address & 0xFF, (address >> 8) & 0xFF])
        return self.updi_phy.receive(1)[0]

    def ld16(self, address):
        """
            Load a 16-bit word directly from a 16-bit address
        """
        self.logger.info("LD from 0x{0:04X}".format(address))
        self.updi_phy.send(
            [constants.UPDI_PHY_SYNC, constants.UPDI_LDS | constants.constants.UPDI_ADDRESS_16 | constants.UPDI_DATA_16, address & 0xFF, (address >> 8) & 0xFF])
        return self.updi_phy.receive(2)

    def st(self, address, value):
        """
            Store a single byte value directly to a 16-bit address
        """
        self.logger.info("ST to 0x{0:04X}".format(address))
        self.updi_phy.send(
            [constants.UPDI_PHY_SYNC, constants.UPDI_STS | constants.UPDI_ADDRESS_16 | constants.UPDI_DATA_8, address & 0xFF, (address >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("Error with st")

        self.updi_phy.send([value & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("Error with st")

    def st16(self, address, value):
        """
            Store a 16-bit word value directly to a 16-bit address
        """
        self.logger.info("ST to 0x{0:04X}".format(address))
        self.updi_phy.send(
            [constants.UPDI_PHY_SYNC, constants.UPDI_STS | constants.UPDI_ADDRESS_16 | constants.UPDI_DATA_16, address & 0xFF, (address >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("Error with st")

        self.updi_phy.send([value & 0xFF, (value >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("Error with st")

    def ld_ptr_inc(self, size):
        """
            Loads a number of bytes from the pointer location with pointer post-increment
        """
        self.logger.info("LD8 from ptr++")
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_LD | constants.UPDI_PTR_INC | constants.UPDI_DATA_8])
        return self.updi_phy.receive(size)

    def ld_ptr_inc16(self, words):
        """
            Load a 16-bit word value from the pointer location with pointer post-increment
        """
        self.logger.info("LD16 from ptr++")
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_LD | constants.UPDI_PTR_INC | constants.UPDI_DATA_16])
        return self.updi_phy.receive(words << 1)

    def st_ptr(self, address):
        """
            Set the pointer location
        """
        self.logger.info("ST to ptr")
        self.updi_phy.send(
            [constants.UPDI_PHY_SYNC, constants.UPDI_ST | constants.UPDI_PTR_ADDRESS | constants.UPDI_DATA_16, address & 0xFF, (address >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("Error with st_ptr")

    def st_ptr_inc(self, data):
        """
            Store data to the pointer location with pointer post-increment
        """
        self.logger.info("ST8 to *ptr++")
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_ST | constants.UPDI_PTR_INC | constants.UPDI_DATA_8, data[0]])
        response = self.updi_phy.receive(1)

        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("ACK error with st_ptr_inc")

        n = 1
        while n < len(data):
            self.updi_phy.send([data[n]])
            response = self.updi_phy.receive(1)

            if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
                raise Exception("Error with st_ptr_inc")
            n += 1

    def st_ptr_inc16(self, data):
        """
            Store a 16-bit word value to the pointer location with pointer post-increment
        """
        self.logger.info("ST16 to *ptr++")
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_ST | constants.UPDI_PTR_INC | constants.UPDI_DATA_16, data[0], data[1]])
        response = self.updi_phy.receive(1)

        if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
            raise Exception("ACK error with st_ptr_inc16")

        n = 2
        while n < len(data):
            self.updi_phy.send([data[n], data[n + 1]])
            response = self.updi_phy.receive(1)

            if len(response) != 1 or response[0] != constants.UPDI_PHY_ACK:
                raise Exception("Error with st_ptr_inc16")
            n += 2

    def repeat(self, repeats):
        """
            Store a value to the repeat counter
        """
        self.logger.info("Repeat {0:d}".format(repeats))
        repeats -= 1
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_REPEAT | constants.UPDI_REPEAT_WORD, repeats & 0xFF, (repeats >> 8) & 0xFF])

    def read_sib(self):
        """
            Read the SIB
        """
        return self.updi_phy.sib()

    def key(self, size, key):
        """
            Write a key
        """
        self.logger.info("Writing key")
        if len(key) != 8 << size:
            raise Exception("Invalid KEY length!")
        self.updi_phy.send([constants.UPDI_PHY_SYNC, constants.UPDI_KEY | constants.UPDI_KEY_KEY | size])
        self.updi_phy.send(list(reversed(list(key))))

