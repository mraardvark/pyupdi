# megaAVR
DEVICES_MEGA_48K = set(["mega4808", "mega4809"])
DEVICES_MEGA_32K = set(["mega3208", "mega3209"])

# tinyAVR
DEVICES_TINY_32K = set(["tiny3216", "tiny3217"])
DEVICES_TINY_16K = set(["tiny1614", "tiny1616", "tiny1617"])
DEVICES_TINY_8K  = set(["tiny814", "tiny816", "tiny817"])
DEVICES_TINY_4K  = set(["tiny402", "tiny404", "tiny406", "tiny412", "tiny414", "tiny416", "tiny417"])
DEVICES_TINY_2K = set(["tiny202", "tiny204", "tiny212", "tiny214"])

class Device(object):  # pylint: disable=too-few-public-methods
    """
    Contains device specific information needed for programming
    """
    def __init__(self, device_name):
        if device_name in DEVICES_MEGA_48K:
            self.flash_start = 0x4000
            self.flash_size = 48 * 1024
            self.flash_pagesize = 128
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_MEGA_32K:
            self.flash_start = 0x4000
            self.flash_size = 32 * 1024
            self.flash_pagesize = 128
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_TINY_32K:
            self.flash_start = 0x8000
            self.flash_size = 32 * 1024
            self.flash_pagesize = 128
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_TINY_16K:
            self.flash_start = 0x8000
            self.flash_size = 16 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_TINY_8K:
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_TINY_4K:
            self.flash_start = 0x8000
            self.flash_size = 4 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_TINY_2K:
            self.flash_start = 0x8000
            self.flash_size = 2 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        else:
            raise Exception("Unknown device")

    @staticmethod
    def get_supported_devices():
        return sorted(
            DEVICES_TINY_2K |
            DEVICES_TINY_4K |
            DEVICES_TINY_8K |
            DEVICES_TINY_16K |
            DEVICES_TINY_32K |
            DEVICES_MEGA_32K |
            DEVICES_MEGA_48K)
    