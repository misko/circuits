# Twin render faithfulness — twin_top.png (`--side top`)

board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
a-render_verdict: PASS
- calibration: **10.7103 px/mm** x, **10.6912 px/mm** y, anisotropy **1.0018** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..110.050 x, 19.950..85.050 y mm
- courtyards drawn (F.CrtYd): **36**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 14 measured / 29 refs with an expected body** (15 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (4 LCSC transform entries)
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (14)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J5` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.779 | 0.048 | -0.05,-1.48,-0.10,-0.07 | 8788 | 5.731 |
| `J6` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.774 | 0.048 | -0.05,-1.52,-0.10,-0.02 | 8805 | 5.731 |
| `J9` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.765 | 0.041 | +0.02,-0.04,+1.51,-0.06 | 8826 | 5.731 |
| `J3` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.761 | 0.041 | +0.01,-0.04,+1.51,-0.06 | 8760 | 5.731 |
| `J7` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.755 | 0.000 | +0.00,+0.05,-0.04,+1.46 | 8760 | 5.731 |
| `J8` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.750 | 0.004 | +0.00,-0.00,-0.04,+1.50 | 8758 | 5.731 |
| `J2` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.747 | 0.048 | -0.05,-0.04,+1.54,-0.06 | 8776 | 5.731 |
| `J10` | C429844 | ANCHOR 1->1 @0deg (failed fit 1.80mm) | 0.733 | 0.041 | -0.02,-0.04,+1.48,-0.06 | 8755 | 5.731 |
| `J1` | C5184243 | 0deg @0.00mm | 0.208 | 0.004 | -0.34,-0.00,+0.34,+0.42 | 14050 | 2.133 |
| `U1` | C5121458 | 0deg @0.01mm | 0.059 | 0.000 | +0.00,-0.04,-0.10,-0.04 | 2803 | 0.000 |
| `D1` | C83270 | 0deg @0.21mm | 0.045 | 0.000 | -0.70,+0.10,+0.63,-0.04 | 3702 | 0.000 |
| `U3` | C2866134 | 180deg @0.04mm | 0.038 | 0.022 | +0.09,-0.29,-0.10,+0.36 | 848 | 0.007 |
| `J11` | C2932107 | NONE (best 0.51mm) -> JLC's own transform | 0.025 | 0.010 | +0.04,-0.47,-0.05,+0.52 | 5757 | 0.000 |
| `U2` | C5452432 | 270deg @0.01mm | 0.013 | 0.000 | +0.03,-0.32,-0.03,+0.29 | 5880 | 0.001 |

## Not measurable by construction (15) — named, never silently passed

- `C1` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (8.6 px, and erosion costs 4 px)
- `C2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (8.6 px, and erosion costs 4 px)
- `C3` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (8.6 px, and erosion costs 4 px)
- `C4` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `C5` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `C6` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `F1` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (8.7 px, and erosion costs 4 px)
- `J4` — a part with NO expected body — so nothing this gate can mask out — sits within 0.5 mm: FID1 (0.00 mm), H1 (0.00 mm); the two would merge into one component
- `R1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `R2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `R3` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `R4` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `R5` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `R6` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (5.4 px, and erosion costs 4 px)
- `U4` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (17.1 px, and erosion costs 4 px)

## 11 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `D1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D1` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `J10` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J10` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J11` | **MOUNT-FALLBACK** | best 0.51mm at 0deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is  |
| `J2` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J2` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J3` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J3` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J4` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J4` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J5` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J5` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J6` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J6` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J7` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J7` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J8` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J8` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |
| `J9` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 4}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `J9` | **MOUNT-FALLBACK** | best 1.80mm at 0deg, over 0.5mm — body mounted by the adjudicated unique-pad datum our 1 -> JLC 1 at 0deg, NOT by either mismatched pad-group centroid |

## Per-ref crops

- `D1` -> `overlay_D1.png`
- `J10` -> `overlay_J10.png`
- `J11` -> `overlay_J11.png`
- `J2` -> `overlay_J2.png`
- `J3` -> `overlay_J3.png`
- `J4` -> `overlay_J4.png`
- `J5` -> `overlay_J5.png`
- `J6` -> `overlay_J6.png`
- `J7` -> `overlay_J7.png`
- `J8` -> `overlay_J8.png`
- `J9` -> `overlay_J9.png`

