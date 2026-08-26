# CPL ACCEPTANCE GATE + COPPER-IDENTITY PROOF — v1.4-2026-07-25

The fix-claim evidence the 07_releases contract requires: the measurement that
proves v1.4 changed EXACTLY what it says it changed, by a method able to
falsify it. Produced 2026-07-25 against the UNCHANGED sealed board
`04_kicad/crow_recorder_central_v2.kicad_pcb`.

## 0. Why v1.4 exists — v1.3 is DO-NOT-ORDER

v1.3 ships SEVEN CPL rows 180 degrees off, and they are **every fine-pitch part
on the board**: the consigned XU316 TQFP-128 SoC (0.4 mm pitch), both PCM1865
TSSOP-30 ADCs (0.5 mm), the SPI flash, both bucks, and the USB ESD array. v1.0,
v1.1 and v1.2 all shipped these CORRECTLY at 270 degrees; v1.3 "fixed" a
non-defect and turned a good board into a bad one.

ROOT CAUSE (fixed at source before this release, commit 1b69760):
`jlc_twin.xform()` used the OPPOSITE handedness to the operator KiCad actually
applies to a rotated footprint's pads, so every `jlc_offset` the twin reported
was NEGATED. The two forms are mathematically identical at 0 and 180 (both
sign-invariant under the negation) and 90/270 negate into each other — so the
error was invisible on more than half the fleet and EXACTLY 180 degrees wrong on
the rest. `jlc_lcsc_rotations.csv` had been POPULATED FROM that function, so six
of its rows inherited the negation (canon M1: the authority table WAS the
checker's output, and an external reviewer reading it was misled). The table was
corrected in e0d735c; the machine that poisoned it in 1b69760, pinned by two
RED-verified tests against pcbnew.

The fingerprint of that root cause is visible in the diff below: the SEVEN rows
that move are all 90-or-270-valued, and Q1/Q2/U9 — whose per-LCSC values are
**180**, which is sign-invariant under the negation — do NOT move. A defect that
touched some other set of rows would not have that shape.

## 1. CPL diff — the gate: EXACTLY SEVEN changed cells, no more, no fewer

```
$ diff crow-recorder-central-v2-v1.3-2026-07-24/fab/cpl.csv \
       crow-recorder-central-v2-v1.4-2026-07-25/fab/cpl.csv
99c99
< D_USB,C90627,USON-10_2.5x1.0mm_P0.5mm,97.0,-126.0,top,90.0
---
> D_USB,C90627,USON-10_2.5x1.0mm_P0.5mm,97.0,-126.0,top,270.0
168c168
< U1,C6938291,TQFP-128_14x14mm_P0.4mm_EP_XU316,90.0,-102.0,top,90.0
---
> U1,C6938291,TQFP-128_14x14mm_P0.4mm_EP_XU316,90.0,-102.0,top,270.0
170,171c170,171
< U2,C181312,TSSOP-30_4.4x7.8mm_P0.5mm,62.0,-62.0,top,90.0
< U3,C181312,TSSOP-30_4.4x7.8mm_P0.5mm,128.0,-62.0,top,90.0
---
> U2,C181312,TSSOP-30_4.4x7.8mm_P0.5mm,62.0,-62.0,top,270.0
> U3,C181312,TSSOP-30_4.4x7.8mm_P0.5mm,128.0,-62.0,top,270.0
173c173
< U5,C82317,SOIC-8_5.3x5.3mm_P1.27mm,112.0,-114.0,top,90.0
---
> U5,C82317,SOIC-8_5.3x5.3mm_P1.27mm,112.0,-114.0,top,270.0
175,176c175,176
< U7,C5224055,SOT-563,20.0,-116.0,top,90.0
< U8,C5224055,SOT-563,38.0,-116.0,top,90.0
---
> U7,C5224055,SOT-563,20.0,-116.0,top,270.0
> U8,C5224055,SOT-563,38.0,-116.0,top,270.0
```

| ref | LCSC | package | v1.3 | v1.4 | what it is |
|---|---|---|---|---|---|
| **U1** | C6938291 | TQFP-128 14x14 **0.4 mm** pitch + EP | 90.0 | **270.0** | the **CONSIGNED** XMOS XU316-1024 SoC |
| **U2** | C181312 | TSSOP-30 **0.5 mm** | 90.0 | **270.0** | PCM1865 4-ch ADC (ch 1-4) |
| **U3** | C181312 | TSSOP-30 **0.5 mm** | 90.0 | **270.0** | PCM1865 4-ch ADC (ch 5-8) |
| **U5** | C82317 | SOIC-8 5.3x5.3 | 90.0 | **270.0** | W25Q16 QSPI boot flash |
| **U7** | C5224055 | SOT-563 | 90.0 | **270.0** | AP61102 buck (3V3) |
| **U8** | C5224055 | SOT-563 | 90.0 | **270.0** | AP61102 buck (0V9 core) |
| **D_USB** | C90627 | USON-10 **0.5 mm** | 90.0 | **270.0** | USB D+/D- ESD array |

Machine-checked cell-by-cell (parsed both CSVs, compared every field of every
row keyed by Designator):

```
rows: 177 vs 177        added: []      removed: []
header identical: True  designator order identical: True
changed cells: 7        (all of them the Rotation column)
   ('D_USB', 'Rotation', '90.0', '270.0')
   ('U1',    'Rotation', '90.0', '270.0')
   ('U2',    'Rotation', '90.0', '270.0')
   ('U3',    'Rotation', '90.0', '270.0')
   ('U5',    'Rotation', '90.0', '270.0')
   ('U7',    'Rotation', '90.0', '270.0')
   ('U8',    'Rotation', '90.0', '270.0')
CONTROLS (must NOT move — 180 is sign-invariant, so the bug never touched them):
   Q1: v1.3 rot=180.0  v1.4 rot=180.0  whole row identical = True
   Q2: v1.3 rot=180.0  v1.4 rot=180.0  whole row identical = True
   U9: v1.3 rot=180.0  v1.4 rot=180.0  whole row identical = True
```

Changed CELLS: **7**. Changed ROWS: **7**. Added/removed rows: **0**. Every
other field of every other row is byte-identical.

## 2. The rotations RE-DERIVED INDEPENDENTLY (canon M1)

The numbers above are NOT taken from `jlc_twin`'s `jlc_offset` — that is the
function whose handedness bug caused the defect, and a gate must never derive
its expectation from the artifact it is grading nor from a table built by it.

`verification/rot_remeasure.py` (canonical tracked copy `03_src/rot_remeasure.py`,
committed in this release's source commit) re-derives all ten per-LCSC rotations
from scratch and shares no code with the exporter or the twin: OUR pads come from
pcbnew, JLC's pads from a plain TEXT parse of JLC's cached `.kicad_mod`, and the
rotation operator is PROVEN against pcbnew on this board's own footprints before
it is used. Pads are matched by pad NUMBER, centroid-aligned (so no translation
can smear the answer) and scored by RMS residual at each of 0/90/180/270.

Operator proof, over every pad of every footprint on this board:

```
   board angle    0.0 deg : max |pcbnew - operator| = 0.000000000 mm
   board angle   90.0 deg : max |pcbnew - operator| = 0.000000000 mm
   board angle  180.0 deg : max |pcbnew - operator| = 0.000000000 mm
   board angle  270.0 deg : max |pcbnew - operator| = 0.000000000 mm
   -- the pre-fix (NEGATED) form, for contrast:
   board angle    0.0 deg : max |pcbnew - NEGATED|  = 0.000000000 mm
   board angle   90.0 deg : max |pcbnew - NEGATED|  = 35.560000000 mm
   board angle  180.0 deg : max |pcbnew - NEGATED|  = 0.000000000 mm
   board angle  270.0 deg : max |pcbnew - NEGATED|  = 0.960000000 mm
```

That is the incident's signature reproduced on THIS board: exact at 0 and 180,
wrong at 90 and 270. It is why the defect could be 180 degrees off and silent.

Per-part fit (`verification/rotation_remeasure.txt`):

```
ref     lcsc          brd    n   best    rms_mm   next    rms_mm     sep     CPL  shipped ok
U1      C6938291        0  129    270    0.0025      0   11.9812   4811x   270.0    270.0 OK
U2      C181312         0   30    270    0.0025      0    5.0702   2028x   270.0    270.0 OK
U3      C181312         0   30    270    0.0025      0    5.0702   2028x   270.0    270.0 OK
U5      C82317          0    8    270    0.0577      0    5.4176     94x   270.0    270.0 OK
U7      C5224055        0    6    270    0.0725      0    1.1183     15x   270.0    270.0 OK
U8      C5224055        0    6    270    0.0725      0    1.1183     15x   270.0    270.0 OK
D_USB   C90627          0   10    270    0.0150      0    1.1438     76x   270.0    270.0 OK
Q1      C15127          0    3    180    0.2003    270    1.7777      9x   180.0    180.0 OK
Q2      C20917          0    3    180    0.0589    270    1.6951     29x   180.0    180.0 OK
U9      C79924          0    5    180    0.1592    270    2.0757     13x   180.0    180.0 OK

rows checked: 10   mismatches vs shipped fab/cpl.csv: 0
```

Every one of the seven corrected parts fits at 270 with a residual under
0.08 mm against a runner-up 15x to 4811x worse. There is no ambiguity to
adjudicate: the pad fit is decisive on all ten. (For U1 the fit uses the 129
pad numbers present exactly once on both sides — the 128 leads plus the EP; the
16 co-numbered in-pad thermal vias and 9 unnamed paste windows carry no
correspondence and are excluded.)

The script is archived beside this document as `verification/rot_remeasure.py`
(canonical tracked copy: `03_src/rot_remeasure.py`), so a future reader can
re-run the measurement rather than take the number on trust — the archive's
completeness test applies to the METHOD behind a fix claim, not only its output.

### 2a. Two published residuals for U1 — reconciled

`skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`'s evidence prose for
C6938291 states "rms 0.2047mm @270 vs 11.98mm next best (58x)"; this run
measures **rms 0.0025 mm @270 vs 11.9812 mm** (4811x). Same part, same day,
same 129-pad correspondence, same runner-up, an 80x difference in the residual.
Reconciliation, measured here rather than assumed:

```
U1, 129 pad numbers unique on BOTH sides, centroid-aligned:
  ang=  0   rms=11.9812   max=13.9392   mean=11.8939
  ang= 90   rms=16.9439   max=19.7114   mean=16.8205
  ang=180   rms=11.9812   max=13.9392   mean=11.8939
  ang=270   rms= 0.0025   max= 0.0025   mean= 0.0025
```

At 270 the residual is not merely small, it is UNIFORM — rms, mean and max all
equal 0.0025 mm — so there is no subset of pads carrying a larger error that a
different inclusion rule could surface as 0.2047. Re-running with the
duplicate-numbered pads zipped in (the `jlc_twin.fit_err` inclusion style)
returns the identical four numbers. The 0.2047 figure therefore comes from a
different ALIGNMENT (a translation taken from something other than the
centroid), not a different pad set; this run could not reproduce it. Both runs
agree on the answer (270) and on the runner-up (11.98), which is what the
release depends on. The table row is owned outside this board and is left
untouched; this note records the discrepancy rather than silently picking a
number.

### 2b. The residual oracle, stated

This measurement is independent of jlc_twin's CODE. It is not independent of
jlc_twin's DATA: both read the same cached JLC `.kicad_mod` files, produced by
easyeda2kicad's fetch/convert path. Re-parsing them as text defeats a PARSER
bug, not a CONVERSION bug, and the whole answer rests on JLC's pad NUMBERING
being faithful — pad numbering is the only thing that breaks the 180-degree
symmetry of a TQFP/TSSOP/SOIC land. Two things address that gap and neither is
hidden:

- 270 for these seven is exactly what v1.0, v1.1 and v1.2 shipped — three
  releases cut BEFORE the per-LCSC table existed, i.e. through a different code
  path. Agreement across a code-path change is real corroboration.
- The only oracle genuinely outside this toolchain is a human looking at JLC's
  own placement preview, and ORDER_README section 3a makes that check MANDATORY
  and BLOCKING for U1 before any PCBA order.

A calibration note in the same spirit: the separations are not uniform. The
seven corrected rows are decisive (15x-4811x, worst residual 0.0725 mm on the
SOT-563 bucks). The WEAKEST fits in the table are the ones that did NOT move —
Q1 (9x, rms 0.2003) and U9 (13x, rms 0.1592), 3- and 5-pad SOT-23 packages where
a pad fit carries the least information. They agree with v1.0-v1.3 and with
fleet cross-verification, so they are not a finding; but after U1, Q1 is the row
most worth a second look in the JLC preview.

### 2c. The five CPL rows this script does NOT grade — measured by the reviewer

`rot_remeasure.py` grades its ten hard-coded per-LCSC refs. Five OTHER CPL rows
carry a non-zero rotation and were therefore graded by nothing independent here:
**U10 (180)**, **C_c9 (180)**, **C_c10 / C_c11 / C_c13 (270)**. The second-pass
zero-context reviewer noticed the gap and closed it with its own instrument
(`verification/fresh_lens_v1.4_final.md`, "Informational"): it re-fitted all five
with the same pcbnew-proven operator and found **all five agree with the shipped
CPL**, the load-bearing one being

```
U10 (C6035451, SOT-89-5):  fits 180 at rms 0.1500 vs next-best 3.2882  (22x)
```

which matters because U10's 180 comes from the `^SOT-89` **name-DB** rule, not
from a per-LCSC measurement — C6035451 has no row in the per-LCSC table. The
other four are non-polarised 2-pad 0402 caps whose CPL rotation is simply their
board orientation with offset 0, and whose 0-vs-180 fit is degenerate by
construction (a symmetric 2-pad land cannot be oriented by a pad fit, which is
why polarity on such parts is checked by silk and by the order preview, never by
a fit). No gap remains. Grading EVERY CPL row rather than a hard-coded list is
the held A-ROT gate's job, and the script's own docstring says so.

## 3. The twin, re-run with the FIXED operator, as a SECOND confirmation

`jlc_twin.py` against this release's own `source/` + `fab/bom.csv`, with
`--assembly 03_src/rules/assembly.yaml` so the coded-but-unplaced and consigned
bodies are checked too:

```
exit 0 . 175 OK / 369 checked . ZERO ROT-DB-SUGGEST
```

and each of the ten per-LCSC rows reports its resolved value with `src=lcsc`:

```
C6938291  U1     OK  fit=0.00mm jlc_offset=270 db=270.0 src=lcsc
C181312   U2     OK  fit=0.00mm jlc_offset=270 db=270.0 src=lcsc
C181312   U3     OK  fit=0.00mm jlc_offset=270 db=270.0 src=lcsc
C82317    U5     OK  fit=0.06mm jlc_offset=270 db=270.0 src=lcsc
C5224055  U7     OK  fit=0.07mm jlc_offset=270 db=270.0 src=lcsc
C5224055  U8     OK  fit=0.07mm jlc_offset=270 db=270.0 src=lcsc
C90627    D_USB  OK  fit=0.01mm jlc_offset=270 db=270.0 src=lcsc
C15127    Q1     OK  fit=0.28mm jlc_offset=180 db=180.0 src=lcsc
C20917    Q2     OK  fit=0.08mm jlc_offset=180 db=180.0 src=lcsc
C79924    U9     OK  fit=0.20mm jlc_offset=180 db=180.0 src=lcsc
```

plus `MODEL-REG-OK  body on courtyard (0.00-0.07 mm)` for all ten. One code,
C9900035627 (the RJ45 consign-only placeholder), is FETCH-FAILED and carries a
standing evidence-backed adjudication in `03_src/rules/twin_adjudications.yaml`
— it is not on the CPL.

## 4. NO COPPER CHANGE — proven by RE-PLOT, not by copying

The fab package was RE-EXPORTED from the unchanged board on 2026-07-25 into
`06_build/fab_v14/`, and the freshly-plotted gerbers + drills were compared
member-for-member against v1.3's sealed zip. 15/15 members present in both; per
member the ONLY differing lines are the plot's own timestamp comments —
exactly 4 diff lines (2 removed + 2 added) on every one of the 15. With those
comment lines stripped, all 15 members hash IDENTICALLY (full table in
`verification/replot_identity.txt`):

```
raw byte-identical members ........ 0/15  (every member carries its own plot timestamp)
timestamp-stripped identical ...... 15/15
mismatched after stripping ........ 0
```

Because the plot is byte-stable apart from its own timestamp, v1.4 SHIPS v1.3's
gerber zip and drill files VERBATIM, so the sha256 identity claimed in the
MANIFEST is literal and checkable. **20 payload files are sha256-identical to
sealed v1.3** — the 3 fab gerber/drill artifacts, `fab/bom.csv`, all 3 PDFs, the
STEP, and all 12 `source/` files (full table in
`verification/payload_identity.txt`). `fab/cpl.csv` is the ONE file that
differs, by 7 cells.

## 5. Independent electrical re-gates on the same unchanged board

```
DRC   kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
      0 violations / 0 unconnected / 0 schematic-parity issues     -> verification/drc.json
DRC   the same, run on a STANDALONE COPY of this release's source/ alone
      (archive self-containment): 0 / 0 / 0, and ZERO lib_footprint_issues
      — this archive's fp-lib-table resolves its two vendored libraries
      through ${KIPRJMOD} (they ship inside source/), so it does NOT have
      the usb-hub-3s-v3 v1.3/v1.4 out-of-archive-pointer defect
                                                    -> verification/standalone_archive_drc.json
ERC   kicad-cli sch erc --severity-all: 0 ERRORS, 1211 warnings (baselined
      lib_symbol_issues class, expected on a tscircuit-native schematic per
      ADR-0002)                                                    -> verification/erc.json
PARITY converter kicad_sch vs sealed 04_kicad, node-for-node:
      116 nets both sides . 598 connected nodes both . 146 no-connects both
      REAL DISCREPANCIES: 0                                        -> verification/parity.md
COUNT board == circuit.json == kicad_sch == netlist == manifest, 199 components
                                                          -> verification/count_parity.txt
PORTS check_port_nets: 115/115 global labels survive to the netlist; 8/8 RJ45
      ports pin-for-pin per the brief, run against THIS release's own
      source/<board>.net                                -> verification/check_port_nets.txt
AUDIT audit_board: 21 polarity + 11 connector mate/keepout checks, USB pair
      23.62/23.51 mm spread 0.110 mm, U1-EP 16 GND 0.30/0.15 thermal vias
                                                                   -> verification/audit.txt
M-BOM fab/bom.csv LCSC == source per refdes (185 coded)   -> verification/bom_source_check.txt
```

## 6. What this gate would have caught

If the re-export had produced an EIGHTH changed row, or had moved Q1/Q2/U9, the
cell count above would not be 7 and the seal would have stopped. That is the
whole point of stating the expected delta as a number BEFORE looking: v1.3 was
sealed on evidence that described its own change accurately ("exactly these 10
rows") while the direction of the change was wrong, because nothing independent
of the broken tool ever re-derived the angle. Section 2 is what was missing.
