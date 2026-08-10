# Twin render faithfulness — twin_top.png (`--side top`)

- calibration: **7.4174 px/mm** x, **7.4251 px/mm** y, anisotropy **0.9990** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..150.050 x, 19.950..110.050 y mm
- courtyards drawn (F.CrtYd): **206**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 57 measured / 195 refs with an expected body** (138 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (10 LCSC transform entries)
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (57)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `U13` | C11355 | 270deg @0.01mm | 0.740 | 0.254 | -0.32,-0.25,-1.14,-0.02 | 699 | 0.000 |
| `U14` | C11355 | 270deg @0.01mm | 0.677 | 0.254 | -0.25,-0.25,-1.07,-0.02 | 703 | 0.000 |
| `Q2` | C454269 | NONE (best 1.09mm) -> JLC's own transform | 0.326 | 0.000 | -0.36,+0.06,-0.24,-0.30 | 2766 | 0.887 |
| `C413` | C309062 | 0deg @0.04mm | 0.311 | 0.057 | -0.44,-0.16,-0.13,-0.10 | 340 | 0.000 |
| `C423` | C309062 | 0deg @0.05mm | 0.302 | 0.075 | -0.44,-0.17,-0.14,+0.02 | 345 | 0.000 |
| `U1` | C3215601 | 0deg @0.03mm | 0.290 | 0.325 | -0.07,-0.33,-0.10,-0.23 | 684 | 0.000 |
| `C112` | C23742 | 0deg @0.05mm | 0.286 | 0.128 | -0.48,-0.23,-0.03,-0.03 | 346 | 0.000 |
| `C114` | C23742 | 0deg @0.05mm | 0.282 | 0.137 | -0.46,-0.24,-0.02,-0.04 | 358 | 0.000 |
| `C115` | C23742 | 0deg @0.05mm | 0.279 | 0.023 | -0.42,-0.12,-0.11,-0.06 | 321 | 0.000 |
| `C208` | C3844168 | 0deg @0.05mm | 0.264 | 0.064 | -0.45,-0.16,-0.01,-0.11 | 346 | 0.000 |
| `C210` | C3844168 | 0deg @0.05mm | 0.257 | 0.107 | -0.38,-0.21,-0.08,-0.01 | 341 | 0.000 |
| `C108` | C3844168 | 0deg @0.05mm | 0.255 | 0.064 | -0.44,-0.16,+0.00,-0.11 | 354 | 0.000 |
| `C433` | C309062 | 0deg @0.05mm | 0.247 | 0.057 | +0.02,-0.16,+0.46,+0.04 | 347 | 0.000 |
| `C113` | C23742 | 0deg @0.05mm | 0.243 | 0.090 | +0.00,-0.19,+0.45,+0.00 | 347 | 0.000 |
| `C209` | C3844168 | 0deg @0.05mm | 0.243 | 0.140 | -0.35,-0.24,-0.04,-0.05 | 332 | 0.000 |
| `C215` | C23742 | 0deg @0.05mm | 0.240 | 0.047 | -0.43,-0.15,+0.01,-0.09 | 338 | 0.000 |
| `C214` | C23742 | 0deg @0.05mm | 0.239 | 0.022 | -0.44,-0.12,-0.00,-0.06 | 342 | 0.000 |
| `C109` | C3844168 | 0deg @0.05mm | 0.239 | 0.084 | -0.44,-0.18,-0.00,+0.01 | 357 | 0.000 |
| `C212` | C23742 | 0deg @0.05mm | 0.231 | 0.018 | -0.43,-0.12,+0.01,-0.06 | 355 | 0.000 |
| `C213` | C23742 | 0deg @0.05mm | 0.229 | 0.104 | -0.42,-0.20,+0.02,-0.01 | 361 | 0.000 |
| `C110` | C3844168 | 0deg @0.05mm | 0.228 | 0.114 | +0.04,-0.21,+0.35,-0.02 | 336 | 0.000 |
| `C207` | C3844168 | 0deg @0.05mm | 0.227 | 0.058 | -0.41,-0.16,+0.03,-0.10 | 336 | 0.000 |
| `C107` | C3844168 | 0deg @0.05mm | 0.226 | 0.119 | +0.04,-0.22,+0.34,-0.03 | 339 | 0.000 |
| `RS1` | C844901 | 0deg @0.11mm | 0.223 | 0.203 | -0.53,-0.28,+0.31,-0.11 | 1881 | 0.075 |
| `RS2` | C844901 | 0deg @0.11mm | 0.214 | 0.203 | -0.44,-0.28,+0.27,-0.11 | 1888 | 0.075 |
| `C443` | C309062 | 0deg @0.05mm | 0.211 | 0.057 | -0.42,-0.16,+0.02,+0.04 | 360 | 0.000 |
| `J1` | C3819953 | 0deg @0.00mm | 0.193 | 0.067 | -0.07,+0.50,-0.17,-0.20 | 4520 | 0.548 |
| `J2` | C86462 | 0deg @0.17mm | 0.180 | 0.296 | -0.30,-0.10,-0.05,-0.01 | 15391 | 4.055 |
| `Q4` | C404363 | NONE (best 1.64mm) -> JLC's own transform | 0.171 | 0.000 | -0.40,+0.11,+0.27,-0.42 | 2574 | 0.029 |
| `Y1` | C1985204 | 0deg @0.05mm | 0.164 | 0.000 | +0.07,-0.10,+0.10,-0.18 | 496 | 0.000 |
| `U2` | C13755 | 270deg @0.01mm | 0.162 | 0.056 | +1.04,-0.06,-1.20,-0.23 | 2366 | 0.001 |
| `Q6` | C404363 | NONE (best 1.64mm) -> JLC's own transform | 0.160 | 0.011 | -0.31,+0.11,+0.36,-0.42 | 2597 | 0.029 |
| `F1` | C5249699 | NONE (best 3.26mm) -> JLC's own transform | 0.156 | 0.287 | -0.04,-0.29,+0.00,-0.02 | 9962 | 4.960 |
| `U8` | C6053 | 270deg @0.06mm | 0.155 | 0.278 | +0.88,-0.28,-0.95,-0.03 | 1915 | 0.000 |
| `L2` | C408523 | 0deg @0.38mm | 0.147 | 0.211 | -0.13,-0.62,+0.21,+0.34 | 17674 | 0.000 |
| `L1` | C408523 | 0deg @0.38mm | 0.142 | 0.185 | -0.18,-0.62,+0.16,+0.34 | 17678 | 0.000 |
| `U18` | C7519 | 270deg @0.01mm | 0.142 | 0.102 | -0.40,+0.04,+0.16,+0.10 | 293 | 0.000 |
| `U3` | C13755 | 270deg @0.01mm | 0.141 | 0.056 | +1.12,-0.06,-1.11,-0.23 | 2268 | 0.001 |
| `U16` | C11355 | 270deg @0.01mm | 0.141 | 0.254 | -0.17,-0.25,+0.23,-0.02 | 735 | 0.000 |
| `U7` | C2847904 | 270deg @0.09mm | 0.139 | 0.000 | -0.27,-0.34,+0.16,+0.08 | 4490 | 0.000 |
| `U15` | C11355 | 270deg @0.01mm | 0.138 | 0.254 | -0.19,-0.25,+0.21,-0.02 | 739 | 0.000 |
| `Q3` | C404363 | NONE (best 1.64mm) -> JLC's own transform | 0.137 | 0.000 | -0.34,+0.22,+0.19,-0.45 | 2546 | 0.029 |
| `J7` | C19191796 | 270deg @0.01mm | 0.133 | 0.083 | -0.08,-0.05,-0.10,-0.15 | 2179 | 2.617 |
| `D1` | C315992 | 0deg @0.21mm | 0.132 | 0.095 | -0.01,-0.85,-0.05,+0.59 | 1423 | 0.000 |
| `U6` | C478081 | 0deg @0.04mm | 0.128 | 0.000 | +0.04,-0.07,-0.06,-0.18 | 7858 | 0.000 |
| `Q5` | C404363 | NONE (best 1.64mm) -> JLC's own transform | 0.127 | 0.000 | -0.39,+0.22,+0.28,-0.45 | 2558 | 0.029 |
| `Q1` | C454269 | NONE (best 1.09mm) -> JLC's own transform | 0.126 | 0.067 | -0.07,+0.05,+0.32,-0.04 | 2963 | 0.887 |
| `D4` | C85098 | 0deg @0.19mm | 0.124 | 0.086 | -0.74,-0.03,+0.53,-0.11 | 1010 | 0.000 |
| `L3` | C307880 | 0deg @0.40mm | 0.107 | 0.195 | -0.00,-0.20,-0.09,-0.00 | 3105 | 0.000 |
| `D7` | C85098 | 0deg @0.19mm | 0.103 | 0.042 | -0.58,+0.02,+0.69,-0.19 | 999 | 0.000 |
| `U4` | C5248536 | 270deg @0.06mm | 0.098 | 0.264 | -0.35,-0.26,+0.35,+0.07 | 347 | 0.000 |
| `D6` | C85098 | 0deg @0.19mm | 0.093 | 0.022 | -0.60,+0.02,+0.67,-0.19 | 999 | 0.000 |
| `U19` | C7519 | 270deg @0.01mm | 0.092 | 0.102 | -0.34,+0.04,+0.22,+0.10 | 290 | 0.000 |
| `D5` | C85098 | 0deg @0.19mm | 0.090 | 0.014 | -0.66,+0.02,+0.61,-0.19 | 985 | 0.000 |
| `U17` | C7519 | 270deg @0.01mm | 0.089 | 0.102 | -0.33,+0.04,+0.23,+0.10 | 317 | 0.000 |
| `U20` | C7519 | 270deg @0.01mm | 0.081 | 0.102 | -0.32,+0.04,+0.24,+0.10 | 295 | 0.000 |
| `U5` | C7519 | 270deg @0.01mm | 0.032 | 0.062 | -0.06,+0.01,+0.00,+0.02 | 680 | 0.000 |

## Not measurable by construction (138) — named, never silently passed

- `C1` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C101` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C102` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C103` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C104` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C105` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C106` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C111` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C116` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C2` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C201` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C202` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C203` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C204` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C205` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C206` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C21` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C211` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C216` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C22` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C23` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C24` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C3` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C30` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C31` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C32` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C33` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C34` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C35` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C36` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C37` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C38` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C39` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C40` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C41` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C410` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C411` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C412` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C414` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C415` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C42` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C420` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C421` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C422` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C424` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C425` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C43` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C430` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C431` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C432` — body 0.80x1.60 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C434` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C435` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C44` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C440` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C441` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C442` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C444` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C445` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C45` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `D2` — body 2.65x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `D3` — body 2.65x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `R1` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R101` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R102` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R103` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R104` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R105` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R106` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R107` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R108` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R109` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R110` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `R2` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R201` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R202` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R203` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R204` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R205` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R206` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R207` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R208` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R209` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R210` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `R3` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R30` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R31` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R32` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R33` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R34` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R35` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R36` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R37` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R4` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R410` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R411` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R412` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R413` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R414` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R415` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R416` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R417` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R418` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R419` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R420` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R421` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R422` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R423` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R424` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R425` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R426` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R427` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R428` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R429` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R430` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R431` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R432` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R433` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R434` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R435` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R436` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R437` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R438` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R439` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R440` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R441` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R442` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R443` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R444` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R445` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R446` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R447` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R448` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R449` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R5` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `U10` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U11` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U12` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U9` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)

## 24 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `D1` | **PAD-GEOM** | pad 1<->2 ours 4.30mm vs JLC 4.72mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D1` | **POLARITY-FIT-BLIND** | no usable polarity marking on our footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D2` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D3` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D4` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.38mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D4` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D4` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D5` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.38mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D5` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D5` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D6` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.38mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D6` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D6` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D7` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.38mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D7` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D7` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `F1` | **PAD-MULTIPLICITY** | pad number(s) 1,2 appear a different number of times on the two footprints (ours {'1': 2, '2': 2} vs JLC {'1': 1, '2': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `F1` | **PAD-GEOM** | pad 1<->2 ours 9.92mm vs JLC 3.40mm (d6.52mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F1` | **PAD-MISMATCH** | best=(3.2600000000000007, False, 90) |
| `F1` | **MOUNT-FALLBACK** | best 3.26mm at 90deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is |
| `F1` | **MODEL-REG** | body center 5.0mm off courtyard, area ratio 0.89, incl. pad_geom_delta=6.52mm -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=0 (authoritative); body asymmetric (0.0mm bbox- |
| `J2` | **MODEL-REG** | body center 4.1mm off courtyard, area ratio 1.91, incl. pad_geom_delta=0.20mm -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=0 (authoritative); body asymmetric (4.3mm bbox- |
| `J7` | **MODEL-REG** | body center 2.6mm off courtyard, area ratio 0.96 -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=0 (authoritative); body asymmetric (0.0mm bbox-center offset) so this metric |
| `L1` | **PAD-GEOM** | pad 1<->2 ours 11.25mm vs JLC 12.00mm (d0.75mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `L2` | **PAD-GEOM** | pad 1<->2 ours 11.25mm vs JLC 12.00mm (d0.75mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `L3` | **PAD-GEOM** | pad 1<->2 ours 4.20mm vs JLC 5.00mm (d0.80mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q1` | **PAD-MULTIPLICITY** | pad number(s) 3,8 appear a different number of times on the two footprints (ours {'3': 1, '8': 1} vs JLC {'3': 2, '8': 2}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `Q1` | **PAD-GEOM** | pad 3<->5 ours 4.08mm vs JLC 5.78mm (d1.70mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q1` | **PAD-MISMATCH** | best=(1.089891307654121, False, 270) |
| `Q1` | **MOUNT-FALLBACK** | best 1.09mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `Q2` | **PAD-MULTIPLICITY** | pad number(s) 3,8 appear a different number of times on the two footprints (ours {'3': 1, '8': 1} vs JLC {'3': 2, '8': 2}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `Q2` | **PAD-GEOM** | pad 3<->5 ours 4.08mm vs JLC 5.78mm (d1.70mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q2` | **PAD-MISMATCH** | best=(1.089891307654121, False, 270) |
| `Q2` | **MOUNT-FALLBACK** | best 1.09mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `Q3` | **PAD-MULTIPLICITY** | pad number(s) 5 appear a different number of times on the two footprints (ours {'5': 2} vs JLC {'5': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `Q3` | **PAD-GEOM** | pad 1<->5 ours 5.25mm vs JLC 6.97mm (d1.72mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q3` | **PAD-MISMATCH** | best=(1.6443216217270307, False, 270) |
| `Q3` | **MOUNT-FALLBACK** | best 1.64mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `Q4` | **PAD-MULTIPLICITY** | pad number(s) 5 appear a different number of times on the two footprints (ours {'5': 2} vs JLC {'5': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `Q4` | **PAD-GEOM** | pad 1<->5 ours 5.25mm vs JLC 6.97mm (d1.72mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q4` | **PAD-MISMATCH** | best=(1.6443216217270307, False, 270) |
| `Q4` | **MOUNT-FALLBACK** | best 1.64mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `Q5` | **PAD-MULTIPLICITY** | pad number(s) 5 appear a different number of times on the two footprints (ours {'5': 2} vs JLC {'5': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `Q5` | **PAD-GEOM** | pad 1<->5 ours 5.25mm vs JLC 6.97mm (d1.72mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q5` | **PAD-MISMATCH** | best=(1.6443216217270307, False, 270) |
| `Q5` | **MOUNT-FALLBACK** | best 1.64mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `Q6` | **PAD-MULTIPLICITY** | pad number(s) 5 appear a different number of times on the two footprints (ours {'5': 2} vs JLC {'5': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `Q6` | **PAD-GEOM** | pad 1<->5 ours 5.25mm vs JLC 6.97mm (d1.72mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q6` | **PAD-MISMATCH** | best=(1.6443216217270307, False, 270) |
| `Q6` | **MOUNT-FALLBACK** | best 1.64mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `U10` | **PAD-MULTIPLICITY** | pad number(s) 5,6 appear a different number of times on the two footprints (ours {'5': 5, '6': 5} vs JLC {'5': 1, '6': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `U10` | **PAD-GEOM** | pad 1<->4 ours 1.42mm vs JLC 1.80mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U11` | **PAD-MULTIPLICITY** | pad number(s) 5,6 appear a different number of times on the two footprints (ours {'5': 5, '6': 5} vs JLC {'5': 1, '6': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `U11` | **PAD-GEOM** | pad 1<->4 ours 1.42mm vs JLC 1.80mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U12` | **PAD-MULTIPLICITY** | pad number(s) 5,6 appear a different number of times on the two footprints (ours {'5': 5, '6': 5} vs JLC {'5': 1, '6': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `U12` | **PAD-GEOM** | pad 1<->4 ours 1.42mm vs JLC 1.80mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U6` | **PAD-MULTIPLICITY** | pad number(s) 65 appear a different number of times on the two footprints (ours {'65': 18} vs JLC {'65': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROI |
| `U9` | **PAD-MULTIPLICITY** | pad number(s) 5,6 appear a different number of times on the two footprints (ours {'5': 5, '6': 5} vs JLC {'5': 1, '6': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `U9` | **PAD-GEOM** | pad 1<->4 ours 1.42mm vs JLC 1.80mm (d0.38mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |

## Per-ref crops

- `D1` -> `overlay_D1.png`
- `D2` -> `overlay_D2.png`
- `D3` -> `overlay_D3.png`
- `D4` -> `overlay_D4.png`
- `D5` -> `overlay_D5.png`
- `D6` -> `overlay_D6.png`
- `D7` -> `overlay_D7.png`
- `F1` -> `overlay_F1.png`
- `J2` -> `overlay_J2.png`
- `J7` -> `overlay_J7.png`
- `L1` -> `overlay_L1.png`
- `L2` -> `overlay_L2.png`
- `L3` -> `overlay_L3.png`
- `Q1` -> `overlay_Q1.png`
- `Q2` -> `overlay_Q2.png`
- `Q3` -> `overlay_Q3.png`
- `Q4` -> `overlay_Q4.png`
- `Q5` -> `overlay_Q5.png`
- `Q6` -> `overlay_Q6.png`
- `U10` -> `overlay_U10.png`
- `U11` -> `overlay_U11.png`
- `U12` -> `overlay_U12.png`
- `U6` -> `overlay_U6.png`
- `U9` -> `overlay_U9.png`

