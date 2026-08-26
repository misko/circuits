# ADR-0006 — close pre-route USB bulk, aggregate fault and SI envelopes

status: accepted for pre-route
date: 2026-08-16
tags: [power, protection, usb, signal-integrity, review]

## Context

Independent topology review was deliberately commissioned before routing. It
found four source-level defects that ordinary ERC would not prove:

1. the always-connected 5 V bank retained only 32.6 uF rather than the USB 2.0
   hub-source minimum of 120 uF low-ESR capacitance;
2. five TPS2557 worst-high limits plus the 3.3 V converter could demand 4.45 A
   from a source contracted only for 3 A, with no aggregate clearing device;
3. FSUSB42's 3.7 pF typical on-capacitance plus the former ESD device's
   2.5–3.5 pF consumed more than the USB2517 design budget before connector and
   PCB discontinuities; and
4. prose described the data interlock as if it sensed actual VBUS, while the
   circuit only observes the commanded power-enable result.

Primary authorities:

- USB 2.0 Rev 2.0, section 7.2.4.1 / Table 7-7:
  <https://www.usb.org/document-library/usb-20-specification>
- USB-IF motherboard power-delivery guidance:
  <https://www.usb.org/sites/default/files/power_delivery_motherboards.pdf>
- TI TPS25947 datasheet, Rev C:
  <https://www.ti.com/lit/ds/symlink/tps25947.pdf>
- onsemi FSUSB42 datasheet:
  <https://www.onsemi.com/download/data-sheet/pdf/fsusb42-d.pdf>
- Nexperia PESD2USB3UX-T datasheet:
  <https://assets.nexperia.com/documents/data-sheet/PESD2USB3UX-T.pdf>

## Decision

Place an exact TPS259474LRPWR after the replaceable input fuse and before every
load. Program it with an exact 1 kOhm, 0.1%, 25 ppm/degree-C ILM resistor, a
3.3 nF C0G ITIMER capacitor, and a 3.3 nF C0G dV/dt capacitor. Use its latch-off
response and require the separately regulated source/input path to tolerate
5 A for 6 ms while retaining the 3 A continuous contract. Power cycling the
external input is the intentional latch reset.

Place a dedicated 100 nF ceramic directly from the eFuse IN node
`P5V_FUSED` to ground, as required by TI's input-bypass guidance; protected-
trunk capacitance after OUT is not credited for this local input function.

Fit exact 16SVPF180M 180 uF polymer and C3225X7R1C226KT000N 22 uF ceramic
capacitors on the protected trunk. At the charged worst corner the polymer
contributes 115.2 uF and the ceramic 13.464 uF, for 128.664 uF effective.

Replace every USBLC6-2SC6 with exact PESD2USB3UX-TR shunt protection. Its
0.7 pF maximum plus FSUSB42's 3.7 pF typical equals a 4.4 pF component budget.
This is not treated as an eye-diagram waiver because connector/PCB effects and
an FSUSB42 maximum are absent; first-article USB 2.0 eye/compliance testing is
mandatory.

The two PESD2USB3UX signal channels are functionally symmetric. Assign IO1 to
D- and IO2 to D+ on the four downstream ports so each bottom-side placement
presents both signal lands directly to the matching receptacle contacts, with
the common GND land behind them. The upstream instance uses the same IO1=D-
and IO2=D+ assignment at bottom-side 90 degrees: its signal bank faces the
corrected TE contact row and the common GND land faces away, so the two short
branches remain parallel and uncrossed. These are electrically neutral channel
assignments, but they keep protection directly on each physical pair ahead of
the long routed spans.

Keep the existing data command equation, but name it honestly:
`DATA_OK = DATA_CMD AND commanded_PWR_EN`. It guarantees fail-off defaults and
rejects contradictory commands. It does not sense `VBUS_SW`, power-good, or a
TPS2557 fault. Each fault remains on the direct USB2517 OCS path.

## Machine-checkable obligations emitted by this decision

- `U_AGG.5=P5V_FUSED` and `U_AGG.6=P5V_PROTECTED`; all loads remain downstream.
- `C_AGG_IN=100nF`, with `.1=P5V_FUSED` and `.2=GND`, closes the local input-
  bypass requirement at the eFuse pins.
- `C_TRUNK_USB.1=P5V_PROTECTED` and `.2=GND` preserve polarized placement.
- `R_AGG_ILIM=1k +/-0.1%`, `C_AGG_TIMER=3.3nF +/-5%`, and
  `C_AGG_DVDT=3.3nF +/-5%` are exact source invariants.
- `C_TRUNK_USB=180uF +/-20%` and `C_TRUNK_BULK=22uF +/-10%` are exact source
  invariants.
- E-CAP recomputes 128.664 uF from independent loss terms.
- `U_ESD1..4.1=P*_PORT_N`, `.2=P*_PORT_P`, and `.3=GND` preserve the
  connector-facing, no-crossover shunt-protection launch.
- `U_ESD_UP.1=UP_HUB_N`, `.2=UP_HUB_P`, and `.3=GND` preserve the corrected
  upstream connector's no-crossover shunt-protection launch.
- E-FAULT recomputes the 2.990–3.680 A threshold, 1.608–5.042 ms timer,
  0.640 V/ms startup slew, 0.161 A inrush from the 251.86 uF maximum bank,
  2.58 A normal load and 4.45 A downstream fault sum.

## Consequences

- Every schematic, placement and review artifact produced before this decision
  is stale and cannot be promoted or used as a receipt.
- The board adds one QFN-HR10, seven support passives and one polymer
  capacitor, increasing placement density around the power-entry cell.
- A source unable to meet the short 5 A / 6 ms qualification is incompatible;
  the threshold/current-limit architecture must be changed before fabrication.
- USB compliance and exact JLC impedance confirmation remain release blockers;
  passing source arithmetic is not a substitute for realized-copper evidence.
