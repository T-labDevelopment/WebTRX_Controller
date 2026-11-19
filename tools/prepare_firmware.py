#!/usr/bin/env python3
"""Prepare CH55xDuino 0.0.26 HID Keyboard+Gamepad USB source.

Usage:
  python tools/prepare_firmware.py \
    "/path/to/CH55xDuino/.../05.USB/HidKeyboardMouse"

This copies the pinned CH55xDuino example's `src` directory (NOT included in
this repository) into the new sketch and patches the USB descriptor and the
report-2 sender. The upstream version and license are not changed.

WARNING: 1209:0001 is a PRIVATE TEST identifier from pid.codes; never use it
on products that are redistributed, manufactured or sold.
"""
from __future__ import annotations
import argparse
import re
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DEST = BASE / 'firmware' / 'ch552_gamepad_keyboard' / 'src'
VID = 0x1209
PID = 0x0001
PRODUCT = 'WebTRX Dial Controller RevA'
MANUFACTURER = 'DIY Radio Controller'
SERIAL = 'WTRXRA0001'  # Prototype only; assign a different serial per unit.

# One HID interface with TWO top-level application collections: keyboard ID 1
# and gamepad ID 2. Gamepad input = [3 button bits/padding, signed X axis].
# The absolute axis is intentionally spring-returned to zero by firmware.
HID_REPORT_DESCRIPTOR = bytes([
  0x05,0x01, 0x09,0x06, 0xA1,0x01, 0x85,0x01,
  0x05,0x07, 0x19,0xE0, 0x29,0xE7, 0x15,0x00, 0x25,0x01,
  0x95,0x08, 0x75,0x01, 0x81,0x02,
  0x95,0x01, 0x75,0x08, 0x81,0x03,
  0x95,0x06, 0x75,0x08, 0x15,0x00, 0x26,0xFF,0x00,
  0x05,0x07, 0x19,0x00, 0x29,0xE7, 0x81,0x00,
  0x05,0x08, 0x19,0x01, 0x29,0x05, 0x15,0x00, 0x25,0x01,
  0x95,0x05, 0x75,0x01, 0x91,0x02,
  0x95,0x01, 0x75,0x03, 0x91,0x03,
  0xC0,
  0x05,0x01, 0x09,0x05, 0xA1,0x01, 0x85,0x02,
  0x05,0x09, 0x19,0x01, 0x29,0x03, 0x15,0x00, 0x25,0x01,
  0x95,0x03, 0x75,0x01, 0x81,0x02,
  0x95,0x01, 0x75,0x05, 0x81,0x03,
  0x05,0x01, 0x09,0x30, 0x15,0x81, 0x25,0x7F,
  0x75,0x08, 0x95,0x01, 0x81,0x02,
  0xC0,
])

def only_one_replace(source: str, pattern: str, replacement: str,
                     description: str, flags: int = 0) -> str:
    result, count = re.subn(pattern, lambda m: replacement, source,
                            flags=flags)
    if count != 1:
        raise RuntimeError(f'{description}: expected exactly one pattern; found {count}. '
                           'Check that CH55xDuino 0.0.26 is used.')
    return result

def make_usb_string(name: str, text: str) -> str:
    assert len(text) < 64 and text.isascii()
    codepoints = ', '.join("'%s'" % x for x in text)
    return (f'__code uint16_t {name}[] = {{\n'
            f'    ((({len(text)} + 1) * 2) | (DTYPE_String << 8)),\n'
            f'    {codepoints}\n}};')

def prepare(src_base: Path) -> None:
    src = src_base / 'src' / 'userUsbHidKeyboardMouse'
    if not src.is_dir():
        raise FileNotFoundError('Expected upstream <HidKeyboardMouse>/src/userUsbHidKeyboardMouse')
    for filename in ('USBconstant.c','USBHIDKeyboardMouse.c','USBHIDKeyboardMouse.h'):
        if not (src / filename).is_file():
            raise FileNotFoundError(str(src / filename))
    if DEST.exists():
        raise RuntimeError('Destination exists. Move it aside before regenerating: '+str(DEST))
    # Transform in memory first; do not create partially transformed source tree.
    constant = (src / 'USBconstant.c').read_text(encoding='utf-8')
    constant = only_one_replace(constant, r'\.ProductID\s*=\s*0x[0-9a-fA-F]+',
         f'.ProductID = 0x{PID:04X}', 'USB Product ID')
    # Vendor ID 0x1209 is the allowed private-test VID. Do not invent another ID.
    constant = only_one_replace(constant, r'\.VendorID\s*=\s*0x[0-9a-fA-F]+',
         f'.VendorID = 0x{VID:04X}', 'USB Vendor ID')
    constant = only_one_replace(constant,
         r'\.SubClass\s*=\s*HID_CSCP_BootSubclass',
         '.SubClass = 0x00', 'HID interface subclass')
    constant = only_one_replace(constant,
         r'\.Protocol\s*=\s*HID_CSCP_KeyboardBootProtocol',
         '.Protocol = 0x00', 'HID interface protocol')
    new_report = ('__code uint8_t ReportDescriptor[] = {\n'
                  + '\n'.join('    '+', '.join(f'0x{x:02X}' for x in HID_REPORT_DESCRIPTOR[i:i+12])+','
                              for i in range(0,len(HID_REPORT_DESCRIPTOR),12))
                  + '\n};')
    constant = only_one_replace(constant,
         r'__code uint8_t ReportDescriptor\[\]\s*=\s*\{.*?\};',
         new_report, 'HID report descriptor', re.S)
    for sym, val in [('SerialDescriptor',SERIAL),('ProductDescriptor',PRODUCT),
                     ('ManufacturerDescriptor',MANUFACTURER)]:
        constant = only_one_replace(constant,
            r'__code uint16_t '+sym+r'\[\]\s*=\s*\{.*?\};',
            make_usb_string(sym,val), sym, re.S)
    handler = (src / 'USBHIDKeyboardMouse.c').read_text(encoding='utf-8')
    handler = only_one_replace(handler,
        r'UEP1_T_LEN\s*=\s*1\s*\+\s*sizeof\(HIDMouse\)\s*;',
        'UEP1_T_LEN = 3;  // Report ID + gamepad buttons + signed X',
        'Gamepad IN report size')
    handler += r"""
/* WTRX-RevA: Report ID 2 is a joystick/gamepad (NOT a mouse).
 * 1-byte button bitfield, followed by 1-byte signed absolute X axis.
 * Uses the endpoint sender and the existing HIDMouse[] storage from upstream.
 */
uint8_t Gamepad_setState(__data uint8_t buttons, __data int8_t x) {
    HIDMouse[0] = buttons & 0x07;
    HIDMouse[1] = (uint8_t)x;
    return USB_EP1_send(2);
}
"""
    header = (src / 'USBHIDKeyboardMouse.h').read_text(encoding='utf-8')
    header = only_one_replace(header, r'void USBInit\(void\);',
          'void USBInit(void);\nuint8_t Gamepad_setState(__data uint8_t buttons, __data int8_t x);',
          'Gamepad declaration')
    shutil.copytree(src_base / 'src', DEST)
    (DEST / 'userUsbHidKeyboardMouse' / 'USBconstant.c').write_text(constant, encoding='utf-8')
    (DEST / 'userUsbHidKeyboardMouse' / 'USBHIDKeyboardMouse.c').write_text(handler, encoding='utf-8')
    (DEST / 'userUsbHidKeyboardMouse' / 'USBHIDKeyboardMouse.h').write_text(header, encoding='utf-8')
    print('Prepared experimental composite HID sources:', DEST)
    print('NOTICE: TEST-ONLY VID:PID 1209:0001. DO NOT REDISTRIBUTE HARDWARE USING THIS ID.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream',type=Path,help='path to CH55xDuino 0.0.26 HidKeyboardMouse example')
    args = parser.parse_args()
    prepare(args.upstream)
