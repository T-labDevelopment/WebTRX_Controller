#!/usr/bin/env python3
"""Static-only HID report and local source-patching tests (NO hardware validation)."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import tempfile
import re

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepare_firmware',HERE/'prepare_firmware.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def input_lengths(report: bytes) -> dict[int,int]:
    """Compute input bits by Report ID from USB HID short items."""
    counts = {}
    report_id = 0
    report_count = 0
    report_size = 0
    i=0
    while i<len(report):
        prefix=report[i];i+=1
        if prefix==0xFE:
            size=report[i];i+=2+size;continue
        size = [0,1,2,4][prefix&3]
        data=report[i:i+size];i+=size
        unsigned=int.from_bytes(data,'little')
        item_type=(prefix>>2)&3
        tag=(prefix>>4)&15
        if item_type==1 and tag==8: report_id=unsigned
        if item_type==1 and tag==7: report_size=unsigned
        if item_type==1 and tag==9: report_count=unsigned
        if item_type==0 and tag==8:
            counts[report_id]=counts.get(report_id,0)+report_size*report_count
    return counts

def test_descriptor():
    report=mod.HID_REPORT_DESCRIPTOR
    assert input_lengths(report)=={1:64,2:16},input_lengths(report)
    assert report.count(bytes([0x85])[0])==2
    assert bytes([0x09,0x05,0xA1,0x01,0x85,0x02]) in report
    assert bytes([0x09,0x30,0x15,0x81,0x25,0x7F]) in report
    assert -64 == int.from_bytes(bytes([0xC0]),'little',signed=True)
    assert mod.VID==0x1209 and mod.PID==0x0001


def test_example_patch():
    # This fixture tests the patcher only, not actual CH55xDuino compatibility.
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp)/'HidKeyboardMouse'
        src=base/'src'/'userUsbHidKeyboardMouse'
        src.mkdir(parents=True)
        (src/'USBconstant.c').write_text('''
__code USB_Descriptor_Device_t DeviceDescriptor = {
.VendorID = 0x1209, .ProductID = 0xc55D,
};
__code USB_Descriptor_Configuration_t ConfigurationDescriptor = {
  .SubClass = HID_CSCP_BootSubclass,
  .Protocol = HID_CSCP_KeyboardBootProtocol,
};
__code uint8_t ReportDescriptor[] = { 0x00 };
__code uint16_t SerialDescriptor[] = { 0x00 };
__code uint16_t ProductDescriptor[] = { 0x00 };
__code uint16_t ManufacturerDescriptor[] = { 0x00 };
''')
        (src/'USBHIDKeyboardMouse.c').write_text('''uint8_t HIDMouse[4];
void send() { UEP1_T_LEN = 1 + sizeof(HIDMouse); }
uint8_t USB_EP1_send(uint8_t report) { return report; }
''')
        (src/'USBHIDKeyboardMouse.h').write_text('void USBInit(void);\n')
        original_dest=mod.DEST
        mod.DEST=Path(temp)/'new_source'
        try:
            mod.prepare(base)
            out=(mod.DEST/'userUsbHidKeyboardMouse'/'USBconstant.c').read_text()
            assert '.ProductID = 0x0001' in out
            assert '.VendorID = 0x1209' in out
            assert "'W', 'e', 'b', 'T', 'R', 'X'" in out
            assert '0x09, 0x05, 0xA1, 0x01, 0x85, 0x02' in out
            assert 'Gamepad_setState' in (mod.DEST/'userUsbHidKeyboardMouse'/'USBHIDKeyboardMouse.h').read_text()
            assert 'UEP1_T_LEN = 3;' in (mod.DEST/'userUsbHidKeyboardMouse'/'USBHIDKeyboardMouse.c').read_text()
        finally:
            mod.DEST=original_dest

if __name__=='__main__':
    test_descriptor()
    test_example_patch()
    print('PASS: HID descriptor 64-bit keyboard/16-bit gamepad input and patcher fixture (static only)')
