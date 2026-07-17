# BRIEF — esp32-laser-timing

status: delivered
current_release: 07_releases/v1.0-2026-07-17

Commissioned: 2026-07-16, via /pcb-design. Prompt sha256: 221b4ba9cc4c0d5caae4484dd7ca0dffd051d64b5a9a320b4e57c02f81fdd899

<!-- prompt-verbatim-begin -->
BOARD DESIGN BRIEF: ESP32 laser timing bench controller

PURPOSE
Bench instrument that timestamps laser beam interruptions caused by moving
shutter blades. Three laser modules and three photodiodes mount off-board on a
test jig and connect via screw terminals. The board powers the lasers,
conditions photodiode signals into clean digital edges, timestamps them on an
ESP32, drives a small OLED status display, and reads three off-board pushbuttons.

SOURCING RULES
- Every component must be in stock at https://jlcpcb.com/parts/in-stock-parts
- Strong preference for JLCPCB Basic parts. Minimize the count of unique
  Extended parts; each unique Extended part adds a setup fee.
- Among equivalent crosses, choose highest stock quantity at lowest unit cost.
- All SMD on one side for economic assembly. Through-hole connectors
  acceptable as hand-solder items.

MCU
- ESP32-S3-WROOM-1, cheapest in-stock flash/PSRAM variant (N8R2 class or
  better).
- Native USB via USB-C connector, no UART bridge chip. 5.1k pulldowns on both
  CC pins. ESD protection array on D+/D-.
- BOOT (GPIO0) and RESET tactile pushbuttons on board.
- 3.3V rail from LDO (AMS1117-3.3 or best basic-part cross, 1A class).
  10-22uF on LDO input and output.

POWER
- USB-C 5V is the sole input. Budget: 3 lasers at 40mA plus ESP32 WiFi peaks,
  under 1A total.
- 5V rail feeds laser terminals and comparator supply. At least 100uF bulk
  capacitance on the 5V rail near the laser terminals.
- 100nF ceramic at every IC power pin.

LASER CHANNELS (x3)
- One 2-position screw terminal per channel (3.5mm or 5mm pitch), supplying
  5V and switched ground.
- Low-side N-channel MOSFET per channel, SOT-23 logic-level basic part
  (AO3400 class). Gate from MCU GPIO through 100R series resistor, 100k gate
  pulldown so lasers stay off at boot. Firmware may hold channels on
  continuously or gate them per measurement.

PHOTODIODE CHANNELS (x3)
- One 2-position screw terminal per channel. Off-board sensor is a BPW34 PIN
  photodiode in photoconductive mode: terminal A ties the cathode to 5V,
  terminal B brings the anode to the on-board load network.
- Load: 1k resistor from anode node to ground. Expected photocurrent under
  direct 650nm 5mW illumination is roughly 0.5-3mA, giving 0.5-3V at the node.
  Blocked-beam level is near 0V.
- Comparator: one LM339 (quad, basic part) covers all three channels.
  IMPORTANT: power the LM339 from the 5V rail, not 3.3V. Its input
  common-mode range tops out about 1.5V below supply, and the signal node
  swings to 3V. On 5V supply the full swing stays inside common-mode range.
- Per channel: signal node to non-inverting input. Inverting input to a fixed
  threshold of approximately 0.7V from a resistor divider off 3.3V.
  Hysteresis of roughly 100mV via positive feedback resistor. Open-collector
  output pulled up to 3.3V with 10k, keeping MCU-safe logic levels.
- No capacitors anywhere in the signal path. Signal chain must preserve
  microsecond edges.
- Fourth comparator unused: tie its inputs to defined levels, output floating.
- Option, only if adjustability is wanted: replace the three fixed dividers
  with one or three 10k trimmers, accepting the Extended-part fee.

PIN ASSIGNMENT CONSTRAINTS
- The three comparator outputs must land on GPIOs usable for hardware edge
  timestamping (MCPWM capture or RMT input on ESP32-S3).
- Avoid strapping pins GPIO0, GPIO3, GPIO45, GPIO46 for any external signal.
- Avoid GPIO19 and GPIO20 (USB D-/D+).
- Final pin map must be documented and silkscreened.

OLED HEADER
- 4-position 2.54mm female header for a 0.96 inch SSD1306 I2C module.
- Pin order GND, VCC(3.3V), SCL, SDA, clearly silkscreened. Note: modules
  exist with the first two pins swapped; label prominently.
- 4.7k I2C pullups to 3.3V on board. Any two free GPIOs, labeled.

BUTTON CHANNELS (x3)
- One 2-position screw terminal per channel for off-board momentary switches
  on wire runs up to 50cm.
- Per channel: 10k pullup to 3.3V, switch closes to ground, 100nF debounce
  capacitor from the input node to ground, 1k series resistor into the GPIO.

MECHANICAL
- 2 layer board, JLCPCB default 2-layer design rules.
- M3 mounting holes in all four corners.
- Every terminal function silkscreened in plain words.
- Test points on each comparator output, 5V, 3.3V, and GND.

DELIVERABLES
- KiCad 9 project: schematic, PCB, all symbols and footprints bundled in
  project-local libraries. Must open with no missing-library errors.
- Gerbers, JLCPCB-format BOM with LCSC part numbers, pick-and-place file.
- README with the final MCU pin map.
- Design passes KiCad ERC and DRC clean.
<!-- prompt-verbatim-end -->

## Parsed requirements

- P1: Bench instrument: timestamp laser-beam interruptions; 3 lasers + 3
  photodiodes off-board via screw terminals; ESP32-S3 timestamps; OLED
  status; 3 off-board pushbuttons.
- P2 (sourcing): all parts in stock at JLC; Basic parts strongly preferred,
  minimize UNIQUE Extended count; among crosses pick highest stock at lowest
  cost; all SMD one side; THT connectors OK as hand-solder.
- P3 (MCU): ESP32-S3-WROOM-1 cheapest in-stock N8R2-or-better; native USB
  via USB-C (no UART bridge); 5.1k CC pulldowns; ESD array on D+/D-; BOOT +
  RESET tactiles; 3.3V from 1A-class basic LDO (AMS1117-3.3 or best cross)
  with 10-22uF in/out.
- P4 (power): USB-C 5V sole input, <1A total; 5V feeds lasers + LM339;
  >=100uF bulk near laser terminals; 100nF at every IC power pin.
- P5 (lasers x3): 2-pos screw terminal each (3.5 or 5mm), 5V + switched GND;
  low-side SOT-23 logic-level NFET (AO3400 class); 100R gate series, 100k
  pulldown (off at boot).
- P6 (photodiodes x3): 2-pos terminal each; BPW34 photoconductive: cathode
  to 5V at terminal, anode to on-board 1k load to GND (0.5-3V lit, ~0V
  blocked); ONE LM339 on the 5V RAIL (common-mode requirement is
  user-pinned); per channel: +in = signal node, -in = ~0.7V divider off
  3.3V, ~100mV hysteresis via positive feedback, open-collector out pulled
  to 3.3V with 10k; NO capacitors in the signal path (microsecond edges);
  4th comparator inputs tied to defined levels, output floating.
- P7 (pins): comparator outputs on MCPWM-capture/RMT-capable GPIOs; never
  use GPIO0/3/45/46 for external signals; avoid GPIO19/20 (USB); pin map
  documented AND silkscreened.
- P8 (OLED): 4-pos 2.54mm female header, order GND,VCC(3.3),SCL,SDA with
  prominent silk (swapped-pin modules exist); 4.7k I2C pullups to 3.3V;
  any two free GPIOs, labeled.
- P9 (buttons x3): 2-pos terminal each, wire runs to 50cm; 10k pullup to
  3.3V, close-to-GND, 100nF debounce at node, 1k series into GPIO.
- P10 (mech): 2-layer, JLC default 2-layer rules; M3 holes all 4 corners;
  every terminal silkscreened in plain words; test points on each
  comparator output, 5V, 3.3V, GND.
- P11 (deliverables): KiCad project with project-local libs (no
  missing-library errors); gerbers, JLC BOM with LCSC codes, CPL; README
  with final pin map; ERC and DRC clean.

## Q / A

- Q1: Threshold adjustability — fixed dividers or trimmers?
  A1 (user, 2026-07-16): **Fixed 0.7V dividers** off 3.3V; thresholds
  changed by resistor swap; zero Extended parts for this function.
- Q2: KiCad version — brief says KiCad 9, pipeline is KiCad 10.
  A2 (user, 2026-07-16): **KiCad 10 format is acceptable**; project-local
  libs, opens clean in KiCad 10; gerbers/BOM/CPL version-independent.
- Q3: Screw terminal pitch?
  A3 (user, 2026-07-16): **All 3.5mm**, one terminal family (qty 9).

- Q4 (implicit): how to handle open/future design choices?
  A4 (user, 2026-07-17): "please make reasonable decisions for these open
  choices and record your rationale" — FULL DELEGATION: engineer decides,
  records D# with rationale (ADR when substantive), flags in final report.

## Decision register

All agent decisions below are made under the A4 full delegation; rationale
in the linked ADR/doc.

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| D1 | LM339 has NO Basic option at JLC → ST LM339DT C71036 (Extended, cheapest/deep-stock cross) | agent (A4; P2 cross rule) | decisions/0002 |
| D2 | All passives 0805 UNI-ROYAL/YAGEO/Samsung Basic (0603 Basic 1k+10k stock=0 on 2026-07-17) | agent (A4) | decisions/0003 |
| D3 | 5V bulk = 100uF/16V SMD aluminum electrolytic C2887276 (Extended; no Basic ≥100uF exists) | agent (A4; P4 pins ≥100uF) | decisions/0003 |
| D4 | Protection posture: USBLC6 pin-5 clamps VBUS; no polyfuse/inrush device; PD lines protected by LM339 36V-rated inputs; no parts added beyond brief | agent (A4) | decisions/0001 |
| D5 | Pin map: COMP=IO4/5/6, LASER=IO7/15/16, BTN=IO17/18/21, I2C=IO1(SDA)/IO2(SCL); MCPWM/RMT are GPIO-matrix-routed so these satisfy P7 | agent (A4) | decisions/0004 |
| D6 | Thresholds: three independent 10k/2.7k dividers (0.702V); hysteresis Rf=33k (≈88mV ≈ "roughly 100mV") | agent (A4; P6/A1) | DETAIL_DESIGN |
| D7 | EN reset RC = 10k + 1uF; BOOT/RESET tactiles = TS-1187A-B-A-B (Basic) | agent (A4) | DETAIL_DESIGN |
| D8 | Power LED (green 0805 + 1k on 3V3) added — bring-up aid, Basic parts, no GPIO | agent (A4) | decisions/0005 |
| D9 | USB-C = HRO TYPE-C-31-M-12 C165948 (Extended; std KiCad footprint matches MPN) | agent (A4; P2) | decisions/0005 |
| D10 | Terminals = KF128L-3.5-2P x9 + 1x4 female socket, hand-solder THT; socket deliberately uncoded | agent (A4; A3/P2) | decisions/0005 |
| D11 | Board 92x62mm, 2-layer, B.Cu = continuous GND pour; antenna overhangs north edge | agent (A4; P10) | ARCHITECTURE |
| D12 | Module/LDO caps consolidated on 22uF 0805 Basic (C45783); no separate 10uF line | agent (A4) | DETAIL_DESIGN |
| D13 | 4th comparator: +IN→GND, −IN→VTH3 (0.7V defined level; routable), output floating | agent (A4; P6) | decisions/0002 |
| D14 | MCU = ESP32-S3-WROOM-1-N8R2 C2913204 ($5.39, 19.6k stock) — cheapest in-stock R2-or-better | agent (A4; P3) | decisions/0003 |
| D15 | ESD = UMW USBLC6-2SC6 C2687116 (clone; figure-verified on crowsync; ST C7519 alternate) | agent (A4; P2/P3) | decisions/0001 |

## Log

- 2026-07-16: commissioned; folders + contracts created from canonical set.
- 2026-07-17: A4 delegation received; D1–D15 recorded; ADRs 0001–0005
  written; parts extracted (02_parts/), design docs written.
- 2026-07-17: all gates green (ERC 0, AUDIT PASS, DRC 0/0/0+parity, twin
  exit 0, pin reviews zero FAIL, render review dispositioned); release
  v1.0-2026-07-17 cut at git 8e4dd80, tag elt-v1.0.
