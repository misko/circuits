# FIX-CLAIM EVIDENCE — the copper pour is back

The 07_releases contract requires that a release claiming a FIX carry, in
`verification/`, the MEASUREMENT that proves that specific claim — numbers,
method, and what was measured — **by a method able to FALSIFY it independently
of whoever produced the fix**. This is that file.

The claim: *v1.6, v1.7 and v1.8 shipped gerbers with no copper pour; v1.9's
gerbers have it, and nothing else about the board changed.*

## 1. The falsifying instrument, and proof that it can fail

`skills/jlcpcb-fab/scripts/fab_payload_census.py` (canon **F-POUR** / **F-IDENT**)
does not look at the board the fixer edited. It opens
`fab/<board>_gerbers.zip` — the artifact that becomes copper — parses the Gerber
**G36/G37 region** primitives out of each copper layer, and grades that count
against the zone declarations in `source/<board>.kicad_pcb`. It shares no method
with the build (canon M1) and it is downstream of the export, which is where the
defect lived.

**It is proven able to fail, on real sealed bytes, not on a synthetic fixture:**
run against `07_releases/v1.8-2026-07-26/` it returns `F-PAYLOAD FAIL: 5
finding(s), 0 ok`. Both runs are archived verbatim, side by side, in
`fab_payload_census.txt`. A gate that has never blocked anything proves nothing;
this one blocks the previous release of this same board.

## 2. The measurement

| | v1.8-2026-07-26 | v1.9-2026-07-27 |
|---|---|---|
| F-PAYLOAD verdict | **FAIL: 5 findings, 0 ok** | **OK: 5 checks passed** |
| G36 regions, `B_Cu.gbl` | **0** | **17** |
| G36 regions, `F_Cu.gtl` | **0** | **87** |
| G36 regions, `In1_Cu.g1` | **0** | **1** |
| G36 regions, `In2_Cu.g2` | **0** | **1** |
| F-IDENT | `In1_Cu` and `In2_Cu` **BYTE-IDENTICAL at 18921 B with 0 G36** | all 4 copper gerbers **distinct** |
| `In1_Cu.g1` size | 18 921 B | **174 761 B** |
| `In2_Cu.g2` size | 18 921 B | **269 172 B** |
| `F_Cu.gtl` size | — | **625 562 B** |
| `B_Cu.gbl` size | — | **287 720 B** |
| gerber zip | **88 692 B** | **394 534 B** |

Independently, on the saved board itself (`pcbnew`, filled-zone polygons, not the
gerbers):

```
pour zones: 36
  F.Cu      10402.72 mm2
  In1.Cu    11406.27 mm2
  In2.Cu    11276.88 mm2
  B.Cu      11196.24 mm2
  TOTAL     44282.10 mm2   (106 filled outlines)
```

against **0.00 mm2 / 0 filled_polygon** on v1.8's `source/usb_hub_3s_v2.kicad_pcb`
(`grep -c filled_polygon` = 0). The fleet audit's figure for the missing copper
was 44287.91 mm2; the 5.81 mm2 difference from the number above is the
regeneration variance already declared under REPRODUCIBILITY (island-rescue via
bonding perturbs pour boundaries by a few mm2 between runs).

## 3. The third instrument: the read-back, at build time

`route_and_stitch_generic.py verify-fill` reopens the saved `.kicad_pcb` **as
TEXT** — not through pcbnew, because pcbnew is the tool whose save behaviour is
under test — and counts pour zones and `filled_polygon` blocks. On the board this
release ships:

```
read-back: 36 pour zone(s) in the SAVED file, 106 filled_polygon block(s)
```

It excludes keepout/rule-area zones, which carry no fill by design and would
otherwise make a pour-free board look healthy. It is wired into both
`03_src/rebuild_fast.sh` and `03_src/rebuild_all.sh`.

Three instruments, three artifacts (the zip, the board object, the board text),
one fact.

## 4. What did NOT change — the other half of the claim

A fix claim is only as good as its blast radius. Measured:

* **Netlist parity vs v1.8: 0 differences.** 122 components, 73 nets, 372 nodes,
  identical component set, identical net-name set, 0 nets differing node-for-node
  (`parity.md`).
* **`fab/cpl.csv` is BYTE-IDENTICAL to v1.8's** — `diff` clean, 119 rows.
  Placement, rotation, layer and datum did not move.
* **`fab/bom.csv` is BYTE-IDENTICAL to v1.8's** — `diff` clean, 46 lines.
* **DRC 0 / 0 / 0** at `--severity-all --refill-zones --schematic-parity`, and
  **0 / 0 / 0 again** on the archive re-measured STANDALONE (`source/` extracted
  to a bare directory, `standalone_archive_drc.json`), with ERC 0 errors and
  **0 `footprint_link_issues`** there.

The drill files differ from v1.8's by one added via and one via displaced
0.010 mm — the island-rescue non-determinism declared in ORDER_README under
REPRODUCIBILITY, on a board rebuilt from source after the fix. It is additive
same-net bonding, and the shipped artifact is the one hashed in `MANIFEST.txt`.
