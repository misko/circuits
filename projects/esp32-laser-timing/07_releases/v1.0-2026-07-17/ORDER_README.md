# ORDER_README — esp32-laser-timing v1.0 (JLCPCB)

## PCB order
- Upload `esp32_laser_timing_gerbers.zip` (2-layer; 11 files incl. PTH+NPTH drills).
- Options: **2 layers**, 1.6mm FR-4, 1oz, HASL or ENIG (either), **standard
  tolerances — NO advanced/small-via option needed** (min drill on board =
  0.3mm vias; P10 default 2-layer rules hold).
- Quantity: 5 (stock check margin assumed 5x).

## Assembly (economic, top side only)
- Upload `bom.csv` + `cpl.csv` to the assembly step (NOT inside the zip).
- 20 coded lines / 66 placements. 10 BOM lines are deliberately UNCODED —
  hand-solder THT (below). If the uploader flags them, mark Do-Not-Place.
- Qty 0 + no price on the ESP32/LM339 lines = "confirm manually", not
  stock-out — click through and confirm (exact MPNs are in the BOM).

## Rotation / polarity preview checklist (DO NOT SKIP)
The rotations DB corrections applied: SOT-23(-90), SOT-23-6(-90),
SOIC-14(+270), USB-C HRO(+180). The twin's EDA-frame fit disagrees with
the DB on these families (EDA-zero vs assembly-zero gap) — the DB rows are
prior-order-verified, but EYEBALL EVERY ONE in JLC's 3D preview:
- [ ] U1 ESP32 module: antenna end overhangs the board's north edge; pin 1
      (dot) at north-west.
- [ ] U3 LM339 SOIC-14: pin-1 dot at the north-west corner of the SOIC.
- [ ] Q1/Q2/Q3 SOT-23: body orientation must match the F.Fab drawing in
      assembly_top.pdf (lone pad = drain on the north side of our pattern).
- [ ] D1 USBLC6 SOT-23-6: pin 1 top-left vs our silk dot.
- [ ] D2 green LED 0805: cathode marker toward GND = the side AWAY from
      R4. Twin model rendered unmarked — the JLC preview is the only
      machine-independent check (POLARITY-CHECK finding).
- [ ] C11 100uF electrolytic: black-stripe half (NEGATIVE) must be the
      side AWAY from the "+" silk marker. Twin render shows consistent;
      re-verify in preview.
- [ ] J1 USB-C: shell overhangs the west edge.
- [ ] SW1/SW2 tactiles: square body centered on 4 pads (orientation-free).

## Hand-solder list (after boards arrive)
- 9x KF128L-3.5-2P 3.5mm screw terminals (LCSC C474930, order separately
  ~$0.15/ea): J4-J6 (LASER), J7-J9 (PHOTODIODE), J10-J12 (BUTTON). Wire
  openings face the board edge.
- 1x 2.54mm 1x4 FEMALE header socket (e.g. LCSC C2718488): J2 OLED.
- Note: the Phoenix-pattern holes are 1.2mm vs Kefa's 1.3mm recommended —
  pins fit (0.94mm diagonal), push straight, don't force at an angle.

## First-power ritual (LASER SAFETY INCLUDED)
1. **Nothing connected to any terminal.** Multimeter before power:
   continuity USB-C shell -> GND test point; NO short 5V->GND or
   3V3->GND (beyond capacitor-charge blip).
2. Plug USB-C into a current-limited port (or USB power meter). Expect
   tens of mA idle, PWR LED on, no hot parts (thumb-test LDO U2).
3. Verify 5.0V and 3.30V at the labeled test points.
4. **VERIFY LASERS OFF AT BOOT BEFORE CONNECTING LASER MODULES** (safety):
   with terminals empty and the board booted (programmed or not — 100k
   gate pulldowns hold the FETs off either way), continuity-check each
   LASER terminal SW pin to GND: must read OPEN (FET off). Only then wire
   laser modules, mounted on the jig, apertures pointed safely; enable
   channels from firmware one at a time. Never look into apertures.
5. Photodiode sanity: with a BPW34 wired (cathode->5V pin, anode->PD pin),
   ambient light reads ~0.05-0.5V at the PD node; a 650nm spot drives it
   >0.7V. COMP test point: HIGH (3.3V) when lit, LOW when blocked — scope
   it while chopping the beam.
6. Stock moves: on the actual order day re-run
   `python3 ~/.claude/skills/jlcpcb-fab/scripts/jlc_stock_check.py 06_build/fab/bom_jlc.csv`

## Inrush note (ADR-0001)
On-board 5V capacitance (~150uF) exceeds the USB 10uF attach guideline —
common for bench boards; power from a real USB port/hub (current-limited),
not a bare unprotected 5V brick with a marginal cable.
