"""
    Definition of device parameters for UPDI programming
"""
import re

# AVR Dx
DEVICE_AVR_D_SERIES = set(["avr128da28", "avr128da32", "avr128da48", "avr128da64"])

# megaAVR
DEVICES_MEGA_48K = set(["mega4808", "mega4809"])
DEVICES_MEGA_32K = set(["mega3208", "mega3209"])

# tinyAVR
DEVICES_TINY_32K = set(["tiny3216", "tiny3217"])
DEVICES_TINY_16K = set(["tiny1604", "tiny1606", "tiny1607", "tiny1614", "tiny1616", "tiny1617"])
DEVICES_TINY_8K = set(["tiny804", "tiny806", "tiny807", "tiny814", "tiny816", "tiny817"])
DEVICES_TINY_4K = set(["tiny402", "tiny404", "tiny406", "tiny412", "tiny414", "tiny416", "tiny417"])
DEVICES_TINY_2K = set(["tiny202", "tiny204", "tiny212", "tiny214"])

# Defaults
DEFAULT_SYSCFG_ADDRESS = 0x0F00
DEFAULT_NVMCTRL_ADDRESS = 0x1000
DEFAULT_SIGROW_ADDRESS = 0x1100
DEFAULT_FUSES_ADDRESS = 0x1280
DEFAULT_USERROW_ADDRESS = 0x1300

class Device(object):  # pylint: disable=too-few-public-methods
    """
        Contains device specific information needed for programming
    """

    def __init__(self, device_name):
        # Start with defaults
        self.syscfg_address = DEFAULT_SYSCFG_ADDRESS
        self.nvmctrl_address = DEFAULT_NVMCTRL_ADDRESS
        self.sigrow_address = DEFAULT_SIGROW_ADDRESS
        self.fuses_address = DEFAULT_FUSES_ADDRESS
        self.userrow_address = DEFAULT_USERROW_ADDRESS

        if device_name in DEVICE_AVR_D_SERIES:
            self.fuses_address = 0x1050
            self.userrow_address = 0x1080
            self.lock_address = 0x1040
            self.flash_start = 0x800000
            self.flash_size = int(re.findall("\d+",device_name)[0]) * 1024
            # Page size is irrelevant for writing since flash if word-oriented
            # However since the 1-byte repeat-count is used for read, 256 is the max.
            self.flash_pagesize = 256
        elif device_name in DEVICES_MEGA_48K:
            self.flash_start = 0x4000
            self.flash_size = 48 * 1024
            self.flash_pagesize = 128
        elif device_name in DEVICES_MEGA_32K:
            self.flash_start = 0x4000
            self.flash_size = 32 * 1024
            self.flash_pagesize = 128
        elif device_name in DEVICES_TINY_32K:
            self.flash_start = 0x8000
            self.flash_size = 32 * 1024
            self.flash_pagesize = 128
        elif device_name in DEVICES_TINY_16K:
            self.flash_start = 0x8000
            self.flash_size = 16 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_TINY_8K:
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_TINY_4K:
            self.flash_start = 0x8000
            self.flash_size = 4 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_TINY_2K:
            self.flash_start = 0x8000
            self.flash_size = 2 * 1024
            self.flash_pagesize = 64
        else:
            raise Exception("Unknown device")

    @staticmethod
    def get_supported_devices():
        """
            Query for device support list
            :return: list of supported devices
        """
        return sorted(
            DEVICES_TINY_2K |
            DEVICES_TINY_4K |
            DEVICES_TINY_8K |
            DEVICES_TINY_16K |
            DEVICES_TINY_32K |
            DEVICES_MEGA_32K |
            DEVICES_MEGA_48K |
            DEVICE_AVR_D_SERIES)
