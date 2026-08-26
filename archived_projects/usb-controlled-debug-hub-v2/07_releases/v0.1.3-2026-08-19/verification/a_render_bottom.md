# Twin render faithfulness — twin_bottom.png (`--side bottom`)

board_sha256: b1c042c695af896b18627c596406157bc5522561c31ac60cc353b11ff065d197
a-render_verdict: PASS
- calibration: **7.4174 px/mm** x, **7.4226 px/mm** y, anisotropy **0.9993** (tol 0.02) — orthographic, projection valid; X-MIRRORED (bottom side)
- board edge: 19.950..150.050 x, 19.950..120.050 y mm
- courtyards drawn (B.CrtYd): **9**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 9 measured / 9 refs with an expected body** (0 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (3 LCSC transform entries)
- overlay: `twin_bottom_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (9)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `U_ESD4` | C3708426 | 180deg @0.22mm | 0.142 | 0.023 | +0.23,+0.66,+0.02,-0.79 | 119 | 0.054 |
| `U_DATA4` | C11355 | 270deg @0.01mm | 0.111 | 0.012 | +1.20,-0.01,-1.10,-0.18 | 306 | 0.000 |
| `U_ESD3` | C3708426 | 180deg @0.22mm | 0.107 | 0.000 | +0.18,+0.66,-0.02,-0.79 | 103 | 0.054 |
| `U_DATA2` | C11355 | 270deg @0.01mm | 0.103 | 0.012 | +1.12,-0.01,-1.05,-0.18 | 323 | 0.000 |
| `U_DATA1` | C11355 | 270deg @0.01mm | 0.101 | 0.012 | +1.18,-0.01,-1.13,-0.18 | 306 | 0.000 |
| `U_DATA3` | C11355 | 270deg @0.01mm | 0.100 | 0.012 | +1.04,-0.01,-1.00,-0.18 | 327 | 0.000 |
| `U_ESD1` | C3708426 | 180deg @0.22mm | 0.094 | 0.000 | +0.23,+0.66,-0.10,-0.79 | 100 | 0.054 |
| `U_ESD2` | C3708426 | 180deg @0.22mm | 0.079 | 0.000 | +0.14,+0.66,-0.06,-0.79 | 103 | 0.054 |
| `U_ESD_UP` | C3708426 | 180deg @0.22mm | 0.071 | 0.000 | +0.64,+0.10,-0.68,-0.24 | 128 | 0.054 |

## 4 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `L_PD` | **MOUNT-FALLBACK** | best 0.52mm at 0deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is  |
| `U_AGG` | **PAD-MULTIPLICITY** | pad number(s) 25,26 appear a different number of times on the two footprints (ours {'25': 7, '26': 4} vs JLC {'25': 1, '26': 1}) — a NAMING convention, not a geometry defect; those numbers a |
| `U_HUB` | **PAD-MULTIPLICITY** | pad number(s) 65 appear a different number of times on the two footprints (ours {'65': 18} vs JLC {'65': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROI |
| `U_PWR_CTRL` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |

