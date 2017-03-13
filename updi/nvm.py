import logging

from updi.application import UpdiApplication
import updi.constants as constants

class UpdiNvmProgrammer(object):
    """
        NVM programming utility for UPDI
    """

    def __init__(self, comport, baud, device):

        self.application = UpdiApplication(comport, baud, device)
        self.device = device
        self.progmode = False
        self.logger = logging.getLogger("nvm")

    def get_device_info(self):
        """
            Reads device info
        """
        self.logger.info("Reading device info")
        return self.application.device_info()

    def enter_progmode(self):
        """
            Enter programming mode
        """
        self.logger.info("Entering NVM programming mode")
        if self.application.enter_progmode():
            self.progmode = True

    def leave_progmode(self):
        """
            Leave programming mode
        """
        self.logger.info("Leaving NVM programming mode")
        self.application.leave_progmode()
        self.progmode = False

    def unlock_device(self):
        """
            Unlock and erase a device
        """
        if self.progmode:
            self.logger.info("Device already unlocked")
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
            raise Exception("Enter progmode first!")

        return self.application.chip_erase()

    def read_flash(self, address, size):
        """
            Reads from flash
        """
        # Must be in prog mode here
        if not self.progmode:
            raise Exception("Enter progmode first!")

        # Find the number of pages
        pages = size / self.device.flash_pagesize
        if size % self.device.flash_pagesize:
            raise Exception("Only full page aligned flash supported.")

        data = []
        # Read out page-wise for convenience
        for _ in range(pages):
            self.logger.info("Reading page at 0x{0:04X}".format(address))
            data += (self.application.read_data_words(address, self.device.flash_pagesize >> 1))
            address += self.device.flash_pagesize
        return data

    def write_flash(self, address, data):
        """
            Writes to flash
        """
        # Must be in prog mode
        if not self.progmode:
            raise Exception("Enter progmode first!")

        # Pad to full page
        data = self.pad_data(data, self.device.flash_pagesize)

        # Divide up into pages
        pages = self.page_data(data, self.device.flash_pagesize)

        # Program each page
        for page in pages:
            self.logger.info("Writing page at 0x{0:04X}".format(address))
            self.application.write_nvm(address, page)
            address += len(page)

    def read_fuse(self, fusenum):
        """
            Reads one fuse value
        """
        # Must be in prog mode
        if not self.progmode:
            raise Exception("Enter progmode first!")

        address = self.device.fuses_address + fusenum
        data = self.application.datalink.ld(address)
        return data

    def write_fuse(self, fusenum, value):
        """
            Writes one fuse value
        """
        # Must be in prog mode
        if not self.progmode:
            raise Exception("Enter progmode first!")

        if not self.application.wait_flash_ready():
            raise Exception("Flash not ready for fuse setting")

        fuse_data = [value]
        fuse_address = self.device.fuses_address + fusenum

        address = self.device.nvmctrl_address + constants.UPDI_NVMCTRL_ADDRL
        data = [fuse_address & 0xff]
        self.application.write_data(address, data)

        address = self.device.nvmctrl_address + constants.UPDI_NVMCTRL_ADDRH
        data = [fuse_address >> 8]
        self.application.write_data(address, data)

        address = self.device.nvmctrl_address + constants.UPDI_NVMCTRL_DATAL
        self.application.write_data(address, fuse_data)

        address = self.device.nvmctrl_address + constants.UPDI_NVMCTRL_CTRLA
        data = [constants.UPDI_NVMCTRL_CTRLA_WRITE_FUSE]
        self.application.write_data(address, data)

    def pad_data(self, data, blocksize, character=0xFF):
        """
            Pads data so that there are full pages
        """
        self.logger.info("Padding to blocksize {0:d} with 0x{1:X}".format(blocksize, character))
        if len(data) % blocksize > 0:
            for _ in range(len(data) % blocksize, blocksize):
                data.append(0)
        return data

    def page_data(self, data, size):
        """
            Divide data into pages
        """
        self.logger.info("Paging into {} byte blocks".format(size))
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
        self.logger.info("Loading from hexfile '{}'".format(filename))
        from intelhex import IntelHex

        ih = IntelHex()
        ih.loadhex(filename)
        data = ih.tobinarray()
        start_address = ih.minaddr()
        self.logger.info("Loaded {0:d} bytes from ihex starting at address 0x{1:04X}".format(len(data), start_address))

        # Size check
        if len(data) > self.device.flash_size:
            raise Exception("ihex too large for flash")

        # Offset to actual flash start
        if start_address < self.device.flash_start:
            self.logger.info("Adjusting flash offset to address 0x{:04X}".format(self.device.flash_start))
            start_address += self.device.flash_start

        return data, start_address
