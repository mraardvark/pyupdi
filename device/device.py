DEVICES_8K = set(["tiny814", "tiny817"])
DEVICES_4K = set(["tiny402", "tiny404", "tiny406", "tiny412", "tiny414", "tiny417"])
DEVICES_2K = set(["tiny202", "tiny204", "tiny214"])

class Device(object):  # pylint: disable=too-few-public-methods
    """
    Contains device specific information needed for programming
    """
    def __init__(self, device_name):
        if device_name in DEVICES_8K:
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_4K:
            self.flash_start = 0x8000
            self.flash_size = 4 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name in DEVICES_2K:
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
        return sorted(DEVICES_2K | DEVICES_4K | DEVICES_8K)
