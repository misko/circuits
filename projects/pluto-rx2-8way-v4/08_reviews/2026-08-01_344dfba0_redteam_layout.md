subject: pluto-rx2-8way-v4 git 344dfba05f7160b99b56dc9722cf8be72e846c7e
date: 2026-08-01
reviewer: redteam-agent (GPT-5, layout/thermal/power-integrity/RF/manufacturability lens)
context-given: full-tree
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER

# Final adversarial layout / RF / PI / thermal / manufacturability review

## Frozen subject

- Source commit, measured with `git rev-parse HEAD` and `git show`: `344dfba05f7160b99b56dc9722cf8be72e846c7e`.
- Board: `04_kicad/pluto_rx2_8way_v4.kicad_pcb`, SHA-256 `4a5e69d474f5354346edbb64683edb3c69946b9ad437c1ddf49e4b126fc7f14a` before and after all read-only checks.
- Fabrication archive: `06_build/fab/pluto_rx2_8way_v4_gerbers.zip`, SHA-256 `4f1d2fea756f86220cb8c8dc2712198f4df0d306d6cd9a174587293f8b0e494d`.
- RF solver evidence: `06_build/verify/cpwg_field.json`, SHA-256 `44c7ddc38f4e90c6b182b32da13a13bafe151b8b98f2556999f96d6ba8e5fb30`.

I reviewed the saved KiCad board and current ignored build evidence directly. Prior review conclusions were not used as acceptance evidence.

## Finding summary

| ID | Severity | Finding | Evidence | Disposition |
|---|---|---|---|---|
| LRF-01 | P0 | The frozen board does not meet the RF ground-stitch bound that its source and field-solver tuple claim it meets. | Independent saved-board reconstruction measures `ANT7 W = 1.8297 mm` and `ANT4 W = 1.2000 mm` against `<=1.1910 mm`; 2/22 arm-sides are over. The solver instead binds a periodic `via_pitch_mm: 1.1769` and names old `962c3cda` geometry. | Open. Add the two legal vias below and rebuild/re-run the fence and field/length gates, or replace the bound with a newly justified and independently graded acceptance contract. Re-review the resulting exact board/fab hashes. |
| LMF-01 | P1 | POFV is authored correctly but vendor execution is not yet qualified. | Board setup has `(filling yes)` and `(capping yes)` and the ten named U_SW via-in-pad sites are present; Gerbers do not select the service. | Order gate: written whole-board fill/cap and flat-land DFM acceptance, production-file preview, and first-panel X-ray/cross-section evidence. Not a current geometry defect. |
| LMF-02 | P1 | Controlled impedance, plug-in SMA assembly, and the user-fitted module still require vendor/physical acceptance. | Source explicitly forbids silent impedance edits; ten C504007 jacks are plated through-hole `Plugin` placements; U_MCU has a populated carrier-facing surface and is excluded from BOM/CPL/paste. | Order/first-article gates: coupon TDR, VNA characterization, JLC plug-in acceptance, module sample metrology/fixture/fillet inspection, representative-firmware current/case-temperature qualification. |
| LPI-01 | P2 | The documented LS-pin geometric checker is absent from `audit_board.py`, although the current geometry passes by direct measurement. | PE42482 dossier says audit I8 checks U_SW.1 to a GND via within 0.5 mm; the current audit implements no such check. Direct pcbnew measurement is 0.4179 mm. | Process debt: promote this assertion into the project audit/shared gate before a future geometry change. No current-board defect. |
| LDOC-01 | P2 | Several narrative counts/dimensions are stale. | The saved outline is 50.0 x 73.0 mm although a floorplan comment says 46.0 x 73.0; current board has 3,440 vias (3,423 GND), while historical comments cite 3,446. | Correct prose in the next source revision; no copper consequence. |

## P0 detail — field tuple is not bound to the current fence

The source requires ground stitching flanking the RF lines at `<= 1.1910 mm`, derived as `lambda_pp/20` for the dielectric parallel-plate mode. I ran the existing independent fence instrument against the exact frozen board:

```text
/usr/bin/python3 projects/pluto-rx2-8way-v2/03_src/fence_pitch.py \
  projects/pluto-rx2-8way-v4/04_kicad/pluto_rx2_8way_v4.kicad_pcb 2.5 1.1910

GND fence elements: 3463 (3423 GND vias + 40 GND PTH posts)
ANT4 W: 1.2000 mm  OVER
ANT7 W: 1.8297 mm  OVER, s=5.64..7.47 mm
WORST: 1.8297 mm = lambda_pp/13.02 = 1.54x the declared bound
VERDICT: FAIL (exit 1)
```

This is an evidence/contract blocker, not evidence that the trace impedance is actually far from 50 ohms. I re-ran the same solver read-only at the measured 1.8297 mm periodic pitch: the finest 0.025 mm result moved only to 52.115834 ohms, 3.173575 effective permittivity, 5.942287 ps/mm, and 12.835341 degrees/mm. The saved nominal solve itself reports 52.0877 ohms, 3.173354 effective permittivity, 5.942081 ps/mm, and a three-mesh interval of 49.19..54.99 ohms. That sensitivity supports impedance robustness, but it cannot make the frozen evidence truthful: the JSON still states `via_pitch_mm: 1.1769`, `via_center_offset_mm: 0.510`, and `geometry_source: frozen PCB direct measurement, layout review 962c3cda`, while the reviewed board hash is `4a5e...` and violates the declared stitch inequality.

### Minimum read-only repair search

I swept each failing aperture at 0.05 mm arclength/lateral steps using `pcb_toolkit.Toolkit.via_site_ok` on the exact frozen board. Both proposed sites were then explicitly rechecked with a 0.25/0.15 mm through via, 0.155 mm hole-to-copper, 0.315 mm hole-to-hole, and all four copper layers:

| Flank | Proposed GND via centre (mm) | `via_site_ok` | Predicted worst sub-gap |
|---|---:|---|---:|
| ANT4 W | `(41.060, 57.800)` | PASS | 0.8000 mm |
| ANT7 W | `(46.312, 42.281)` | PASS | 1.1500 mm |

Neither site lies within the stitcher's 0.75 mm spacing radius of a current 0.8 mm grid via, so placing these as deterministic pre-grid seed vias is predicted to suppress zero grid sites. The ANT7 proposal is 0.6822 mm from the existing custom GND via at `(46.739, 41.749)`, but clears the 0.315 mm hole-to-hole floor and the 0.5 mm-box dedupe rule (`dy=0.532 mm`). This is a repair proposal, not a passed artifact: the board must be regenerated and all gates re-run before either predicted number becomes evidence.

## Independent measurements that passed

### Layout and connectivity

- Fresh KiCad 10.0.4 full-severity DRC with zone refill and schematic parity: `0 violations / 0 unconnected / 0 parity`.
- Project geometry audit: module underside keepout clear; SW_V4 crosses ANT4 on In2.Cu; In1.Cu has zero tracks and a continuous GND zone.
- P-LAND: 47/130 copper pads graded, 0 failing; all QFN RF launches accept the 0.36 mm RF floor under the authored 0.14 mm local clearance.
- Eight matched arms are F.Cu-only, 0.36 mm wide, and contain zero vias. ANT3 and ANT7 connector endpoints terminate at the connector pad centres `(29.200,59.150)` and `(52.800,38.350)` respectively.
- R-LEN: 8/8 paths measured, spread 0.1208 mm against 1.0 mm, equal to 0.718 ps / 1.55 degrees at 6 GHz using the declared solver tuple. Octilinear pad floor spread is 0.0007 mm.

### RF cross-section and reference

- Saved-board fill sampling at 0.1 mm steps measures a 0.2005..0.2010 mm edge-to-edge coplanar gap, pooled median 0.2010 mm (`g/h=0.955`), and a mean 78.6% GCPW classification across the eleven RF polylines. All eight matched arms are 68.8..87.2% GCPW; the non-GCPW portions are concentrated at the intentional SMA launch antipads.
- In1.Cu reference is continuous beneath every arm except those launch-antipad intervals. There are no In1.Cu signal tracks.
- The masked 3-D quasi-static solver converges with relative residual below `2e-9`; its complete saved numerical interval fits 50 ohms +/-10%. This numerical pass remains useful but does not close LRF-01's current-geometry identity failure.

### Power integrity and thermal

- The carrier load is light: PE42482A-X supply current is 200 uA maximum. Its 7.5625 mm2 exposed pad has seven directly located GND vias; the current R-THERM gate passes.
- U_SW VDD-to-C_SW1 bypass span is 2.83 mm inside the declared 3.0 mm budget; all 8/8 measurable keep-short constraints pass.
- The RP2040-Zero LDO bound is explicitly limited to 125 mA total at 50 C ambient with WS2812 dark: derived worst-case dissipation 252 mW versus a 400 mW conservative budget. Because the regulator is on the purchased module and its actual thermal environment is not the assumed JEDEC board, this remains a physical qualification gate, not a layout proof.

### Fabrication and assembly geometry

- Board thickness is 1.2 mm. Every via is 0.25/0.15 mm, so nominal aspect ratio is 8.0:1; even the documented +0.10 mm thickness tolerance gives 8.67:1, below the tier's 10:1 limit. Tier preflight reports 0 failures.
- Native KiCad setup contains board-wide fill and cap flags. Direct pad-hit measurement confirms all ten documented assembly-critical U_SW sites: seven in pad 25 and one each in pads 18, 8, and 11.
- The fab archive contains 13 required files: 11 plotted copper/mask/paste/silkscreen/edge layers plus PTH and NPTH drills. PTH drill tools are 0.150 mm vias and 1.400 mm component holes.
- Assembly evidence reports 32 footprints, 27 CPL placements, and five declared unassembled refs (`H1`-`H4`, `U_MCU`); BOM source/legibility and body coverage are green. Catalog stock evidence is current PASS, 11/11 lines, zero failures, so the order verdict is **not** `BLOCKED-SOURCING`.

## Known-class closure matrix

| Class | Result | Reason |
|---|---|---|
| POFV contract | Source-side CLOSED; vendor gate OPEN | Native fill/cap flags and ten fixed sites are present; vendor process selection/X-ray remain order gates. |
| Via aspect ratio | CLOSED | 1.2/0.15 = 8.0:1; preflight passes. |
| Masked CPWG / phase tuple | NOT CLOSED | Solver numerics are plausible, but its frozen fence pitch/geometry identity does not match the current board. |
| ANT3 / ANT7 endpoint centring | CLOSED | Saved F.Cu endpoints land at both connector centres. |
| Via-fence modeling | NOT CLOSED | Direct current-board gate finds 2/22 flanks over the declared bound. |
| Assembly/order qualifications | Correctly explicit; OPEN | POFV, impedance coupon/TDR, plug-in SMA, module fit/thermal, VNA and first-article inspection are named gates rather than hidden assumptions. |

## Verdict

`design_verdict: DEFECTIVE` because LRF-01 is a confirmed P0: the frozen board and the evidence tuple make contradictory statements about a binding RF structure. The issue is narrowly repairable with two currently legal GND via sites, but predictions do not pass a frozen artifact.

`order_verdict: DO-NOT-ORDER`. Current sourcing evidence is clear, so `BLOCKED-SOURCING` would be incorrect. Ordering is prohibited by the open P0 and, after that is fixed, remains held until the vendor-process and first-article qualifications above are completed.
