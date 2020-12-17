"""
    Definition of device parameters for UPDI programming
"""
import re

# AVR Dx
DEVICE_AVR_D_SERIES = set(["avr128da28", "avr128da32", "avr128da48", "avr128da64", "avr64da28", "avr64da32", "avr64da48", "avr64da64", "avr32da28", "avr32da32", "avr32da48", "avr128db28", "avr128db32", "avr128db48", "avr128db64", "avr64db28", "avr64db32", "avr64db48", "avr64db64", "avr32db28", "avr32db32", "avr32db48", "avr64dd14", "avr64dd20", "avr64dd28", "avr64dd32", "avr32dd14", "avr32dd20", "avr32dd28", "avr32dd32", "avr16dd14", "avr16dd20", "avr16dd28", "avr16dd32"])

# megaAVR
DEVICES_ATMEGA_48K = set(["atmega4808", "atmega4809"])
DEVICES_ATMEGA_32K = set(["atmega3208", "atmega3209"])
DEVICES_ATMEGA_16K = set(["atmega1608", "atmega1609"])
DEVICES_ATMEGA_8K = set(["atmega808", "atmega809"])

# tinyAVR
DEVICES_ATTINY_32K = set(["attiny3216", "attiny3217"])
DEVICES_ATTINY_16K = set(["attiny1604", "attiny1606", "attiny1607", "attiny1614", "attiny1616", "attiny1617"])
DEVICES_ATTINY_8K = set(["attiny804", "attiny806", "attiny807", "attiny814", "attiny816", "attiny817"])
DEVICES_ATTINY_4K = set(["attiny402", "attiny404", "attiny406", "attiny412", "attiny414", "attiny416", "attiny417"])
DEVICES_ATTINY_2K = set(["attiny202", "attiny204", "attiny212", "attiny214"])

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
        
        # Add add at* prefix if not present
        if(device_name.startswith("tiny") or device_name.startswith("mega")):
            device_name = "at" + device_name

        if device_name in DEVICE_AVR_D_SERIES:
            self.fuses_address = 0x1050
            self.userrow_address = 0x1080
            self.lock_address = 0x1040
            self.flash_start = 0x800000
            self.flash_size = int(re.findall("\d+",device_name)[0]) * 1024
            # Page size is irrelevant for writing since flash if word-oriented
            # However since the 1-byte repeat-count is used for read, 256 is the max.
            self.flash_pagesize = 256
        elif device_name in DEVICES_ATMEGA_48K:
            self.flash_start = 0x4000
            self.flash_size = 48 * 1024
            self.flash_pagesize = 128
        elif device_name in DEVICES_ATMEGA_32K:
            self.flash_start = 0x4000
            self.flash_size = 32 * 1024
            self.flash_pagesize = 128
        elif device_name in DEVICES_ATMEGA_16K:
            self.flash_start = 0x4000
            self.flash_size = 16 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_ATMEGA_8K:
            self.flash_start = 0x4000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_ATTINY_32K:
            self.flash_start = 0x8000
            self.flash_size = 32 * 1024
            self.flash_pagesize = 128
        elif device_name in DEVICES_ATTINY_16K:
            self.flash_start = 0x8000
            self.flash_size = 16 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_ATTINY_8K:
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_ATTINY_4K:
            self.flash_start = 0x8000
            self.flash_size = 4 * 1024
            self.flash_pagesize = 64
        elif device_name in DEVICES_ATTINY_2K:
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
        
        # Remove at* prefix on all targets (e.g attiny202 -> tiny202)
        # for legacy naming support
        DEVICES_TINY_2K  = set([s[2:] for s in DEVICES_ATTINY_2K])
        DEVICES_TINY_4K  = set([s[2:] for s in DEVICES_ATTINY_4K])
        DEVICES_TINY_8K  = set([s[2:] for s in DEVICES_ATTINY_8K])
        DEVICES_TINY_16K = set([s[2:] for s in DEVICES_ATTINY_16K])
        DEVICES_TINY_32K = set([s[2:] for s in DEVICES_ATTINY_32K])
        DEVICES_MEGA_8K  = set([s[2:] for s in DEVICES_ATMEGA_8K])
        DEVICES_MEGA_16K = set([s[2:] for s in DEVICES_ATMEGA_16K])
        DEVICES_MEGA_32K = set([s[2:] for s in DEVICES_ATMEGA_32K])
        DEVICES_MEGA_48K = set([s[2:] for s in DEVICES_ATMEGA_48K])


        return sorted(
            DEVICES_ATTINY_2K  |
            DEVICES_TINY_2K    |
            DEVICES_ATTINY_4K  |
            DEVICES_TINY_4K    |
            DEVICES_ATTINY_8K  |
            DEVICES_TINY_8K    |
            DEVICES_ATTINY_16K |
            DEVICES_TINY_16K   |
            DEVICES_ATTINY_32K |
            DEVICES_TINY_32K   |
            DEVICES_ATMEGA_8K  |
            DEVICES_MEGA_8K    |
            DEVICES_ATMEGA_16K |
            DEVICES_MEGA_16K   |
            DEVICES_ATMEGA_32K |
            DEVICES_MEGA_32K   |
            DEVICES_ATMEGA_48K |
            DEVICES_MEGA_48K   |
            DEVICE_AVR_D_SERIES)
