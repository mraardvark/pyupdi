
import logging

from device.device import Device
from updi.nvm import UpdiNvmProgrammer

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

"""
    Simple command line interface for programming flash
"""
if __name__ == "__main__":
    # Simple command line interface for demo purposes
    import sys

    if len(sys.argv) != 4:
        print("Python UPDI programmer demo")
        print("Usage: pyupdi.py comport device filename")
        sys.exit(1)

    logging.basicConfig(format="%(levelname)s:%(name)s %(message)s",
                        level=logging.WARNING)

    # Retrieve parameters
    comport = sys.argv[1]
    device = Device(sys.argv[2])
    filename = sys.argv[3]

    nvm = UpdiNvmProgrammer(comport=comport, baud=115200, device=device)

    # Retrieve data to write
    data, start_address = nvm.load_ihex(filename)

    # Enter programming mode
    try:
        nvm.enter_progmode()
    except Exception:
        print("Device is locked.  Performing unlock with chip erase.")
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
            print("Verify error at location 0x{0:04X}: expected 0x{1:02X} read 0x{2:02X} ".format(i, data[i],
                                                                                                  readback[i]))

    # Exit programming mode
    nvm.leave_progmode()
