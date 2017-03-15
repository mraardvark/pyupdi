#!/usr/bin/env python
from device.device import Device
from updi.nvm import UpdiNvmProgrammer

import sys
import argparse
import re

import logging
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

def _main():
    parser = argparse.ArgumentParser(description="Simple command line"
                                     " interface for UPDI programming")
    parser.add_argument("-d", "--device", choices=Device.get_supported_devices(),
                        required=True, help="Target device")
    parser.add_argument("-c", "--comport", required=True,
                        help="Com port to use (Windows: COMx | *nix: /dev/ttyX)")
    parser.add_argument("-e", "--erase", action="store_true",
                        help="Perform a chip erase (implied with --flash)")
    parser.add_argument("-b", "--baudrate", type=int, default=115200)
    parser.add_argument("-f", "--flash", help="Intel HEX file to flash.")
    parser.add_argument("-fs", "--fuses", action="append", nargs="*",
                        help="Fuse to set (syntax: fuse_nr:0xvalue)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Set verbose mode")

    args = parser.parse_args(sys.argv[1:])

    if args.fuses is None and args.flash is None and not args.erase:
        print("No action (erase, flash or fuses)")
        sys.exit(0)

    if args.verbose:
        logging.basicConfig(format="%(levelname)s:%(name)s %(message)s",
                            level=logging.INFO)
    else:
        logging.basicConfig(format="%(levelname)s:%(name)s %(message)s",
                            level=logging.WARNING)

    nvm = UpdiNvmProgrammer(comport=args.comport,
                            baud=args.baudrate,
                            device=Device(args.device))

    try:
        nvm.enter_progmode()
    except:
        print("Device is locked. Performing unlock with chip erase.")
        nvm.unlock_device()

    nvm.get_device_info()

    if not _process(nvm, args):
        print("Error during processing")

    nvm.leave_progmode()

def _process(nvm, args):
    if args.erase:
        try:
            nvm.chip_erase()
        except:
            return False
    if args.fuses is not None:
        for fslist in args.fuses:
            for fsarg in fslist:
                if not re.match("^[0-9]+:0x[0-9a-fA-F]+$", fsarg):
                    print("Bad fuses format {}. Expected fuse_nr:0xvalue".format(fsarg))
                    continue
                lst = fsarg.split(":0x")
                fusenum = int(lst[0])
                value = int(lst[1], 16)
                if not _set_fuse(nvm, fusenum, value):
                    return False
    if args.flash is not None:
        return _flash_file(nvm, args.flash)
    return True

def _flash_file(nvm, filename):
    data, start_address = nvm.load_ihex(filename)

    fail=False

    nvm.chip_erase()
    nvm.write_flash(start_address, data)

    # Read out again
    readback = nvm.read_flash(nvm.device.flash_start, len(data))
    for i, _ in enumerate(data):
        if data[i] != readback[i]:
            print("Verify error at location 0x{0:04X}: expected 0x{1:02X} read 0x{2:02X} ".format(i, data[i], readback[i]))
            fail=True

    if not fail:
        print("Programming successful")
    return not fail


def _set_fuse(nvm, fusenum, value):
    nvm.write_fuse(fusenum, value)
    actual_val = nvm.read_fuse(fusenum)
    ret = actual_val == value
    if not ret:
        print("Verify error for fuse {0}, expected 0x{1:02X} read 0x{2:02X}".format(fusenum, value, actual_val))
    return ret

if __name__ == "__main__":
    _main()
