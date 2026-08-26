# v1.3 CPL rotation fix — per-LCSC exact-fit (evidence)

**What changed:** `fab/cpl.csv` only. Copper, schematic, routing, drills,
gerbers, and BOM are byte-identical to v1.2 (a docs+CPL supersede). This
document is the measured evidence for the 10 corrected rotation rows.

## The blocker (from the external review of sealed v1.2)

v1.2's `fab/cpl.csv` wrote the community footprint-NAME rotation DB
(`jlc_rotations_db.csv`) family values, which DISAGREE with the digital twin's
exact pad-fit (fit ≈ 0.00–0.28 mm against JLC's OWN fetched footprint) on 10
parts — including the consigned **U1 (XU316, TQFP-128) at 270° vs the exact-fit
90° = 180° off**. Shipping that CPL to PCBA would place 10 parts (2 of them
polarized FETs, one the 128-lead SoC) at the wrong rotation.

## Root cause: JLC zero-orientation is PER-LCSC, not per-footprint-name

The name DB keys the rotation offset by footprint NAME. But JLC's CPL
zero-orientation is a property of how JLC drew **that specific LCSC part's**
footprint — two different parts that share a KiCad footprint name can need
different offsets. Measured on this fleet (2026-07-24):

| Footprint (shared name) | Part A | fit→offset | Part B | fit→offset |
|---|---|---|---|---|
| `SOT-23-5` | C79924 (crow-rv2 U9) | **180°** | C7719 (cooksense U_WD) | **90°** |
| `SOT-23`   | C15127/C20917/C8545/C78284 (fleet) | **180°** (unanimous) | — | — |

`SOT-23-5` is the proof: a single name key cannot hold both 180° and 90°, and a
broad `^SOT-23,180` name rule would mis-set every OTHER part sharing that name.

## The fix (root-cause, fleet-wide)

A new global per-LCSC table `skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv`
(keyed `LCSC,rotation,evidence`) is consulted **before** the name DB and WINS
(`jlc_rotation_resolve.resolve_rotation()`, shared by the exporter and the
twin). A part with no per-LCSC row falls through to the name DB unchanged, so
every un-listed part keeps its existing behaviour. The table is populated ONLY
with twin-measured exact-fits (evidence cited per row). This resolves U9
(C79924→180) WITHOUT touching cooksense's C7719 (different LCSC → different row,
still name-DB).

## Before / after — all 10 corrected CPL rows (board orientation = 0° for each)

| Ref | LCSC | Footprint | v1.2 CPL | v1.3 CPL | twin fit | source |
|---|---|---|---|---|---|---|
| U1 | C6938291 | TQFP-128_14x14mm_P0.4mm_EP_XU316 | 270° | **90°** | 0.00 mm | per-LCSC |
| U2 | C181312 | TSSOP-30_4.4x7.8mm_P0.5mm | 270° | **90°** | 0.00 mm | per-LCSC |
| U3 | C181312 | TSSOP-30_4.4x7.8mm_P0.5mm | 270° | **90°** | 0.00 mm | per-LCSC |
| U5 | C82317 | SOIC-8_5.3x5.3mm_P1.27mm | 270° | **90°** | 0.06 mm | per-LCSC |
| U7 | C5224055 | SOT-563 | 0° | **90°** | 0.07 mm | per-LCSC |
| U8 | C5224055 | SOT-563 | 0° | **90°** | 0.07 mm | per-LCSC |
| D_USB | C90627 | USON-10_2.5x1.0mm_P0.5mm | 270° | **90°** | 0.01 mm | per-LCSC |
| Q1 | C15127 | SOT-23 | 270° | **180°** | 0.28 mm | per-LCSC |
| Q2 | C20917 | SOT-23 | 270° | **180°** | 0.08 mm | per-LCSC |
| U9 | C79924 | SOT-23-5 | 270° | **180°** | 0.20 mm | per-LCSC |

`diff` of v1.2 → v1.3 `fab/cpl.csv` = EXACTLY these 10 rows, rotation column
only; all 177 rows' designator/value/package/X/Y/layer are byte-identical.

## Twin proof

Re-ran `jlc_twin.py` against this release's own `source/` + `fab/bom.csv` with
the per-LCSC table active: **twin exit 0, 175 OK / 369 checked, ZERO
ROT-DB-SUGGEST** (v1.2 had 10). Each of the 10 rows above now reports
`OK  fit=… jlc_offset=… db=… src=lcsc` (see `twin_report.txt` /
`twin_report.csv`). `missing_models.txt` regenerated from the final CPL:
177 CPL rows / 177 modeled / 0 missing bodies.

## Human gate (does NOT block the seal; BLOCKS assembly)

U1's 90°-vs-270° must be confirmed against JLC's placement preview (package
pin-1 dot vs the board pin-1 marker) before ANY PCBA order — a symmetric-package
180° error is invisible to a pad-fit. The exact-fit (90°) is the machine-best
answer and is what the CPL now uses; the preview is the physical confirmation.
Recorded as a MANDATORY pre-PCBA step in ORDER_README §3a.

## Fleet exposure (for the separate fleet-audit task)

The per-LCSC table also carries the fleet-cross-verified SOT-23 codes C8545 and
C78284 (both 180°, NOT on this board — added with cited evidence). The fleet
audit must extend the table with MEASURED per-LCSC values for the remaining
boards' unresolved suggestions — notably cooksense's C7719 (SOT-23-5 → 90°) and
its other ROT-DB-SUGGEST rows, and crow-recorder-central v1.0's identical
shared-footprint set. No sealed release changes until it next reseals.
