# KiCad 10 static checks / Rev.A

| Check | Status |
|---|---|
| Embedded formal standard symbols Device:RotaryEncoder, Switch:SW_Push, Connector_Generic:Conn_01x06 | Present |
| S-expression parentheses and quotation balancing | PASS, static |
| Reference SW1 / SW2 / SW3 / SW4 / J1 and 15 signal-side wire endpoints | PASS, static |
| Global label endpoints on wires, 50 mil alignment | PASS, static |
| Ref/symbol pin mapping | PASS, static |
| KiCad 10 GUI file open | NOT RUN (environment lacks KiCad GUI) |
| KiCad 10 ERC: 0 errors / 0 warnings | NOT RUN (not claimed) |
| Footprint matching, KiCad PCB, DRC | NOT DONE |
| USB HID and real hardware | NOT RUN |

The module supplies power internally and is represented as a 6-signal external device; PWR_FLAG cannot be inferred as required for this passive schematic. Re-evaluate if circuit power pins are added.

Run on Windows after opening/saving the KiCad project:
```powershell
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc .\WebTRX_Controller.kicad_sch -o .\ERC_report.txt
```
