# Pluto RX2 eight-way v5 — hardware design archive and JLC work order

## STOP — DO NOT ORDER THIS ARCHIVE AS-IS

SOURCING: CLEAR
ORDER VERDICT: DO-NOT-ORDER
DESIGN VERDICT: SOUND

## Supersession record

This v0.2.1 hardware archive supersedes `v0.1.2-2026-08-14`. It adds the
populated J12 two-pin bench-power input and deliberately changes the top RF
copper: seven formerly sharp two-corner paths now use 14 native tangent arcs,
while the two direct paths remain straight. The board has migrated to blocking
`rf-module-v1`; the smallest realized bend radius is 3.350 trace widths against
the 3.0 minimum, with no exception.

The exact source and realized RF evidence covers all nine RF nets. Every route
remains branch-free 0.295 mm F.Cu with zero RF vias. Both flanks of all nine
routes pass the independent saved-board fence audit; the worst aperture is
1.3979 mm against 1.4000 mm. Final KiCad DRC is 0/0/0. Schematic, parts,
outline and board stackup retain the reviewed architecture; the generated
schematic, board, BOM, CPL, Gerbers, drills, PDFs and STEP all include J12.

Physical SMA registration is now a separate blocking claim. `P-MODEL-REG`
binds the exact native Amphenol STEP by SHA-256, compares its independently
measured pixels with F.Fab and F.CrtYd, and requires every drilled attachment
centre to lie inside the body. J2–J10 pass 9/9 bodies and 45/45 drilled centres;
the measured body exceeds no courtyard. The raw JLC C429844 catalog twin is
retained only as diagnostic catalog-CAD evidence: its converted WRL has a bad
internal XY origin. The former green/pink pass compared two channels derived
from that same bad mesh and therefore did not prove physical placement.

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
basis, ENIG. Assembly: quantity five, top side, 14 BOM rows, 30 placements,
including nine exact Amphenol 901-143-6RFX through-hole SMA connectors and the
exact C225477 J12 through-hole bench-power header.

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
  of the 615 ordinary 0.45/0.20 mm route, stitch, fence or plane-return vias.
- Paste the exact fabrication remark from `fab/order_notes.txt` and obtain a
  written/process-preview acknowledgement before payment.

## 2. Assembly upload and human preview gate

- Upload `fab/bom.csv` and `fab/cpl.csv` for quantity five. JLC must resolve
  exactly 14 BOM rows and 30 top-side designators.
- Save JLC's resolved BOM table and compare every code/value/ref group with
  `verification/bom_echo_gate.txt`. Any redirect, substitute, shortage,
  omitted designator or quantity mismatch stops the order.
- Confirm exact C429844 is allocated for J2–J10 and exact C225477 is allocated
  for J12; both must be accepted on JLC's through-hole connector wave/manual-
  assembly service. The project retains the Amphenol Rev-C manufacturer land:
  1.50 mm signal and 1.70 mm ground drills. JLC catalog CAD uses 1.60/1.80 mm.
  Any request to change the footprint stops this release for engineering
  review.
- Inspect the current JLC placement preview for U1 pin 1, U2 pin 1, D1
  cathode, J1 orientation, J11 pin 1/keying, J12 pin 1 at the `+5V` silk, and
  all nine outward-facing SMA bodies. Local rotations are sourced 30/30, but
  only the uploader preview proves JLC's current interpretation.
- Confirm the seven non-CPL board objects are only FID1–FID3 and H1–H4.
  Every electrical component and all nine SMA connectors must remain placed.
- Re-run same-day stock/allocation. The sealed catalog measurement passes
  13/13 rows for five boards but does not predict JLC's assembly allocation.

## 3. First article and acceptance

- Build five first articles only after sections 1–2 pass. Follow
  `verification/FIRST_ARTICLE_TEST_PLAN.md` in full.
- Perform unpowered inspection and resistance checks, then current-limited
  first power from one input at a time. USB-C J1 and bench header J12 are
  non-isolated alternatives and must never be energized together. Neither
  Raspberry Pi GPIO nor an ST-LINK may source target power through J11.1/VTref.
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
inspection without rerunning network-dependent sourcing or twin stages. The
high-resolution final images use the native project models; the raw supplier
catalog twin is isolated under `verification/jlc_catalog_twin/` and is not
physical-registration evidence.
