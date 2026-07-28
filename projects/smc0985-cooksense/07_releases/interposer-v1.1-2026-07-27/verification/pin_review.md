    date: 2026-07-27
    subject: smc0985-cooksense interposer v1.1 (pre-seal staging archive)
    reviewer: FIX-PASS targeted pin re-confirmation (canon "Verification scoping")
    context-given: pin_audit dossiers regenerated from THIS release's source/ +
                   part.yaml/datasheets; the v1.0 fresh-context verdicts carried
                   forward on a copper state PROVEN identical
    verdict: PASS

# PIN REVIEW — interposer v1.1

## Why this is a targeted re-confirmation and not a new fresh-context review

Canon "Verification scoping": the full multi-lens battery runs once per MATERIAL
design state. **This release moves no copper.** `verification/copper_identity.txt`
measures it: both copper gerbers, both masks, both pastes and both drill files are
GEOMETRICALLY IDENTICAL to the sealed v1.0 (630 copper atoms, 136 mask, 12 paste,
61 holes — same shapes, same coordinates, aperture numbering and statement order
cancelled out). The pad-to-pin question this review exists to answer is therefore
bit-for-bit the same question v1.0's three-agent fresh-context PIN REVIEW answered
PASS on 2026-07-24 (`07_releases/interposer-v1.0-2026-07-24/verification/pin_review.md`,
archived verbatim in `08_reviews/`).

What IS new in v1.1 is the ASSEMBLY payload — CPL rotation, CPL datum, population
set, BOM legibility. The pin-level re-confirmation below regrades every pad-level
claim against THIS release's shipped bytes, and the one integrated fresh-context
adversarial lens for this fix-pass is `verification/redteam_topology.md` /
`redteam_layout.md`.

## Re-measured on `source/interposer.kicad_pcb` (this archive, not 04_kicad)

`pin_audit.py source/interposer.kicad_pcb fab/bom.csv 02_parts` -> 3 dossiers.

### J_MEMBRANE (10FDZ-BT) — PASS
10 PTH pads, drill ø0.900, pad 1.6 mm (annular ring 0.35), one row at y = 20.000,
pitch 2.5400 exactly, x = 25.000 → 47.860 (span **22.8600**). Pin 1 is the RECT
pad. Polarization boss is NPTH ø1.800 at (22.460, 20.000) — colinear with the
row, exactly 2.5400 mm outside pin 1. Matches `02_parts/10FDZ-BT/part.yaml`
(A = 22.86 for 10 circuits, ø0.9±0.05 at 2.54±0.05, ø1.8 boss one pitch outside
circuit 1) and re-reads identically out of `fab/interposer-{PTH,NPTH}.drl`.
Pads 1..10 carry KP_U1..U6, KP_D1..D4 positionally.

### J_CN1_JUMPER (10FDZ-BT) — PASS
Identical footprint, identical orientation (rot 0, boss at x = 22.460 west of
pin 1 at x = 25.000, y = 46.000). Pin columns X-aligned with J_MEMBRANE to the
micron — that alignment IS the straight-through intent. Nets 1..10 positional and
identical to J_MEMBRANE.

### J_KEY_MATRIX (SM10B-GHS-TB, C2683602) — PASS
Side-entry GH header, 10 circuits. Local pads 1..10 at x = −5.625 → +5.625,
y = −1.85, pitch 1.25, pad 0.6 × 1.7 SMD; span 11.25 = eGH A for 10 circuits.
Board anchor (15.0, 33.0) at rot −90, mouth WEST (off-board) — same part, same
rotation and same layer as the sealed main board's J_KEY_MATRIX
(`07_releases/cooksense-v1.4-2026-07-26`), so the ribbon is a 1:1 contact-k →
contact-k harness. Nets 1..10 = KP_U1..U6, KP_D1..D4, matching both ZIFs
pin-for-pin. Both MP mechanical tabs are in NO NET — correct and required on this
board (see `verification/parity.md`).

### The pad-1 map, graded pad-for-pad rather than sampled
`03_src/interposer/audit_board.py` (reads the SAVED board with pcbnew, not the
floorplan that placed it) -> `verification/audit.txt`:
`polarity(pad1-net x30) + mate-direction + pin-order + isolation(10 KP_* nets, 0 zones)` PASS.

## v1.1-specific pin-adjacent items

| item | verdict | evidence |
|---|---|---|
| CPL rotation J_KEY_MATRIX = 270.0 | CORRECT (was 90.0 = 180 out) | board orientation −90 ⇒ board_rot 270; the MEASURED per-LCSC row for C2683602 is offset 0 (`jlc_lcsc_rotations.csv:17`, pad-fit rms 0.0049 mm vs 5.0792 mm next best = 1037× separation); 270 + 0 = **270.0**. `jlc_twin` re-fits the SHIPPED footprint against JLC's own cached model: `fit=0.01mm jlc_offset=0 src=lcsc`. The sealed main board ships the same code at the same board orientation at CPL 270.0 |
| CPL datum J_KEY_MATRIX Mid X 15.25 (anchor is 15.00) | CORRECT | JLC's origin is the pad-centre bounding-box centre, not KiCad's anchor. `assembly_coverage.py` re-derives it from the BOARD TEXT (no pcbnew, no exporter code) and reports worst datum residual **0.00000 mm** over 1 CPL row, tolerance 0.05 mm |
| A-POL channel for C2683602 | two-channel, satisfied | the row's numbering-free corroboration is the unnumbered MP mounting tabs, absent from JLC's numbered set and therefore excluded from the fit on both sides. No JLC order-preview human gate is raised for this board (`rotation_human_gate.txt` not emitted) |
| both ZIFs off the CPL | CORRECT | `fab/cpl.csv` has 1 row; `assembly_coverage.py` A-POS confirms no CPL ref has plated drilled pads with no paste |

## Findings

1. **OPEN, USER-HELD, unchanged and NOT closable from this repo** — 10FDZ-BT
   polarity: which housing end carries circuit 1 relative to the boss. The board
   is internally consistent (both ZIFs identically oriented, and the OEM tail is
   self-keying so the pass-through works either way), but if the convention is
   reversed the `TP_M_U1 … TP_M_D4` labels name the wrong physical conductors.
   Carried as a NAMED OPEN ITEM in `ORDER_README.md` §0, not silently.
2. **OPEN, recorded** — 10FDZ-BT M3 (boss centre → nearest pin centre) measured
   **2.35 mm** on the physical part against the 2.39–2.69 band. The arithmetic and
   the slack budget are written out in `ORDER_README.md` §0; the user has
   explicitly decided to build with the current footprint.
3. v1.0 finding 2 (the stale `SM10B-GHS-TB` `layout.notes` sentence telling the
   reader to tie MP to the isolated ground) was disposed as I4 pre-v1.0-seal.
   Re-checked here: `02_parts/SM10B-GHS-TB/part.yaml` `pins.MP` says FLOAT and the
   board floats them. No board impact either way.

No P0. No P1. PASS for release.
