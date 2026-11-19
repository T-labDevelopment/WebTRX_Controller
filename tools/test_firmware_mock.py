#!/usr/bin/env python3
"""Compile actual Arduino sketch with stub USB/IO on host and simulate detents.
NO validation of CH552/CH55xDuino build, USB enumeration, or real device.
"""
import subprocess
import shutil
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'firmware'/'ch552_gamepad_keyboard'
with tempfile.TemporaryDirectory() as tmp:
    target=Path(tmp)
    for name in ('ch552_gamepad_keyboard.ino','config.h','rotary_event.h'):
        shutil.copy2(SRC/name,target/name)
    h=target/'src'/'userUsbHidKeyboardMouse'
    h.mkdir(parents=True)
    (h/'USBHIDKeyboardMouse.h').write_text('''
#ifndef USB_HID_STUB
#define USB_HID_STUB
void USBInit(void);
void Keyboard_press(unsigned char);
void Keyboard_release(unsigned char);
unsigned char Gamepad_setState(unsigned char buttons,signed char axis);
#endif
''')
    binary=target/'mock_test'
    cmd=['g++','-std=c++17','-Wall','-Wextra','-Werror','-x','c++','-I',str(target),
         '-include',str(ROOT/'tests'/'mock_firmware.cpp'),'-o',str(binary),'-']
    subprocess.run(cmd,input='',text=True,check=True)
    subprocess.run([str(binary)],check=True)
