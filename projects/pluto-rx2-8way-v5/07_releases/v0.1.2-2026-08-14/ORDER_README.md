# Pluto RX2 eight-way v5 — hardware design archive and JLC work order

## STOP — DO NOT ORDER THIS ARCHIVE AS-IS

SOURCING: CLEAR
ORDER VERDICT: DO-NOT-ORDER
DESIGN VERDICT: SOUND

## Supersession record

This v0.1.2 verification-only archive supersedes `v0.1.1-2026-08-14` to
correct the JLC digital-twin placement of J2-J10. The earlier fallback averaged
incompatible repeated-pad number groups and shifted every SMA model 1.796 mm;
it did not indicate a PCB, drill or CPL defect. The corrected renderer anchors
the unique signal hole, pad 1 to pad 1 at zero degrees, and the independent
A-RENDER overlay passes. The `fab/`, `source/`, `pdf/` and `3d/` payloads are
byte-identical to v0.1.1. No schematic, PCB, footprint, part, placement,
Gerber, drill, BOM, CPL, 3D model or order verdict changed.

This is a hardware-only design archive. Local schematic, PCB, fabrication,
assembly-data and reproducibility gates pass, but the JLCPCB uploader preview,
controlled-impedance/process acknowledgements and physical first-article tests
have not happened. Those are mandatory stop gates before payment.

Firmware is not included or qualified. The fitted STM32C011F4P6 may arrive
blank. U2 and keyed SWD connector J11 provide a programming interface, but this
archive makes no claim that autonomous dwell switching operates. Do not infer
programmed behavior from the presence of the controller.

Product boundary: receive-only, one common Pluto RX SMA connected to zero or
one of eight antenna SMAs through a PE42482A-X absorptive SP8T. Desired board
path is 100 MHz–5.9 GHz. The user's AD9363-as-AD9361 extended-frequency use is
accepted project risk and is not an ADI-guaranteed system claim.
All nine RF centre conductors must remain at 0 VDC: this board contains no RF
DC-blocking capacitors. A DC-biased antenna or receiver requires an externally
qualified bias tee/DC block and is outside this archive's direct-use boundary.

PCB: 90 x 65 mm, four layers, 1.6 mm, JLC04161H-7628 controlled-impedance
basis, ENIG. Assembly: quantity five, top side, 13 BOM rows, 29 placements,
including nine exact Amphenol 901-143-6RFX through-hole SMA connectors.

Before an order is released, complete sections 1–3 and obtain a renewed order
verdict. Catalog stock is necessary evidence, not uploader allocation.

## 1. PCB order options

- Fabricator: JLCPCB; four copper layers; 1.6 mm finished thickness; advanced
  process; ENIG; green mask and white legend unless procurement records an
  equivalent controlled choice.
- Select JLC04161H-7628 and controlled impedance for the top-layer CPWG. The
  source geometry is 0.295 mm finished trace width and 0.200 mm coplanar gap
  over continuous In1.Cu, calculated as 49.9719 ohms using JLC's retained live
  calculator inputs. Confirm the actual order form reproduces that stackup and
  geometry; the published-versus-live solder-mask input discrepancy is not a
  waiver.
- Upload `fab/pluto_rx2_8way_v5_gerbers.zip`. Confirm 11 Gerber layers, PTH and
  NPTH drills, the 90 x 65 mm outline, four copper layers, visible plane pours
  and no unexpected DFM edits.
- Select copper-paste fill and copper cap for the complete 0.25 mm drill family
  only: exactly nine 0.45/0.25 mm U1 exposed-pad vias. Do not fill or cap any
  of the 629 ordinary 0.45/0.20 mm route, stitch, fence or plane-return vias.
- Paste the exact fabrication remark from `fab/order_notes.txt` and obtain a
  written/process-preview acknowledgement before payment.

## 2. Assembly upload and human preview gate

- Upload `fab/bom.csv` and `fab/cpl.csv` for quantity five. JLC must resolve
  exactly 13 BOM rows and 29 top-side designators.
- Save JLC's resolved BOM table and compare every code/value/ref group with
  `verification/bom_echo_gate.txt`. Any redirect, substitute, shortage,
  omitted designator or quantity mismatch stops the order.
- Confirm exact C429844 is allocated for J2–J10 and accepted on JLC's
  through-hole connector wave/manual-assembly service. The project retains the
  Amphenol Rev-C manufacturer land: 1.50 mm signal and 1.70 mm ground drills.
  JLC catalog CAD uses 1.60/1.80 mm. Any request to change the footprint stops
  this release for engineering review.
- Inspect the current JLC placement preview for U1 pin 1, U2 pin 1, D1
  cathode, J1 orientation, J11 pin 1/keying and all nine outward-facing SMA
  bodies. Local rotations are sourced 29/29, but only the uploader preview
  proves JLC's current interpretation.
- Confirm the seven non-CPL board objects are only FID1–FID3 and H1–H4.
  Every electrical component and all nine SMA connectors must remain placed.
- Re-run same-day stock/allocation. The sealed catalog measurement passes
  13/13 rows for five boards but does not predict JLC's assembly allocation.

## 3. First article and acceptance

- Build five first articles only after sections 1–2 pass. Follow
  `verification/FIRST_ARTICLE_TEST_PLAN.md` in full.
- Perform unpowered inspection and resistance checks, then current-limited
  first power from the board's power-only USB-C input. Neither Raspberry Pi
  GPIO nor an ST-LINK may source target power through J11.1/VTref.
- Use an explicitly approved, separately controlled debug/test method to place
  U1 in each legal state. No firmware is supplied by this archive.
- Calibrate a VNA at the SMA mating planes and retain Touchstone data for all
  eight selected paths and required off states over 100 MHz–5.9 GHz.
- Required article targets are: insertion loss no more than 2.0 dB through
  1 GHz and 3.5 dB at 5.9 GHz; path spread no more than 1.5 dB; common-to-off
  isolation at least 30 dB through 4 GHz and 25 dB at 5.9 GHz; active-path
  return loss at least 10 dB.
- A failed electrical, assembly, RF or process result reopens the design.
  Production remains HOLD until first-article evidence passes.

## 4. Integrity and recovery

`MANIFEST.txt` hashes every archived file except itself and names the exact
committed source state. `source/` contains the routed KiCad board, schematic,
project/rules, authoring TSX, exported netlist, local footprint table and
vendored project footprint library. `pdf/`, `3d/` and `verification/` allow
inspection without rerunning network-dependent sourcing or twin stages.
