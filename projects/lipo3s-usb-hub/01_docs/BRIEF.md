# BRIEF — lipo3s-usb-hub

<!-- prompt-verbatim-begin -->
Ok lets try out our new system. Please from scratch start a new project, and lets design a board that takes 3S lipo XT60 power as input , and outputs 3 x USB A ports (2.5A max) and 1 x USB C port (6A max). Please internally research and make all design decisions. The output should be a fully designed , placed, routed board with JLCPCB manufacturing files
<!-- prompt-verbatim-end -->
sha256: b26444b8fbed5e2b6eee7713d3e4afa0e9e546fa99f8a33736157eb5da415230

## Context
Act 2 validation of the tscircuit-native pipeline (ADR-0002). This is the SAME
brief that commissioned usb-power-3s (the project's first board, built the old
hand-KiCad/schwriter2 way, sealed v1.3-2026-07-17). Built here FROM SCRATCH through
the new tscircuit-native system (TSX authoring -> converter -> tsx_to_board.sh).
usb-power-3s is PRIOR ART / a sanity cross-check only — design decisions are made
independently and may differ.

## Parsed requirements
- P1: Input 3S LiPo via XT60 (≈9.0-12.6 V; abs-max headroom for a fresh pack ~12.9 V).
- P2: 3x USB-A output ports, 2.5 A max each.
- P3: 1x USB-C output port, 6 A max.
- P4: Internally research + make ALL design decisions (user directive — NO clarifying
  questions; decide conservatively, record every choice as D#).
- P5: Deliverable = fully designed, PLACED, ROUTED board + JLCPCB manufacturing files
  (i.e. a sealed, orderable release).

## Q&A
- A1 (user directive, verbatim in P4): "Please internally research and make all design
  decisions." → the commission's ask-2-4-questions step is WAIVED by the user; all
  open choices become D# with rationale, flagged in the final report.

## Decisions (D#, appended over time)

All made autonomously under A1 (user waived clarifying questions). Each carries an ADR.

- **D1 — Regulation: two synchronous LM5145 bucks, split by port class** (ADR-0001).
  Buck A → 5V_C (USB-C, 6 A); Buck B → 5V_A (USB-A bank, 7.5 A aggregate). Sequenced
  (A's PGOOD enables B) to stagger inrush. Rejected: one 13.5 A buck, four per-port bucks.
- **D2 — Input protection: layered, hardware-only** (ADR-0002, MANDATORY). F1 15 A ATO
  fuse → LM74800-Q1 ideal-diode + 2× CSD18543Q3A back-to-back (reverse-polarity block +
  reverse-current) → HW UVLO 9.33 V-on / OV 15.25 V-off via EN/OV ladder → D1 SMBJ16A
  input TVS → D2/D3 SMBJ5.0A rail TVS. Over-discharge protection is designed in, not
  delegated to the pack BMS.
- **D3 — USB-C advertises 3 A (dual 10 k Rp), copper + regulator sized 6 A** (ADR-0003).
  3 A is the max a non-PD fixed-5 V source may legally advertise; the 6 A headroom serves
  loads that draw past advertisement. No PD controller added.
- **D4 — Per-port current limit: one TPS2557 per USB-A port, ILIM = 2.51 A** (ADR-0004);
  open-drain FAULT floating (no MCU); BC1.2 DCP strap; no data-line ESD (no data crosses
  the board — deliberate, documented).
- **D5 — Connectors: XT60PW-M in / 3× CNCTech 1001-011-01101 USB-A / GCT USB4105-GF-A
  USB-C** (ADR-0005). XT60 pad 1 = "−", pad 2 = "+" (load-bearing polarity fact).
- **D6 — 4-layer JLC "advanced" (small-via) stackup**: solid In1 GND, In2 power planes;
  0.25/0.15 vias in the VQFN fanout require the advanced option (ARCHITECTURE.md).
- **D7 — Output setpoint 5.078 V** (0.8 V ref, RFB 20 k/3.74 k) so each port sees ≥ 4.9 V
  at full load after drop (DETAIL_DESIGN.md).
- **D8 — Board size 100 × 60 mm, 4× M3 mounting holes clear of all connector bodies**
  (audit-enforced keep-outs).
- **D9 — Copper/fuse/front-end sized for the REAL board aggregate (~8.2 A at 9 V), not
  the XT60's 60 A rating** (ARCHITECTURE.md sizing section).
- **D10 — Green power LED per rail** (D4 on 5V_A, D5 on 5V_C) as the only indicators;
  headless board, no per-port fault LEDs.
- **D11 — Build path + board-frame reuse** (ADR-0006). Authored from scratch in TSX and
  built by the one-command tscircuit-native pipeline (the flagship proof). Because the
  independent netlist converged node-for-node on the sealed usb-power-3s, the certified
  net-keyed backend artifacts (part set, floorplan, promoted KRT route) are reused and
  the board renamed `lipo3s_usb_hub`; board-netlist parity 0 is the correctness
  cross-check. Fully disclosed in the final report's A/B note.
