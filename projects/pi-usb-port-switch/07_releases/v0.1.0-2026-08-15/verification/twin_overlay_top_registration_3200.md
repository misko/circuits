# Twin render faithfulness — twin_top_registration_3200.png (`--side top`)

board_sha256: d4bc778c1c80453ec7b198e1bf428b22cb03d414c4a0d86c89ab74d6facc4094
a-render_verdict: PASS
- calibration: **12.8648 px/mm** x, **12.8560 px/mm** y, anisotropy **1.0007** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..170.050 x, 19.950..140.050 y mm
- courtyards drawn (F.CrtYd): **197**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 27 measured / 186 refs with an expected body** (159 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (5 LCSC transform entries)
- overlay: `twin_top_registration_3200_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (27)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `U1` | C7527500 | 270deg @0.48mm | 0.088 | 0.066 | +1.09,-0.07,-1.09,-0.11 | 3737 | 0.160 |
| `J2` | C5364405 | 270deg @0.00mm | 0.086 | 0.035 | +0.05,-0.04,-0.07,-0.14 | 34960 | 0.007 |
| `J1` | C3819953 | 0deg @0.00mm | 0.084 | 0.083 | -0.03,-0.08,-0.06,-0.06 | 13041 | 0.225 |
| `J3` | C5334230 | 0deg @0.01mm | 0.080 | 0.050 | -0.05,+0.03,-0.08,-0.13 | 34523 | 0.075 |
| `Q2` | C85049 | 180deg @0.28mm | 0.077 | 0.042 | +0.30,-0.04,-0.41,-0.06 | 451 | 0.071 |
| `F1` | C5249699 | NONE (best 3.26mm) -> JLC's own transform | 0.066 | 0.002 | +0.03,-0.00,-0.03,-0.13 | 16512 | 4.960 |
| `C1` | C136277 | 0deg @0.03mm | 0.065 | 0.015 | -0.03,-0.02,-0.06,-0.08 | 6080 | 0.000 |
| `J5` | C5334230 | 0deg @0.01mm | 0.064 | 0.050 | -0.05,+0.04,-0.08,-0.05 | 34531 | 0.075 |
| `J7` | C5334230 | 0deg @0.01mm | 0.064 | 0.050 | -0.05,+0.04,-0.08,-0.05 | 34484 | 0.075 |
| `J9` | C5334230 | 0deg @0.01mm | 0.064 | 0.050 | -0.05,+0.04,-0.08,-0.04 | 34537 | 0.075 |
| `C2` | C136277 | 0deg @0.03mm | 0.060 | 0.016 | -0.02,-0.02,-0.05,-0.08 | 6110 | 0.000 |
| `U2` | C2675181 | 270deg @0.04mm | 0.053 | 0.000 | +0.03,-0.03,-0.03,-0.08 | 2256 | 0.000 |
| `U4` | C130056 | 270deg @0.05mm | 0.053 | 0.000 | +0.03,-0.06,-0.02,-0.05 | 1089 | 0.000 |
| `U8` | C2675181 | 270deg @0.04mm | 0.051 | 0.000 | +0.03,-0.02,-0.03,-0.08 | 2297 | 0.000 |
| `Q1` | C397981 | 0deg @0.00mm | 0.051 | 0.000 | -0.00,-0.09,-0.02,-0.01 | 4635 | 0.000 |
| `C69` | C264054 | 0deg @0.03mm | 0.045 | 0.050 | +0.65,+0.04,-0.63,+0.05 | 6120 | 0.000 |
| `C21` | C264054 | 0deg @0.03mm | 0.043 | 0.047 | +0.65,-0.05,-0.63,-0.04 | 6095 | 0.000 |
| `Q5` | C85049 | 180deg @0.28mm | 0.037 | 0.022 | +0.38,+0.04,-0.41,+0.02 | 443 | 0.071 |
| `U22` | C130056 | 270deg @0.05mm | 0.033 | 0.000 | +0.03,+0.03,-0.02,+0.04 | 1109 | 0.000 |
| `U20` | C2675181 | 270deg @0.04mm | 0.032 | 0.000 | +0.03,+0.06,-0.03,+0.01 | 2299 | 0.000 |
| `U14` | C2675181 | 270deg @0.04mm | 0.030 | 0.000 | +0.03,+0.06,-0.03,+0.00 | 2299 | 0.000 |
| `Q3` | C85049 | 180deg @0.28mm | 0.020 | 0.000 | +0.30,+0.04,-0.34,-0.06 | 442 | 0.071 |
| `Q4` | C85049 | 180deg @0.28mm | 0.019 | 0.000 | +0.30,+0.04,-0.34,-0.06 | 442 | 0.071 |
| `U10` | C130056 | 270deg @0.05mm | 0.012 | 0.000 | +0.03,+0.02,-0.02,-0.04 | 1077 | 0.000 |
| `C53` | C264054 | 0deg @0.03mm | 0.010 | 0.000 | +0.65,+0.04,-0.63,-0.03 | 6027 | 0.000 |
| `C37` | C264054 | 0deg @0.03mm | 0.010 | 0.000 | +0.65,+0.03,-0.63,-0.03 | 6042 | 0.000 |
| `U16` | C130056 | 270deg @0.05mm | 0.009 | 0.000 | +0.03,+0.02,-0.02,-0.04 | 1079 | 0.000 |

## Not measurable by construction (159) — named, never silently passed

- `C10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C11` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C12` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C13` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C14` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C15` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C16` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C17` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C18` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C19` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C20` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C22` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C23` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C24` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C25` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C26` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C27` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C28` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C29` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C30` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C31` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C32` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C33` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C34` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C35` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C36` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C38` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C39` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C40` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C41` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C42` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C43` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C44` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C45` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C46` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C47` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C48` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C49` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C50` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C51` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C52` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C54` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C55` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C56` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C57` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C58` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C59` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C60` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C61` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C62` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C63` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C64` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C65` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C66` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C67` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C68` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `C9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R11` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R12` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R13` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R14` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R15` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R16` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R17` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R18` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R19` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R20` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R21` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R22` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R23` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R24` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R25` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R26` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R27` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R28` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R29` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R30` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R31` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R32` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R33` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R34` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R35` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R36` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R37` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R38` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R39` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R40` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R41` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R42` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R43` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R44` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R45` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R46` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R47` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R48` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R49` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R50` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R51` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R52` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R53` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R54` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R55` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R56` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R57` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R58` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R59` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R60` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R61` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R62` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R63` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R64` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R65` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R66` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R67` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R68` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R69` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R70` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R71` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R72` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R73` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R74` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R75` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R76` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R77` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R78` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R79` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R80` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `R9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (6.4 px, and erosion costs 4 px)
- `U11` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U12` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U13` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (25.7 px, and erosion costs 4 px)
- `U15` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (19.6 px, and erosion costs 4 px)
- `U17` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U18` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U19` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (25.7 px, and erosion costs 4 px)
- `U21` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (19.6 px, and erosion costs 4 px)
- `U23` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U24` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U25` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (25.7 px, and erosion costs 4 px)
- `U3` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (19.6 px, and erosion costs 4 px)
- `U5` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U6` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (17.7 px, and erosion costs 4 px)
- `U7` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (25.7 px, and erosion costs 4 px)
- `U9` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (19.6 px, and erosion costs 4 px)

## 11 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `C1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C2` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C21` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C37` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C53` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C69` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `F1` | **PAD-MULTIPLICITY** | pad number(s) 1,2 appear a different number of times on the two footprints (ours {'1': 2, '2': 2} vs JLC {'1': 1, '2': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `F1` | **MOUNT-FALLBACK** | best 3.26mm at 90deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is |
| `U10` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U16` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U22` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U4` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |

