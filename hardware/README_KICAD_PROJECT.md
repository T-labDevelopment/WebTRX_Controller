# WebTRX_Controller Rev.A / KiCad 10 editable data
The KiCad project files are in this folder. Open `WebTRX_Controller.kicad_pro` with **KiCad 10.0.x stable**; the complete schematic is `WebTRX_Controller.kicad_sch`.

The electrical circuit contains:
- SW1 = EC12E2420801 encoder A/B/C, phases to P1.4/P1.5 and C to GND
- SW2 = F1, NO contact P1.6 to GND
- SW3 = F2, NO contact P1.7 to GND
- SW4 = PTT, NO contact P3.2 to GND
- J1 = 6-way **logical harness** to WeAct Studio CH552 Core Board V1.0 (J1 pin numbers are NOT WeAct board physical pad numbers)

The WeAct board owns USB connector, power conversion, USB bootstrap and reset. P3.6 and RST remain reserved. GPIO pull-ups must be enabled in firmware. No extra PWR_FLAG is needed in this passive external signal circuit as no active power input pin is represented.

**Hardware-only circuit:** firmware continues to use 1 mechanical click = HID X-axis `0 -> +127` / `0 -> -127` and F1/F2/PTT configurable HID key mapping. These USB commands are software and do not change A/B electrical connections.

**Manufacture not approved:** PCB, DRC, exact encoder/switch/connector footprints, WeAct mounting geometry, ERC and on-device tests have NOT been finished. KiCad 10 will fill missing default project settings when opened/saved for the first time. For a ready-to-extract KiCad archive, see the dataset delivered with the chat.

Sources: https://github.com/WeActStudio/WeActStudio.CH552CoreBoard ; https://tech.alpsalpine.com/e/products/detail/EC12E2420801/ ; https://gitlab.com/kicad/libraries/kicad-symbols
