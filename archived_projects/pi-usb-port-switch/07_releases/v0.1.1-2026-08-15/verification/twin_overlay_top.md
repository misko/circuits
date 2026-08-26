# Twin render faithfulness — twin_top.png (`--side top`)

board_sha256: 3cf5cc4491fdce418b802c2fa20a18f9b8f29c37e27c978ba8fe7065735dca45
a-render_verdict: FAIL
- calibration: **6.4357 px/mm** x, **6.4363 px/mm** y, anisotropy **0.9999** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..170.050 x, 19.950..140.050 y mm
- courtyards drawn (F.CrtYd): **197**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 27 measured / 186 refs with an expected body** (159 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (5 LCSC transform entries)
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## FAIL — 4 ref(s): the render disagrees with the geometry

| ref | LCSC | centre delta mm | outward mm | expected | measured |
|---|---|---|---|---|---|
| `J9` | C5334230 | **0.809** | **1.448** | 20.000,119.550..38.451,133.950 | 18.552,117.988..38.285,135.389 |
| `J3` | C5334230 | **0.808** | **1.448** | 20.000,35.550..38.451,49.950 | 18.552,34.089..38.285,51.490 |
| `J7` | C5334230 | **0.807** | **1.448** | 20.000,91.550..38.451,105.950 | 18.552,90.021..38.285,107.423 |
| `J5` | C5334230 | **0.807** | **1.448** | 20.000,63.550..38.451,77.950 | 18.552,62.055..38.285,79.456 |

## Graded refs (27)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J9` | C5334230 | 0deg @0.01mm | 0.809 | 1.448 | -1.45,-1.56,-0.17,+1.44 | 17208 | 0.075 |
| `J3` | C5334230 | 0deg @0.01mm | 0.808 | 1.448 | -1.45,-1.46,-0.17,+1.54 | 17038 | 0.075 |
| `J7` | C5334230 | 0deg @0.01mm | 0.807 | 1.448 | -1.45,-1.53,-0.17,+1.47 | 17167 | 0.075 |
| `J5` | C5334230 | 0deg @0.01mm | 0.807 | 1.448 | -1.45,-1.50,-0.17,+1.51 | 17191 | 0.075 |
| `J1` | C3819953 | 0deg @0.00mm | 0.410 | 0.117 | -0.12,-0.01,-0.69,-0.15 | 3271 | 0.225 |
| `Q5` | C85049 | 180deg @0.28mm | 0.310 | 0.336 | +0.64,-0.34,-0.63,-0.28 | 113 | 0.071 |
| `J2` | C5364405 | 270deg @0.00mm | 0.255 | 0.232 | -0.23,-0.19,-0.07,-0.22 | 15308 | 0.007 |
| `Q2` | C85049 | 180deg @0.28mm | 0.229 | 0.000 | -0.45,+0.08,-0.00,-0.03 | 105 | 0.071 |
| `C37` | C264054 | 0deg @0.03mm | 0.204 | 0.196 | -0.66,-0.20,+0.40,-0.11 | 2879 | 0.000 |
| `C69` | C264054 | 0deg @0.03mm | 0.196 | 0.263 | -0.66,-0.26,+0.40,-0.03 | 2942 | 0.000 |
| `C53` | C264054 | 0deg @0.03mm | 0.173 | 0.229 | -0.66,-0.23,+0.40,+0.01 | 2912 | 0.000 |
| `U20` | C2675181 | 270deg @0.04mm | 0.166 | 0.000 | -0.01,-0.08,-0.15,-0.21 | 941 | 0.000 |
| `U22` | C130056 | 270deg @0.05mm | 0.165 | 0.188 | -0.19,-0.12,+0.07,-0.19 | 483 | 0.000 |
| `C1` | C136277 | 0deg @0.03mm | 0.159 | 0.267 | -0.59,-0.27,+0.47,-0.03 | 2883 | 0.000 |
| `U1` | C7527500 | 270deg @0.48mm | 0.140 | 0.093 | -0.58,-0.07,+0.65,-0.20 | 1903 | 0.160 |
| `C21` | C264054 | 0deg @0.03mm | 0.139 | 0.162 | -0.66,-0.16,+0.40,+0.07 | 2915 | 0.000 |
| `U14` | C2675181 | 270deg @0.04mm | 0.137 | 0.000 | -0.01,-0.05,-0.15,-0.18 | 941 | 0.000 |
| `U16` | C130056 | 270deg @0.05mm | 0.134 | 0.188 | -0.19,-0.09,+0.07,-0.16 | 453 | 0.000 |
| `Q1` | C397981 | 0deg @0.00mm | 0.129 | 0.000 | -0.18,-0.09,-0.05,-0.03 | 2136 | 0.000 |
| `Q4` | C85049 | 180deg @0.28mm | 0.121 | 0.303 | +0.64,-0.30,-0.63,+0.06 | 104 | 0.071 |
| `U8` | C2675181 | 270deg @0.04mm | 0.111 | 0.000 | -0.01,-0.01,-0.15,-0.15 | 920 | 0.000 |
| `U10` | C130056 | 270deg @0.05mm | 0.104 | 0.188 | -0.19,-0.05,+0.07,-0.12 | 451 | 0.000 |
| `C2` | C136277 | 0deg @0.03mm | 0.091 | 0.177 | -0.60,-0.18,+0.46,+0.06 | 2865 | 0.000 |
| `U2` | C2675181 | 270deg @0.04mm | 0.090 | 0.000 | -0.01,+0.02,-0.15,-0.11 | 922 | 0.000 |
| `U4` | C130056 | 270deg @0.05mm | 0.078 | 0.188 | -0.19,-0.02,+0.07,-0.09 | 450 | 0.000 |
| `F1` | C5249699 | NONE (best 3.26mm) -> JLC's own transform | 0.045 | 0.165 | +0.02,-0.17,+0.02,+0.09 | 7284 | 4.960 |
| `Q3` | C85049 | 180deg @0.28mm | 0.012 | 0.000 | +0.64,+0.04,-0.63,-0.06 | 121 | 0.071 |

## Not measurable by construction (159) — named, never silently passed

- `C10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C11` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C12` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C13` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C14` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C15` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C16` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C17` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C18` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C19` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C20` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C22` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C23` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C24` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C25` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C26` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C27` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C28` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C29` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C30` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C31` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C32` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C33` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C34` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C35` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C36` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C38` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C39` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C40` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C41` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C42` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C43` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C44` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C45` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C46` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C47` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C48` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C49` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C50` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C51` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C52` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C54` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C55` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C56` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C57` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C58` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C59` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C60` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C61` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C62` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C63` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C64` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C65` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C66` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C67` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C68` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `C9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R11` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R12` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R13` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R14` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R15` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R16` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R17` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R18` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R19` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R20` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R21` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R22` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R23` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R24` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R25` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R26` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R27` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R28` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R29` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R30` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R31` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R32` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R33` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R34` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R35` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R36` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R37` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R38` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R39` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R40` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R41` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R42` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R43` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R44` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R45` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R46` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R47` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R48` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R49` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R50` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R51` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R52` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R53` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R54` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R55` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R56` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R57` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R58` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R59` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R60` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R61` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R62` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R63` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R64` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R65` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R66` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R67` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R68` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R69` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R70` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R71` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R72` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R73` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R74` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R75` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R76` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R77` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R78` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R79` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R80` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `R9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.2 px, and erosion costs 4 px)
- `U11` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U12` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U13` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (12.9 px, and erosion costs 4 px)
- `U15` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (9.8 px, and erosion costs 4 px)
- `U17` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U18` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U19` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (12.9 px, and erosion costs 4 px)
- `U21` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (9.8 px, and erosion costs 4 px)
- `U23` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U24` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U25` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (12.9 px, and erosion costs 4 px)
- `U3` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (9.8 px, and erosion costs 4 px)
- `U5` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U6` — body 1.37x3.50 mm is under the 2.0 mm resolvability floor (8.8 px, and erosion costs 4 px)
- `U7` — body 2.10x2.00 mm is under the 2.0 mm resolvability floor (12.9 px, and erosion costs 4 px)
- `U9` — body 1.52x2.02 mm is under the 2.0 mm resolvability floor (9.8 px, and erosion costs 4 px)

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

## Per-ref crops

- `C1` -> `overlay_C1.png`
- `C2` -> `overlay_C2.png`
- `C21` -> `overlay_C21.png`
- `C37` -> `overlay_C37.png`
- `C53` -> `overlay_C53.png`
- `C69` -> `overlay_C69.png`
- `F1` -> `overlay_F1.png`
- `J3` -> `overlay_J3.png`
- `J5` -> `overlay_J5.png`
- `J7` -> `overlay_J7.png`
- `J9` -> `overlay_J9.png`
- `U10` -> `overlay_U10.png`
- `U16` -> `overlay_U16.png`
- `U22` -> `overlay_U22.png`
- `U4` -> `overlay_U4.png`

