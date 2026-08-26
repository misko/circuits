# Twin render faithfulness — twin_bottom.png (`--side bottom`)

board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
a-render_verdict: PASS
- calibration: **7.4174 px/mm** x, **7.4251 px/mm** y, anisotropy **0.9990** (tol 0.02) — orthographic, projection valid; X-MIRRORED (bottom side)
- board edge: 19.950..150.050 x, 19.950..110.050 y mm
- courtyards drawn (B.CrtYd): **9**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 9 measured / 9 refs with an expected body** (0 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (1 LCSC transform entry)
- overlay: `twin_bottom_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (9)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `U_ESD4` | C3708426 | 180deg @0.22mm | 0.188 | 0.023 | +0.23,+0.52,+0.02,-0.80 | 102 | 0.054 |
| `U_ESD3` | C3708426 | 180deg @0.22mm | 0.163 | 0.000 | +0.18,+0.52,-0.02,-0.80 | 109 | 0.054 |
| `U_ESD1` | C3708426 | 180deg @0.22mm | 0.155 | 0.000 | +0.23,+0.52,-0.10,-0.80 | 105 | 0.054 |
| `U_ESD2` | C3708426 | 180deg @0.22mm | 0.146 | 0.000 | +0.14,+0.52,-0.06,-0.80 | 108 | 0.054 |
| `U_ESD_UP` | C3708426 | 180deg @0.22mm | 0.123 | 0.000 | +0.20,+0.47,-0.14,-0.71 | 98 | 0.054 |
| `U_DATA4` | C11355 | 270deg @0.01mm | 0.118 | 0.020 | +1.20,-0.02,-1.10,-0.19 | 306 | 0.000 |
| `U_DATA2` | C11355 | 270deg @0.01mm | 0.111 | 0.020 | +1.12,-0.02,-1.05,-0.19 | 324 | 0.000 |
| `U_DATA1` | C11355 | 270deg @0.01mm | 0.109 | 0.020 | +1.18,-0.02,-1.13,-0.19 | 306 | 0.000 |
| `U_DATA3` | C11355 | 270deg @0.01mm | 0.108 | 0.020 | +1.04,-0.02,-1.00,-0.19 | 326 | 0.000 |

## 7 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `C_TRUNK_USB` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `U_HUB` | **PAD-MULTIPLICITY** | pad number(s) 65 appear a different number of times on the two footprints (ours {'65': 18} vs JLC {'65': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROI |
| `U_PWR1` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U_PWR2` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U_PWR3` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U_PWR4` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U_PWR_CTRL` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |

