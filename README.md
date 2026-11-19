# WebTRX Controller — CH552 USB HID rotary dial (KiCad 10)

Active hardware revision: **Rev.A.2**, with WeAct CH552 Core Board V1.0 module (onboard USB), EC12E2420801 24-detent encoder, and three 12mm tact switches.

The current **editable KiCad schematic + two-layer PCB** and all project-local symbol / footprint libraries are in `hardware/`. Open `hardware/WebTRX_Controller.kicad_pro` in KiCad 10.x. Full hardware instructions and cautions: `hardware/README_JA.md`.

Firmware and HID specification remain unchanged from prior revision: each mechanical click transmits X axis `0 -> +127` / `0 -> -127`, and F1/F2/PTT produce configurable HID key assignments.

**Verification:** Python static connectivity/clearance checks pass, but **KiCad ERC/DRC, actual KiCad project opening, module mechanical fit, switch matching and hardware operation have not been tested.** Not approved for manufacture.

Current work branch: `feature/ch552-module-encoder-12mm-kicad10`; `main` is not updated.
