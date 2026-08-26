# USB-controlled debug hub architecture research — 2026-08-15

## Scope and authorities

This record freezes the source-stage interpretation used before schematic
generation. Primary authorities were the USB 2.0 specification and ECNs, the
USB-IF hub design guidance, and the current manufacturer datasheets/checklists
for USB2517I, MCP2221A, MCP23017, FSUSB42, TPS2557 and AP63203Q. Distributor
pages are sourcing evidence only; they are not electrical-design authority.

- USB 2.0 specification: <https://www.usb.org/document-library/usb-20-specification>
- USB 2.0 voltage droop/drop ECN: <https://www.usb.org/sites/default/files/USB20_32_BC12_Drop_Droop_1_4_1.pdf>
- USB2517I datasheet: <https://ww1.microchip.com/downloads/en/DeviceDoc/USB2517-USB2517i-Data-Sheet-00001598C.pdf>
- USB2517I hardware checklist: <https://ww1.microchip.com/downloads/en/DeviceDoc/USB2517-Hardware-Design-Checklist-00004211.pdf>
- MCP2221A datasheet: <https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP2221A-Data-Sheet-DS20005565D.pdf>
- MCP23017 datasheet: <https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf>
- FSUSB42 datasheet: <https://www.onsemi.com/download/data-sheet/pdf/fsusb42-d.pdf>
- TPS2557 product/datasheet: <https://www.ti.com/product/TPS2557>

## Frozen USB topology

USB2517I physical port 1 is the permanently attached MCP2221A management
function. Physical ports 2 through 5 are external user ports 1 through 4.
Physical ports 6 and 7 are disabled. This consumes one upstream cable while
keeping hub-class port power sequencing in every external VBUS-enable equation.
The hub and MCP2221A use factory behavior; this project generates no firmware,
descriptor image or host utility.

## USB2517I checklist translation

The implemented configuration is `CFG_SEL[2:0]=000`: internal defaults,
hardware resistor straps, self-powered operation, LEDs disabled, and individual
port power/overcurrent. `NON_REM[1:0]=01` marks physical port 1 non-removable.
`PRT_SWP1` is strapped high and physical port 1's DM/DP pads carry management
logical D+/D-, respectively; this uses the manufacturer's routing feature to
remove an otherwise unavoidable pair crossover. `PRT_SWP2..7`, `GANG_EN`, and
`BOOST0/1` are strapped low, so the four external ports retain normal physical
DM=D- and DP=D+ polarity. Both D+ and D- of
physical ports 6 and 7 receive the documented 10 kOhm pullups to 3V3_MAIN;
their PRTPWR and OCS pins remain unconnected. TEST and the unused LED-B pins
remain unconnected.

The reset network is 10 kOhm to 3V3_MAIN and 1 uF to ground. VBUS_DET senses
upstream VBUS through a 47 kOhm / 100 kOhm divider and has no conductive path
to the self-powered trunk. RBIAS is exactly 12 kOhm, 1%. The oscillator is an
exact 24 MHz crystal with a 1 MOhm feedback resistor and two selected 18 pF C0G
load capacitors.

Hub supply support is explicit rather than hidden in a generator: four 100 nF
VDDA33 capacitors plus one shared 1 uF, 100 nF + 1 uF at VDD33CR, 100 nF at
VDD33, 100 nF at VDD33PLL, and 1 uF each at VDD18 and VDD18PLL. All functional
grounds and connector shells use one uninterrupted board-ground system.

## Management and safe-state logic

MCP2221A is powered only by internal hub port 1 `VBUS_CTRL`; VUSB receives
330 nF, RESET receives an external 10 kOhm pullup, and its factory USB current
declaration remains truthful. MCP23017 shares `VBUS_CTRL`, uses 4.7 kOhm I2C
pullups, address `000`, and a 10 kOhm RESET pullup. Unused GPB/interrupt pins
remain unconnected.

Every `PWR_CMD` and `DATA_CMD` has an external pulldown. External-port TPS2557
enable is `hub PRTPWR AND PWR_CMD`. Data connection is commanded `PWR_EN AND
DATA_CMD`; a 2N7002 converts that active-high result into active-low FSUSB42 OE.
An OE pullup disconnects data whenever logic is absent. Thus reset and partial
power always resolve to fully disconnected, while `PWR_CMD=1, DATA_CMD=0`
deliberately provides power-only operation. This is a command-state interlock,
not a measurement of switched VBUS or power-good; each TPS2557 fault remains
on the hub OCS path.

## Power and manufacturing bounds

The source requirement is regulated SELV 5.20–5.25 V at `P5V_RAW`, at least
3 A continuous and qualified for 5 A / 6 ms transients. Exact Littelfuse
0297004.WXNV provides a replaceable 4 A input fuse. A TPS259474L aggregate
eFuse provides reverse-current blocking and a calculated 2.990–3.680 A
latch-off threshold with 1.608–5.042 ms fault timing. A 180 uF polymer plus
22 uF X7R bank retains 128.664 uF at the charged life/bias/temperature corner,
above the USB 2.0 120 uF hub-bypass minimum. The full derivation and the move
from the original source-stage architecture are recorded in ADR-0006.

TPS2557 uses exact 165 kOhm 1% ILIM resistors, giving the reviewed approximate
535 mA minimum, 667 mA typical and 794 mA maximum window. AP63203Q uses the
manufacturer-recommended 3.3 uH inductor, 10 uF input, 100 nF bootstrap and two
22 uF output capacitors. The provisional fabrication target is JLCPCB
four-layer advanced because USB2517I is a 0.50 mm-pitch QFN64; the order-time
stackup and 90 Ohm differential geometry remain release evidence, not a
source-stage assumption.

## 2026-08-16 pre-route correction addendum

Independent review found the original USBLC6-2SC6 protection too capacitive in
series with the FSUSB42 channel. The current source replaces all five arrays
with PESD2USB3UX-TR shunt devices (0.7 pF maximum). FSUSB42's 3.7 pF typical
plus that protector is a narrow 4.4 pF component budget; connector/PCB
discontinuities and an unpublished FSUSB42 maximum are not waived, so USB 2.0
eye/compliance testing remains mandatory on first articles.
