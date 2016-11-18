"""
Copyright (c) 2016 Atmel Corporation, a wholly owned subsidiary of Microchip Technology Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
pyupdi is a Python utility for programming AVR devices with UPDI interface
  using a standard TTL serial port.

  Connect RX and TX together with a suitable resistor and connect this node
  to the UPDI pin of the AVR device.

  Be sure to connect a common ground, and use a TTL serial adapter running at
   the same voltage as the AVR device.

                        Vcc                     Vcc
                        +-+                     +-+
                         |                       |
 +---------------------+ |                       | +--------------------+
 | Serial port         +-+                       +-+  AVR device        |
 |                     |      +----------+         |                    |
 |                  TX +------+   4k7    +---------+ UPDI               |
 |                     |      +----------+    |    |                    |
 |                     |                      |    |                    |
 |                  RX +----------------------+    |                    |
 |                     |                           |                    |
 |                     +--+                     +--+                    |
 +---------------------+  |                     |  +--------------------+
                         +-+                   +-+
                         GND                   GND

"""

import serial
import time

# UPDI commands and control definitions
UPDI_BREAK = 0x00

UPDI_LDS = 0x00
UPDI_STS = 0x40
UPDI_LD = 0x20
UPDI_ST = 0x60
UPDI_LDCS = 0x80
UPDI_STCS = 0xC0
UPDI_REPEAT = 0xA0
UPDI_KEY = 0xE0

UPDI_PTR = 0x00
UPDI_PTR_INC = 0x04
UPDI_PTR_ADDRESS = 0x08

UPDI_ADDRESS_8 = 0x00
UPDI_ADDRESS_16 = 0x04

UPDI_DATA_8 = 0x00
UPDI_DATA_16 = 0x01

UPDI_KEY_SIB = 0x04
UPDI_KEY_KEY = 0x00

UPDI_KEY_64 = 0x00
UPDI_KEY_128 = 0x01

UPDI_SIB_8BYTES = UPDI_KEY_64
UPDI_SIB_16BYTES = UPDI_KEY_128

UPDI_REPEAT_BYTE = 0x00
UPDI_REPEAT_WORD = 0x01

UPDI_PHY_SYNC = 0x55
UPDI_PHY_ACK = 0x40

UPDI_MAX_REPEAT_SIZE = 0xFF

# CS and ASI Register Address map
UPDI_CS_STATUSA = 0x00
UPDI_CS_STATUSB = 0x01
UPDI_CS_CTRLA = 0x02
UPDI_CS_CTRLB = 0x03
UPDI_ASI_KEY_STATUS = 0x07
UPDI_ASI_RESET_REQ = 0x08
UPDI_ASI_CTRLA = 0x09
UPDI_ASI_SYS_CTRLA = 0x0A
UPDI_ASI_SYS_STATUS = 0x0B
UPDI_ASI_CRC_STATUS = 0x0C

UPDI_CTRLA_IBDLY_BIT = 7
UPDI_CTRLB_CCDETDIS_BIT = 3
UPDI_CTRLB_UPDIDIS_BIT = 2

UPDI_KEY_NVM = "NVMProg "
UPDI_KEY_CHIPERASE = "NVMErase"

UPDI_ASI_STATUSA_REVID = 4
UPDI_ASI_STATUSB_PESIG = 0

UPDI_ASI_KEY_STATUS_CHIPERASE = 3
UPDI_ASI_KEY_STATUS_NVMPROG = 4
UPDI_ASI_KEY_STATUS_UROWWRITE = 5

UPDI_ASI_SYS_STATUS_RSTSYS = 5
UPDI_ASI_SYS_STATUS_INSLEEP = 4
UPDI_ASI_SYS_STATUS_NVMPROG = 3
UPDI_ASI_SYS_STATUS_UROWPROG = 2
UPDI_ASI_SYS_STATUS_LOCKSTATUS = 0

UPDI_RESET_REQ_VALUE = 0x59

# FLASH CONTROLLER
UPDI_NVMCTRL_CTRLA = 0x00
UPDI_NVMCTRL_CTRLB = 0x01
UPDI_NVMCTRL_STATUS = 0x02
UPDI_NVMCTRL_INTCTRL = 0x03
UPDI_NVMCTRL_INTFLAGS = 0x04
UPDI_NVMCTRL_DATAL = 0x06
UPDI_NVMCTRL_DATAH = 0x07
UPDI_NVMCTRL_ADDRL = 0x08
UPDI_NVMCTRL_ADDRH = 0x09

# CTRLA
UPDI_NVMCTRL_CTRLA_NOP = 0x00
UPDI_NVMCTRL_CTRLA_WRITE_PAGE = 0x01
UPDI_NVMCTRL_CTRLA_ERASE_PAGE = 0x02
UPDI_NVMCTRL_CTRLA_ERASE_WRITE_PAGE = 0x03
UPDI_NVMCTRL_CTRLA_PAGE_BUFFER_CLR = 0x04
UPDI_NVMCTRL_CTRLA_CHIP_ERASE = 0x05
UPDI_NVMCTRL_CTRLA_ERASE_EEPROM = 0x06
UPDI_NVMCTRL_CTRLA_WRITE_FUSE = 0x07

UPDI_NVM_STATUS_WRITE_ERROR = 2
UPDI_NVM_STATUS_EEPROM_BUSY = 1
UPDI_NVM_STATUS_FLASH_BUSY = 0


class UpdiPhysical:
    """
        PDI physical driver using a given COM port at a given baud
    """

    def __init__(self, port, baud=100000, verbose=0):
        """
            Initialise the COM port
        """
        self.VERBOSE_THRESHOLD = 4
        self.verbose = verbose
        self.notify("Constructor")

        # Inter-byte delay
        self.ibdly = 0.0001
        self.port = port
        self.baud = baud
        self.ser = None
        self.initialise_serial(self.port, self.baud)

    def notify(self, message):
        if self.verbose >= self.VERBOSE_THRESHOLD:
            print "      PHY:{}".format(message)

    def initialise_serial(self, port, baud):
        # Standard COM port initialisation
        self.notify("Opening {} at {} baud".format(port, baud))
        self.ser = serial.Serial(port, baud, parity=serial.PARITY_EVEN, timeout=1)

    def send_double_break(self):
        """
            Sends a double break to reset the UPDI port
            BREAK is actually just a slower zero frame
            A double break is guaranteed to push the UPDI state
            machine into a known state, albeit rather brutally
        """
        self.notify("Sending double break")
        # Re-init at a lower baud
        self.ser.close()
        s = serial.Serial(self.port, 1000)
        # Send a break
        s.write([UPDI_BREAK])
        # Wait
        time.sleep(0.05)
        # Send another
        s.write([UPDI_BREAK])
        time.sleep(0.001)
        # Re-init at the real baud 
        s.close()
        self.initialise_serial(self.port, self.baud)

    def send(self, command):
        """
            Sends a char array to UPDI with inter-byte delay
            Note that the byte will echo back
        """
        if self.verbose >= self.VERBOSE_THRESHOLD:
            self.notify("send: {}".format(command))
        for c in command:
            # Send
            self.ser.write([c])
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
            c = self.ser.read()
            # Anything in?
            if c != "":
                response.append(ord(c))
                size -= 1
            else:
                timeout -= 1
        self.notify("receive: {}".format(response))
        return response

    def sib(self):
        """
            System information block is just a string coming back from a SIB command
        """
        self.send([UPDI_PHY_SYNC, UPDI_KEY | UPDI_KEY_SIB | UPDI_SIB_16BYTES])
        return self.ser.readline()

    def __del__(self):
        self.notify("Closing {}".format(self.port))
        self.ser.close()


class UpdiDatalink:
    """
        UPDI data link class handles the UPDI data protocol within the device
    """

    def __init__(self, comport, baud, verbose=0):
        self.VERBOSE_THRESHOLD = 3
        self.verbose = verbose
        self.notify("Constructor")
        # Create a UPDI physical connection
        self.updi_phy = UpdiPhysical(comport, baud, verbose=verbose)
        # Initialise
        self.init()
        # Check
        if not self.check():
            # Send double break if all is not well, and re-check
            self.updi_phy.send_double_break()
            self.init()
            if not self.check():
                raise (Exception("UPDI initialisation failed."))

    def notify(self, message):
        if self.verbose >= self.VERBOSE_THRESHOLD:
            print "    DL:{}".format(message)

    def init(self):
        # Set the inter-byte delay bit and disable collision detection
        self.stcs(UPDI_CS_CTRLB, 1 << UPDI_CTRLB_CCDETDIS_BIT)
        self.stcs(UPDI_CS_CTRLA, 1 << UPDI_CTRLA_IBDLY_BIT)

    def check(self):
        """
            Check UPDI by loading CS STATUSA
        """
        if self.ldcs(UPDI_CS_STATUSA) != 0:
            self.notify("UPDI init OK")
            return True
        self.notify("UPDI not OK - reinitialisation required")
        return False

    def ldcs(self, address):
        """
            Load data from Control/Status space
        """
        self.notify("LDCS from 0x{0:02X}".format(address))
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_LDCS | (address & 0x0F)])
        response = self.updi_phy.receive(1)
        if len(response) != 1:
            # Todo - flag error
            return 0x00
        return response[0]

    def stcs(self, address, value):
        """
            Store a value to Control/Status space
        """
        self.notify("STCS to 0x{0:04X}".format(address))
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_STCS | (address & 0x0F), value])

    def ld(self, address):
        """
            Load a single byte direct from a 16-bit address
        """
        self.notify("LD from 0x{0:04X}".format(address))
        self.updi_phy.send(
            [UPDI_PHY_SYNC, UPDI_LDS | UPDI_ADDRESS_16 | UPDI_DATA_8, address & 0xFF, (address >> 8) & 0xFF])
        return self.updi_phy.receive(1)[0]

    def ld16(self, address):
        """
            Load a 16-bit word directly from a 16-bit address
        """
        self.notify("LD from 0x{0:04X}".format(address))
        self.updi_phy.send(
            [UPDI_PHY_SYNC, UPDI_LDS | UPDI_ADDRESS_16 | UPDI_DATA_16, address & 0xFF, (address >> 8) & 0xFF])
        return self.updi_phy.receive(2)

    def st(self, address, value):
        """
            Store a single byte value directly to a 16-bit address
        """
        self.notify("ST to 0x{0:04X}".format(address))
        self.updi_phy.send(
            [UPDI_PHY_SYNC, UPDI_STS | UPDI_ADDRESS_16 | UPDI_DATA_8, address & 0xFF, (address >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("Error with st"))

        self.updi_phy.send([value & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("Error with st"))

    def st16(self, address, value):
        """
            Store a 16-bit word value directly to a 16-bit address
        """
        self.notify("ST to 0x{0:04X}".format(address))
        self.updi_phy.send(
            [UPDI_PHY_SYNC, UPDI_STS | UPDI_ADDRESS_16 | UPDI_DATA_16, address & 0xFF, (address >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("Error with st"))

        self.updi_phy.send([value & 0xFF, (value >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("Error with st"))

    def ld_ptr_inc(self, size):
        """
            Loads a number of bytes from the pointer location with pointer post-increment
        """
        self.notify("LD8 from ptr++")
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_LD | UPDI_PTR_INC | UPDI_DATA_8])
        return self.updi_phy.receive(size)

    def ld_ptr_inc16(self, words):
        """
            Load a 16-bit word value from the pointer location with pointer post-increment
        """
        self.notify("LD16 from ptr++")
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_LD | UPDI_PTR_INC | UPDI_DATA_16])
        return self.updi_phy.receive(words << 1)

    def st_ptr(self, address):
        """
            Set the pointer location
        """
        self.notify("ST to ptr")
        self.updi_phy.send(
            [UPDI_PHY_SYNC, UPDI_ST | UPDI_PTR_ADDRESS | UPDI_DATA_16, address & 0xFF, (address >> 8) & 0xFF])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("Error with st_ptr"))

    def st_ptr_inc(self, data):
        """
            Store data to the pointer location with pointer post-increment
        """
        self.notify("ST8 to *ptr++")
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_ST | UPDI_PTR_INC | UPDI_DATA_8, data[0]])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("ACK error with st_ptr_inc"))
        n = 1
        while n < len(data):
            self.updi_phy.send([data[n]])
            response = self.updi_phy.receive(1)
            if len(response) != 1 or response[0] != UPDI_PHY_ACK:
                raise (Exception("Error with st_ptr_inc"))
            n += 1

    def st_ptr_inc16(self, data):
        """
            Store a 16-bit word value to the pointer location with pointer post-increment
        """
        self.notify("ST16 to *ptr++")
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_ST | UPDI_PTR_INC | UPDI_DATA_16, data[0], data[1]])
        response = self.updi_phy.receive(1)
        if len(response) != 1 or response[0] != UPDI_PHY_ACK:
            raise (Exception("ACK error with st_ptr_inc16"))
        n = 2
        while n < len(data):
            self.updi_phy.send([data[n], data[n + 1]])
            response = self.updi_phy.receive(1)
            if len(response) != 1 or response[0] != UPDI_PHY_ACK:
                raise (Exception("Error with st_ptr_inc16"))
            n += 2

    def repeat(self, repeats):
        """
            Store a value to the repeat counter
        """
        self.notify("Repeat {0:d}".format(repeats))
        repeats -= 1
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_REPEAT | UPDI_REPEAT_WORD, repeats & 0xFF, (repeats >> 8) & 0xFF])

    def read_sib(self):
        """
            Read the SIB
        """
        return self.updi_phy.sib()

    def key(self, size, key):
        """
            Write a key
        """
        self.notify("Writing key")
        if len(key) != 8 << size:
            raise (Exception("Invalid KEY length!"))
        self.updi_phy.send([UPDI_PHY_SYNC, UPDI_KEY | UPDI_KEY_KEY | size])
        self.updi_phy.send(list(reversed(list(key))))


class UpdiApplication:
    """
        Generic application layer for UPDI
    """

    def __init__(self, comport, baud, device=None, verbose=0):
        self.VERBOSE_THRESHOLD = 2
        self.verbose = verbose
        self.notify("Constructor")
        self.datalink = UpdiDatalink(comport, baud, verbose)
        self.device = device

    def notify(self, message):
        if self.verbose >= self.VERBOSE_THRESHOLD:
            print "  APP:{}".format(message)

    def device_info(self):
        """
            Reads out device information from various sources
        """
        sib = self.datalink.read_sib()
        print "SIB read out as: {}".format(sib)
        print "Family ID = {}".format(sib[0:7])
        print "NVM revision = {}".format(sib[10])
        print "OCD revision = {}".format(sib[13])
        print "PDI OSC = {}MHz".format(sib[15])

        print "PDI revision = 0x{:X}".format(self.datalink.ldcs(UPDI_CS_STATUSA) >> 4)
        if self.in_prog_mode():
            if self.device is not None:
                devid = self.read_data(self.device.sigrow_address, 3)
                devrev = self.read_data(self.device.syscfg_address + 1, 1)
                print "Device ID = {0:X}{1:X}{2:X} rev {3:}".format(devid[0], devid[1], devid[2],
                                                                    chr(ord('A') + devrev[0]))

    def in_prog_mode(self):
        """
            Checks whether the NVM PROG flag is up
        """
        if self.datalink.ldcs(UPDI_ASI_SYS_STATUS) & (1 << UPDI_ASI_SYS_STATUS_NVMPROG):
            return True
        return False

    def wait_unlocked(self, timeout_ms):
        """
            Waits for the device to be unlocked.  
            All devices boot up as locked until proven otherwise
        """
        while True:
            if not self.datalink.ldcs(UPDI_ASI_SYS_STATUS) & (1 << UPDI_ASI_SYS_STATUS_LOCKSTATUS):
                return True
            if timeout_ms == 0:
                self.notify("Timeout waiting for device to unlock")
                return False
            time.sleep((timeout_ms / 1000.0) / 10)
            timeout_ms -= 1

    def unlock(self):
        """
            Unlock and erase
        """
        # Put in the key
        self.datalink.key(UPDI_KEY_64, UPDI_KEY_CHIPERASE)

        # Check key status
        key_status = self.datalink.ldcs(UPDI_ASI_KEY_STATUS)
        self.notify("Key status = 0x{0:02X}".format(key_status))
        if not key_status & (1 << UPDI_ASI_KEY_STATUS_CHIPERASE):
            raise (Exception("Key not accepted"))

        # Toggle reset
        self.reset(True)
        self.reset(False)

        # And wait for unlock
        if not self.wait_unlocked(10):
            raise (Exception("Failed to chip erase using key."))

    def enter_progmode(self):
        """
            Enters into NVM programming mode
        """
        # First check if NVM is already enabled
        if self.in_prog_mode():
            self.notify("Already in NVM programming mode")
            return True

        self.notify("Entering NVM programming mode")

        # Put in the key
        self.datalink.key(UPDI_KEY_64, UPDI_KEY_NVM)

        # Check key status
        key_status = self.datalink.ldcs(UPDI_ASI_KEY_STATUS)
        self.notify("Key status = 0x{0:02X}".format(key_status))
        if not key_status & (1 << UPDI_ASI_KEY_STATUS_NVMPROG):
            raise (Exception("Key not accepted"))

        # Toggle reset
        self.reset(True)
        self.reset(False)

        # And wait for unlock
        if not self.wait_unlocked(10):
            raise (Exception("Failed to enter NVM programming mode: device is locked"))

        # Check for NVMPROG flag
        if not self.in_prog_mode():
            raise (Exception("Failed to enter NVM programming mode"))

        self.notify("Now in NVM programming mode")
        return True

    def leave_progmode(self):
        """
            Disables UPDI which releases any keys enabled
        """
        self.notify("Leaving NVM programming mode")
        self.datalink.stcs(UPDI_CS_CTRLB, (1 << UPDI_CTRLB_UPDIDIS_BIT) | (1 << UPDI_CTRLB_CCDETDIS_BIT))

    def reset(self, apply_reset):
        """
            Applies or releases an UPDI reset condition
        """
        if apply_reset:
            self.notify("Apply reset")
            self.datalink.stcs(UPDI_ASI_RESET_REQ, UPDI_RESET_REQ_VALUE)
        else:
            self.notify("Release reset")
            self.datalink.stcs(UPDI_ASI_RESET_REQ, 0x00)

    def wait_flash_ready(self):
        """
            Waits for the NVM controller to be ready
        """
        # TODO - add timeout
        self.notify("Wait flash ready")
        while True:
            status = self.datalink.ld(self.device.nvmctrl_address + UPDI_NVMCTRL_STATUS)
            if status & (1 << UPDI_NVM_STATUS_WRITE_ERROR):
                self.notify("NVM error")
                return False

            if not (status & ((1 << UPDI_NVM_STATUS_EEPROM_BUSY) | (1 << UPDI_NVM_STATUS_FLASH_BUSY))):
                return True

    def execute_nvm_command(self, command):
        """
            Executes an NVM COMMAND on the NVM CTRL
        """
        self.notify("NVMCMD {:d} executing".format(command))
        return self.datalink.st(self.device.nvmctrl_address + UPDI_NVMCTRL_CTRLA, command)

    def chip_erase(self):
        """
            Does a chip erase using the NVM controller
            Note that on locked devices this it not possible and the ERASE KEY has to be used instead
        """
        self.notify("Chip erase using NVM CTRL")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_flash_ready():
            raise (Exception("Timeout waiting for flash ready before erase "))

        # Erase 
        self.execute_nvm_command(UPDI_NVMCTRL_CTRLA_CHIP_ERASE)

        # And wait for it
        if not self.wait_flash_ready():
            raise (Exception("Timeout waiting for flash ready after erase"))

        return True

    def write_data_words(self, address, data):
        """
            Writes a number of words to memory
        """
        # Special-case of 1 word
        if len(data) == 2:
            value = data[0] + (data[1] << 8)
            return self.datalink.st16(address, value)

        # Range check
        if len(data) > (UPDI_MAX_REPEAT_SIZE + 1) << 1:
            raise (Exception("Invalid length"))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        self.datalink.repeat(len(data) >> 1)
        return self.datalink.st_ptr_inc16(data)

    def write_data(self, address, data):
        """
            Writes a number of bytes to memory
        """
        # Special case of 1 byte
        if len(data) == 1:
            return self.datalink.st(address, data[0])
        # Special case of 2 byte
        elif len(data) == 2:
            self.datalink.st(address, data[0])
            return self.datalink.st(address + 1, data[1])

        # Range check
        if len(data) > (UPDI_MAX_REPEAT_SIZE + 1):
            raise (Exception("Invalid length"))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        self.datalink.repeat(len(data))
        return self.datalink.st_ptr_inc(data)

    def write_nvm(self, address, data, nvm_command=UPDI_NVMCTRL_CTRLA_WRITE_PAGE, use_word_access=True):
        """
            Writes a page of data to NVM.  
            By default the PAGE_WRITE command is used, which requires that the page is already erased
            By default word access is used (flash)
        """

        # Check that NVM controller is ready
        if not self.wait_flash_ready():
            raise (Exception("Timeout waiting for flash ready before page buffer clear "))

        # Clear the page buffer
        self.notify("Clear page buffer")
        self.execute_nvm_command(UPDI_NVMCTRL_CTRLA_PAGE_BUFFER_CLR)

        # Waif for NVM controller to be ready
        if not self.wait_flash_ready():
            raise (Exception("Timeout waiting for flash ready after page buffer clear "))

        # Load the page buffer by writing directly to location
        if use_word_access:
            self.write_data_words(address, data)
        else:
            self.write_data(address, data)

        # Write the page to NVM, maybe erase first
        self.notify("Committing page")
        self.execute_nvm_command(nvm_command)

        # Waif for NVM controller to be ready again
        if not self.wait_flash_ready():
            raise (Exception("Timeout waiting for flash ready after page write "))

    def read_data(self, address, size):
        """
            Reads a number of bytes of data from UPDI
        """
        self.notify("Reading {0:d} bytes from 0x{1:04X}".format(size, address))
        # Range check
        if size > UPDI_MAX_REPEAT_SIZE + 1:
            raise (Exception("Cant read that many bytes in one go"))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        if size > 1:
            self.datalink.repeat(size)

        # Do the read(s)
        return self.datalink.ld_ptr_inc(size)

    def read_data_words(self, address, words):
        """
            Reads a number of words of data from UPDI
        """
        self.notify("Reading {0:d} words from 0x{1:04X}".format(words, address))
        # Range check
        if words > (UPDI_MAX_REPEAT_SIZE >> 1) + 1:
            raise (Exception("Cant read that many words in one go"))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        if words > 1:
            self.datalink.repeat(words)

        # Do the read
        return self.datalink.ld_ptr_inc16(words)


class UpdiNvmProgrammer:
    """
        NVM programming utility for UPDI
    """

    def __init__(self, comport, baud, device, verbose=0):
        self.VERBOSE_THRESHOLD = 1
        self.verbose = verbose
        self.notify("Constructor")
        self.application = UpdiApplication(comport, baud, device, verbose)
        self.device = device
        self.progmode = False

    def notify(self, message):
        if self.verbose >= self.VERBOSE_THRESHOLD:
            print "{}".format(message)

    def get_device_info(self):
        """
            Reads device info
        """
        self.notify("Reading device info")
        return self.application.device_info()

    def enter_progmode(self):
        """
            Enter programming mode
        """
        self.notify("Entering NVM programming mode")
        if self.application.enter_progmode():
            self.progmode = True

    def leave_progmode(self):
        """
            Leave programming mode
        """
        self.notify("Leaving NVM programming mode")
        self.application.leave_progmode()
        self.progmode = False

    def unlock_device(self):
        """
            Unlock and erase a device
        """
        if self.progmode:
            self.notify("Device already unlocked")
            return

        # Unlock
        self.application.unlock()
        # Unlock after using the NVM key results in prog mode.
        self.progmode = True

    def chip_erase(self):
        """
            Erase (unlocked) device
        """
        if not self.progmode:
            raise (Exception("Enter progmode first!"))
        return self.application.chip_erase()

    def read_flash(self, address, size):
        """
            Reads from flash
        """
        # Must be in prog mode here
        if not self.progmode:
            raise (Exception("Enter progmode first!"))
        # Find the number of pages
        pages = size / device.flash_pagesize
        if size % device.flash_pagesize:
            raise (Exception("Only full page aligned flash supported."))
        data = []
        # Read out page-wise for convenience
        for i in range(pages):
            self.notify("Reading page at 0x{0:04X}".format(address))
            data += (self.application.read_data_words(address, device.flash_pagesize >> 1))
            address += device.flash_pagesize
        return data

    def write_flash(self, address, data):
        """
            Writes to flash
        """
        # Must be in prog mode
        if not self.progmode:
            raise (Exception("Enter progmode first!"))
        # Pad to full page
        data = self.pad_data(data, self.device.flash_pagesize)
        # Divide up into pages
        pages = self.page_data(data, self.device.flash_pagesize)
        # Program each page
        for page in pages:
            self.notify("Writing page at 0x{0:04X}".format(address))
            self.application.write_nvm(address, page)
            address += len(page)

    def pad_data(self, data, blocksize, character=0xFF):
        """
            Pads data so that there are full pages
        """
        self.notify("Padding to blocksize {0:d} with 0x{1:X}".format(blocksize, character))
        if len(data) % blocksize > 0:
            for i in range(len(data) % blocksize, blocksize):
                data.append(0)
        return data

    def page_data(self, data, size):
        """
            Divide data into pages
        """
        self.notify("Paging into {} byte blocks".format(size))
        total_length = len(data)
        result = []
        while len(result) < total_length / size:
            result.append(data[:size].tolist())
            data = data[size:]
        return result

    def load_ihex(self, filename):
        """
            Load from intel hex format
        """
        self.notify("Loading from hexfile '{}'".format(filename))
        from intelhex import IntelHex

        ih = IntelHex()
        ih.loadhex(filename)
        data = ih.tobinarray()
        start_address = ih.minaddr()
        self.notify("Loaded {0:d} bytes from ihex starting at address 0x{1:04X}".format(len(data), start_address))

        # Size check
        if len(data) > self.device.flash_size:
            raise (Exception("ihex too large for flash"))

        # Offset to actual flash start
        if start_address < self.device.flash_start:
            self.notify("Adjusting flash offset to address 0x{:04X}".format(self.device.flash_start))
            start_address += self.device.flash_start

        return data, start_address


class Device:
    def __init__(self, device_name):
        if device_name == "tiny817":
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.syscfg_address = 0x0F00
        else:
            raise (Exception("Unknown device"))


"""
    Simple command line interface for programming flash
"""
if __name__ == "__main__":
    # Simple command line interface for demo purposes
    import sys

    if len(sys.argv) != 4:
        print "Python UPDI programmer demo"
        print "Usage: pyupdi.py comport device filename"
        sys.exit(1)

    # Retrieve parameters
    comport = sys.argv[1]
    device = Device(sys.argv[2])
    filename = sys.argv[3]

    # Initialise the UPDI stack on a COM port
    # Verbose 0: quiet
    # Verbose 1: NVM logging
    #   Verbose 2: APP logging
    #   Verbose 3: DL logging
    #   Verbose 4: PHY logging
    #
    nvm = UpdiNvmProgrammer(comport=comport, baud=100000, device=device, verbose=1)

    # Retrieve data to write
    data, start_address = nvm.load_ihex(filename)

    # Enter programming mode
    try:
        nvm.enter_progmode()
    except:
        print "Device is locked.  Performing unlock with chip erase."
        nvm.unlock_device()

    # Read and display device info
    nvm.get_device_info()

    # Erase the device
    nvm.chip_erase()

    # Program from intel hex file
    nvm.write_flash(start_address, data)

    # Read out again
    readback = nvm.read_flash(device.flash_start, len(data))
    for i in range(len(data)):
        if data[i] != readback[i]:
            print "Verify error at location 0x{0:04X}: expected 0x{1:02X} read 0x{2:02X} ".format(i, data[i],
                                                                                                  readback[i])

    # Exit programming mode
    nvm.leave_progmode()