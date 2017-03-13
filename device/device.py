class Device(object): # pylint: disable=too-few-public-methods
    """
    Contains device specific information needed for programming
    """
    def __init__(self, device_name):
        if device_name == "tiny817" or device_name == "tiny816" or device_name == "tiny814":
            self.flash_start = 0x8000
            self.flash_size = 8 * 1024
            self.flash_pagesize = 64
            self.syscfg_address = 0x0F00
            self.nvmctrl_address = 0x1000
            self.sigrow_address = 0x1100
            self.fuses_address = 0x1280
            self.userrow_address = 0x1300
        elif device_name == "tiny417":
            self.flash_start = 0x8000
            self.flash_size = 4 * 1024
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
        return ["tiny817", "tiny816", "tiny814", "tiny417"]
