

class Device(object): # pylint: disable=too-few-public-methods
    """
    Contains device specific information needed for programming
    """
    def __init__(self, device_name):
        if device_name == "tiny817":
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.syscfg_address = 0x0F00
        else:
            raise Exception("Unknown device")
