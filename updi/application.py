"""
    Application layer for UPDI stack
"""
import logging

import updi.constants as constants
from updi.link import UpdiDatalink
from updi.timeout import Timeout


class UpdiApplication(object):
    """
        Generic application layer for UPDI
    """

    def __init__(self, comport, baud, device=None):
        self.datalink = UpdiDatalink(comport, baud)
        self.device = device

        self.logger = logging.getLogger("app")

        self.write_nvm = self.write_nvm_v0

    def device_info(self):
        """
            Reads out device information from various sources
        """
        info = {}
        sib = bytearray(self.datalink.read_sib())
        self.logger.info("SIB read out as: {}".format(sib))
        
        # Parse fixed width fields according to spec
        family = sib[0:7].strip()
        info['family'] = family.decode()
        self.logger.info("Device family ID: '%s'", family.decode())

        nvm = sib[8:11].strip()
        self.logger.info("NVM interface: '%s'", nvm.decode())
        info['nvm'] = nvm.decode()
        if nvm.decode() == "P:2":
            self.logger.info("Using PDI v2")
            self.write_nvm = self.write_nvm_v1
            self.datalink.set_24bit_updi(True)

        ocd = sib[11:14].strip()
        info['ocd'] = ocd.decode()
        self.logger.info("Debug interface: '%s'", ocd.decode())

        osc = sib[15:19].strip()
        info['osc'] = osc.decode()
        self.logger.info("PDI oscillator: '%s'", osc.decode())

        self.logger.info("PDI revision = 0x{:X}".format(self.datalink.ldcs(constants.UPDI_CS_STATUSA) >> 4))
        if self.in_prog_mode():
            if self.device is not None:
                devid = self.read_data(self.device.sigrow_address, 3)
                device_id_string = "{0:X}{1:X}{2:X}".format(devid[0], devid[1], devid[2])
                info['device_id'] = device_id_string
                self.logger.info("Device ID = '%s'", device_id_string)

                devrev = self.read_data(self.device.syscfg_address + 1, 1)
                device_rev_string = "{0:}".format(chr(ord('A') + devrev[0]))
                info['device_rev'] = device_rev_string
                self.logger.info("Device rev = '%s'", device_rev_string)
        return info

    def in_prog_mode(self):
        """
            Checks whether the NVM PROG flag is up
        """
        if self.datalink.ldcs(constants.UPDI_ASI_SYS_STATUS) & (1 << constants.UPDI_ASI_SYS_STATUS_NVMPROG):
            return True
        return False

    def wait_unlocked(self, timeout_ms):
        """
            Waits for the device to be unlocked.
            All devices boot up as locked until proven otherwise
        """

        timeout = Timeout(timeout_ms)

        while not timeout.expired():
            if not self.datalink.ldcs(constants.UPDI_ASI_SYS_STATUS) & (1 << constants.UPDI_ASI_SYS_STATUS_LOCKSTATUS):
                return True

        self.logger.info("Timeout waiting for device to unlock")
        return False

    def unlock(self):
        """
            Unlock and erase
        """
        # Put in the key
        self.datalink.key(constants.UPDI_KEY_64, constants.UPDI_KEY_CHIPERASE)

        # Check key status
        key_status = self.datalink.ldcs(constants.UPDI_ASI_KEY_STATUS)
        self.logger.info("Key status = 0x{0:02X}".format(key_status))

        if not key_status & (1 << constants.UPDI_ASI_KEY_STATUS_CHIPERASE):
            raise Exception("Key not accepted")

        # Insert NVMProg key as well
        # In case of CRC being enabled, the device must be left in programming mode after the erase
        # to allow the CRC to be disabled (or flash reprogrammed)
        self._progmode_key()

        # Toggle reset
        self.reset(apply_reset=True)
        self.reset(apply_reset=False)

        # And wait for unlock
        if not self.wait_unlocked(200):
            raise Exception("Failed to chip erase using key")

    def _progmode_key(self):
        """
            Inserts the NVMProg key and checks that its accepted
        """
        # First check if NVM is already enabled
        if self.in_prog_mode():
            self.logger.info("Already in NVM programming mode")
            return

        self.logger.info("Entering NVM programming mode")

        # Put in the key
        self.datalink.key(constants.UPDI_KEY_64, constants.UPDI_KEY_NVM)

        # Check key status
        key_status = self.datalink.ldcs(constants.UPDI_ASI_KEY_STATUS)
        self.logger.info("Key status = 0x{0:02X}".format(key_status))

        if not key_status & (1 << constants.UPDI_ASI_KEY_STATUS_NVMPROG):
            raise Exception("Key not accepted")

    def enter_progmode(self):
        """
            Enters into NVM programming mode
        """
        # Enter NVMProg key
        self._progmode_key()

        # Toggle reset
        self.reset(apply_reset=True)
        self.reset(apply_reset=False)

        # Wait for NVMPROG flag
        while True:
            self.logger.info("Wait for NVMPROG")
            sys_status = self.datalink.ldcs(constants.UPDI_ASI_SYS_STATUS)
            if sys_status & (1 << constants.UPDI_ASI_SYS_STATUS_NVMPROG):
                break
        
        if not self.in_prog_mode():
            raise Exception("Failed to enter NVM programming mode")

        self.logger.info("Now in NVM programming mode")
        return True

    def leave_progmode(self):
        """
            Disables UPDI which releases any keys enabled
        """
        self.logger.info("Leaving NVM programming mode")
        self.reset(apply_reset=True)
        self.reset(apply_reset=False)
        self.datalink.stcs(constants.UPDI_CS_CTRLB,
                           (1 << constants.UPDI_CTRLB_UPDIDIS_BIT) | (1 << constants.UPDI_CTRLB_CCDETDIS_BIT))

    def reset(self, apply_reset):
        """
            Applies or releases an UPDI reset condition
        """
        if apply_reset:
            self.logger.info("Apply reset")
            self.datalink.stcs(constants.UPDI_ASI_RESET_REQ, constants.UPDI_RESET_REQ_VALUE)
            self.logger.info("Check reset")
            sys_status = self.datalink.ldcs(constants.UPDI_ASI_SYS_STATUS)
            if not sys_status & (1 << constants.UPDI_ASI_SYS_STATUS_RSTSYS):
                raise("Error applying reset")
        else:
            self.logger.info("Release reset")
            self.datalink.stcs(constants.UPDI_ASI_RESET_REQ, 0x00)
            while True:
                self.logger.info("Wait for !reset")
                sys_status = self.datalink.ldcs(constants.UPDI_ASI_SYS_STATUS)
                if not sys_status & (1 << constants.UPDI_ASI_SYS_STATUS_RSTSYS):
                    break
                    #raise("Error releasing reset")

    def wait_flash_ready(self):
        """
            Waits for the NVM controller to be ready
        """

        timeout = Timeout(10000)  # 10 sec timeout, just to be sure

        self.logger.info("Wait flash ready")
        while not timeout.expired():
            status = self.datalink.ld(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_STATUS)
            if status & (1 << constants.UPDI_NVM_STATUS_WRITE_ERROR):
                self.logger.info("NVM error")
                return False

            if not status & ((1 << constants.UPDI_NVM_STATUS_EEPROM_BUSY) |
                             (1 << constants.UPDI_NVM_STATUS_FLASH_BUSY)):
                return True

        self.logger.error("Wait flash ready timed out")
        return False

    def execute_nvm_command(self, command):
        """
            Executes an NVM COMMAND on the NVM CTRL
        """
        self.logger.info("NVMCMD {:d} executing".format(command))
        return self.datalink.st(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_CTRLA, command)

    def chip_erase(self):
        """
            Does a chip erase using the NVM controller
            Note that on locked devices this it not possible
            and the ERASE KEY has to be used instead
        """
        self.logger.info("Chip erase using NVM CTRL")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready before erase ")

        # Erase
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_CHIP_ERASE)
        # TODO:  erase for DA? 

        # And wait for it
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready after erase")

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
        if len(data) > constants.UPDI_MAX_REPEAT_SIZE << 1:
            raise Exception("Invalid length")

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
        if len(data) > constants.UPDI_MAX_REPEAT_SIZE:
            raise Exception("Invalid length")

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        self.datalink.repeat(len(data))
        return self.datalink.st_ptr_inc(data)

    def write_nvm_v0(self, address, data, use_word_access=True):
        """
            Writes a page of data to NVM.
            By default the PAGE_WRITE command is used, which
            requires that the page is already erased.
            By default word access is used (flash)
        """
        nvm_command=constants.UPDI_V0_NVMCTRL_CTRLA_WRITE_PAGE

        # Check that NVM controller is ready
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready before page buffer clear ")

        # Clear the page buffer
        self.logger.info("Clear page buffer")
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_PAGE_BUFFER_CLR)

        # Wait for NVM controller to be ready
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready after page buffer clear")

        # Load the page buffer by writing directly to location
        if use_word_access:
            self.write_data_words(address, data)
        else:
            self.write_data(address, data)

        # Write the page to NVM, maybe erase first
        self.logger.info("Committing page")
        self.execute_nvm_command(nvm_command)

        # Wait for NVM controller to be ready again
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready after page write ")

    def write_nvm_v1(self, address, data):
        """
            Writes data to NVM.
            This version of the NVM block has no page buffer, so words are written directly.
        """
        nvm_command=constants.UPDI_V1_NVMCTRL_CTRLA_FLASH_WRITE#  UPDI_NVMCTRL_CTRLA_WRITE_PAGE

        # Check that NVM controller is ready
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready before page buffer clear ")

        # Write the command to the NVM controller
        self.logger.info("NVM write command")
        self.execute_nvm_command(nvm_command)

        # Write the data
        self.write_data_words(address, data)

        # Wait for NVM controller to be ready again
        if not self.wait_flash_ready():
            raise Exception("Timeout waiting for flash ready after data write")

        # Remove command from NVM controller
        self.logger.info("Clear NVM command")
        self.execute_nvm_command(constants.UPDI_V1_NVMCTRL_CTRLA_NOCMD)


    def read_data(self, address, size):
        """
            Reads a number of bytes of data from UPDI
        """
        self.logger.info("Reading {0:d} bytes from 0x{1:04X}".format(size, address))
        # Range check
        if size > constants.UPDI_MAX_REPEAT_SIZE:
            raise Exception("Cant read that many bytes in one go")

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
        self.logger.info("Reading {0:d} words from 0x{1:04X}".format(words, address))

        # Range check
        if words > constants.UPDI_MAX_REPEAT_SIZE:
            raise Exception("Cant read that many words in one go")

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        if words > 1:
            self.datalink.repeat(words)

        # Do the read
        return self.datalink.ld_ptr_inc16(words)
