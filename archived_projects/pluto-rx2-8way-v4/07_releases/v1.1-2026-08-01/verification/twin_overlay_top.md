# Twin render faithfulness — twin_top.png (`--side top`)

- calibration: **13.1936 px/mm** x, **13.2011 px/mm** y, anisotropy **0.9994** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..70.050 x, 19.950..93.050 y mm
- courtyards drawn (F.CrtYd): **32**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 11 measured / 27 refs with an expected body** (16 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (11)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J_ANT4` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.079 | 0.000 | +0.93,+0.92,-1.03,-1.04 | 2077 | 0.000 |
| `U_SW` | C5121458 | 0deg @0.01mm | 0.077 | 0.034 | -0.17,-0.22,+0.13,+0.07 | 2103 | 0.000 |
| `J_ANT7` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.075 | 0.000 | +2.29,+2.26,-2.35,-2.39 | 2081 | 0.000 |
| `J_ANT1` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.072 | 0.000 | +2.28,+2.27,-2.37,-2.38 | 2083 | 0.000 |
| `J_ANT5` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.060 | 0.000 | +2.29,+2.27,-2.35,-2.38 | 2081 | 0.000 |
| `J_ANT6` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.060 | 0.000 | +1.01,+0.92,-1.01,-1.04 | 2070 | 0.000 |
| `J_ANT2` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.056 | 0.000 | +0.98,+0.93,-1.05,-1.02 | 2075 | 0.000 |
| `J_RX2` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.055 | 0.000 | +0.94,+0.93,-1.01,-1.02 | 2077 | 0.000 |
| `J_ANT8` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.055 | 0.000 | +0.95,+0.93,-1.00,-1.03 | 2079 | 0.000 |
| `J_ANT3` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.055 | 0.000 | +2.32,+2.29,-2.40,-2.36 | 2079 | 0.000 |
| `J_RX1` | C504007 | NONE (best 5.08mm) -> JLC's own transform | 0.051 | 0.000 | +1.02,+0.93,-1.01,-1.03 | 2072 | 0.000 |

## Not measurable by construction (16) — named, never silently passed

- `C_BULK` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (17.2 px, and erosion costs 4 px)
- `C_SW1` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `C_SW2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (10.6 px, and erosion costs 4 px)
- `FB_3V3` — body 1.30x2.00 mm is under the 2.0 mm resolvability floor (17.2 px, and erosion costs 4 px)
- `LED_ST` — body 1.62x0.80 mm is under the 2.0 mm resolvability floor (10.6 px, and erosion costs 4 px)
- `R_LED` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_PD1` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_PD2` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_PD3` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_PD4` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_S1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_S2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_S3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_S4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_T1` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)
- `R_T2` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.6 px, and erosion costs 4 px)

## 1 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `LED_ST` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `LED_ST` | **POLARITY-FIT** | the pad-number fit says offset 180, but the MARKING channel disagrees by 180deg: our polarity marking sits at pad 1 (margin 0.68mm) while JLC's sits at pad 2 (margin 0.23mm) — the two librar |

## Per-ref crops

- `LED_ST` -> `overlay_LED_ST.png`

