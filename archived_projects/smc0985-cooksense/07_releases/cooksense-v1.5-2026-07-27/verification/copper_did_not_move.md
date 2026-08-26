# THE COPPER DID NOT MOVE — v1.5 vs v1.4, measured four ways

On this fleet that claim needs numbers, not a sentence. usb-hub-3s-v3 v1.6-v1.8
shipped 44 287.91 mm² of MISSING COPPER with every gate green, so "we only
changed the BOM" is exactly the sentence that has been wrong before.

v1.5 changes **two LCSC codes and the text of the BOM**. Nothing else. Here is
that, measured.

---

## 1. THE BOARD FILE IS THE SAME FILE

    md5  420445b5141dd1111eccab038c68511b   04_kicad/cooksense.kicad_pcb
    md5  420445b5141dd1111eccab038c68511b   v1.5/source/cooksense.kicad_pcb
    md5  420445b5141dd1111eccab038c68511b   v1.4/source/cooksense.kicad_pcb
    md5  420445b5141dd1111eccab038c68511b   v1.3/source/cooksense.kicad_pcb

An LCSC code never enters the `.kicad_pcb` — it lives in `circuit.json` and is
attached to the BOM row at export time — so a code swap CANNOT reach the copper
unless it changes a FOOTPRINT. It does not: the BOM delta below shows **0
Footprint changes**, and both replacements are the same
`Resistor_SMD:R_0402_1005Metric` land at the same `componentSpecificationEn`
0402.

## 2. THE GERBERS, RE-PLOTTED AND COMPARED BY A DIFFERENT METHOD (canon M1)

Re-plotted from that board by `export_jlc_package.py`, then compared to v1.4's
sealed zip with an **aperture-resolved, order-independent** comparator: every
D-code is resolved to its `%ADD` aperture DEFINITION, coordinates are resolved
out of gerber's MODAL state, and the multiset of `(aperture, op, x, y)` atoms is
compared. This is necessary rather than fussy — KiCad does not guarantee
emission ORDER between runs, so a byte or line diff reports differences that are
not differences.

| member | atoms | verdict |
|---|---|---|
| `cooksense-B_Cu.gbl` | 3991 | DIFFERS: 3 region atoms each way |
| `cooksense-B_Mask.gbs` | 210 | IDENTICAL GEOMETRY |
| `cooksense-B_Paste.gbp` | 0 | IDENTICAL GEOMETRY |
| `cooksense-B_Silkscreen.gbo` | 105 | IDENTICAL GEOMETRY |
| `cooksense-Edge_Cuts.gm1` | 112 | IDENTICAL GEOMETRY |
| `cooksense-F_Cu.gtl` | 9264 | DIFFERS: 2 region atoms each way |
| `cooksense-F_Mask.gts` | 900 | IDENTICAL GEOMETRY |
| `cooksense-F_Paste.gtp` | 674 | IDENTICAL GEOMETRY |
| `cooksense-F_Silkscreen.gto` | 30071 | IDENTICAL GEOMETRY |
| `cooksense-In1_Cu.g1` | 2299 | IDENTICAL GEOMETRY |
| `cooksense-In2_Cu.g2` | 2299 | IDENTICAL GEOMETRY |
| `cooksense-NPTH.drl` | 6 | IDENTICAL GEOMETRY |
| `cooksense-PTH.drl` | 1146 | IDENTICAL GEOMETRY |

**11 of 13 identical. The two that differ are not reported as identical, and
they are not hand-waved either** — section 3 measures them.

## 3. THE FIVE DIFFERING G36 REGIONS CARRY ZERO AREA

The differences are entirely inside poured (`G36`..`G37`) regions, and they are
DUPLICATE / sub-nanometre-collinear vertices that KiCad's polygon writer emits
nondeterministically. Raw counts:

    F_Cu    NEW 106 regions / 14 002 vertices    OLD 106 regions / 14 000
    B_Cu    NEW  13 regions / 15 585 vertices    OLD  13 regions / 15 584
    In1_Cu  NEW   1 region  / 24 920 vertices    OLD   1 region  / 24 920
    In2_Cu  NEW   1 region  / 24 920 vertices    OLD   1 region  / 24 920

Three extra vertices out of 29 587 on the two outer layers, e.g. the triple
`(50090700, -87596682) (50090701, -87596683) (50090701, -87596682)` — points
1 nm apart. **Region COUNTS are equal on every layer**, which is the number
`fab_payload_census` grades.

The property that decides it is AREA, computed by shoelace over every G36
polygon, independently of vertex count:

| layer | regions | v1.5 area | v1.4 area | delta |
|---|---|---|---|---|
| `B_Cu` | 13 | 7379.912432 mm² | 7379.912432 mm² | **0.000000** |
| `F_Cu` | 106 | 2838.968914 mm² | 2838.968914 mm² | **0.000000** |
| `In1_Cu` | 1 | 8475.761683 mm² | 8475.761683 mm² | **0.000000** |
| `In2_Cu` | 1 | 8435.827928 mm² | 8435.827928 mm² | **0.000000** |

Equal to six decimal places — i.e. to the nanometre². The pour did not move.

## 4. THE MACHINE INSTRUCTIONS ARE BYTE-IDENTICAL

    md5  d606af7ad01986b754955a5abead783a   v1.5/fab/cpl.csv
    md5  d606af7ad01986b754955a5abead783a   v1.4/fab/cpl.csv

    md5  a72b13657951ecb78204e16399c6d720   v1.5/fab/rotation_human_gate.txt
    md5  a72b13657951ecb78204e16399c6d720   v1.4/fab/rotation_human_gate.txt

So **every A-ROT rotation and every A-POS coordinate carries forward untouched**,
including the 12-code / 16-ref POLARITY-FIT-BLIND population that ORDER_README §6
is the only defence for. The `3d/`, `pdf/` and the five carried `source/` files
are byte-identical too; `source/cooksense.tsx` is in the CHANGED column BY DESIGN
(that is where the swap was made) and `source/cooksense.net` is a fresh export of
the same unchanged schematic.

## 5. THE BOM DELTA, PARSED AS CSV RATHER THAN DIFFED AS TEXT

    rows: 56 -> 56
    added rows: none
    removed rows: none
    cells changed by column: {'Comment': 28, 'Footprint': 0, 'MPN': 54, 'LCSC': 2}
    total cells changed: 84

    LCSC changes (2):
       R_ILM                                       C25862 -> C138040
       R_BID0,R_BID1,R_DOORPD,...,R_TEMPOK (17)    C25744 -> C60490

    Footprint changes: 0

The 54 MPN fills and 28 Comment rewrites are the F-LEGIBLE repair; the 2 LCSC
cells are the whole electrical content of this release. Row ORDER changed
because the exporter sorts by Comment and the Comments changed — the designator
SET is identical (0 added, 0 removed), which is the property that matters.

*Tools: `md5sum`; an aperture-resolving gerber comparator; a shoelace area
integrator over G36 regions; `csv.DictReader`. None of them is the plotter or
the exporter that produced the artifacts (canon M1).*
