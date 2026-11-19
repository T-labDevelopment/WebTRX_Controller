# KiCad Rev.A.2 verification

- Python static checker: PASS (schematic, labels, 50mil grid, pin numbers, PCB pad-to-net connectivity, geometric approximation)
- Schematic built with A1 WeAct CH552 20-pin custom symbol + footprint, SW1 EC12E2420801 custom symbol + footprint, SW2/SW3/SW4 standard Switch:SW_Push + Button_Switch_THT:SW_PUSH-12mm.
- KiCad 10 GUI open and KiCad 10 ERC/DRC: NOT RUN (KiCad not installed on this runner)
- PCB footprint clearance/USB cable access/mechanical fit: NOT VERIFIED
- PCB routed trial layout: NOT approved for production

Run `python tools/validate_static.py` in `hardware/` then run KiCad 10 `kicad-cli sch erc` and `kicad-cli pcb drc` locally before manufacturing.
