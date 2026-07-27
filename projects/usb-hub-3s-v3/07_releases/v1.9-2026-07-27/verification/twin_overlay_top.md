# Twin render faithfulness — twin_top.png (`--side top`)

- calibration: **7.4174 px/mm** x, **7.4159 px/mm** y, anisotropy **1.0002** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..150.050 x, 19.950..112.050 y mm
- courtyards drawn (F.CrtYd): **129**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 53 measured / 121 refs with an expected body** (68 unresolvable, 0 resolvable but NOT measured, 1 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## FAIL — 29 ref(s): the render disagrees with the geometry

| ref | LCSC | centre delta mm | outward mm | expected | measured |
|---|---|---|---|---|---|
| `J1` | C98732 | **6.792** | **1.508** | 13.850,32.650..31.950,48.150 | 12.400,31.142..19.815,49.616 |
| `Q2` | C404363 | **1.978** | **0.558** | 73.548,28.727..78.948,34.777 | 72.664,27.232..79.270,32.356 |
| `Q4` | C404363 | **1.952** | **0.532** | 73.548,66.727..78.948,72.777 | 72.664,65.258..79.270,70.383 |
| `Q1` | C2760089 | **1.902** | **0.554** | 33.594,64.690..38.898,70.790 | 32.623,63.236..39.229,68.495 |
| `Q6` | C2760089 | **1.820** | **0.417** | 101.594,88.690..106.898,94.790 | 100.706,87.373..107.312,92.497 |
| `Q5` | C404363 | **1.677** | **0.263** | 73.052,71.223..78.452,77.273 | 72.664,73.349..79.270,78.473 |
| `C10` | C77102 | **1.669** | **0.091** | 58.300,29.850..61.500,32.350 | 57.834,29.659..58.643,32.221 |
| `C25` | C77102 | **1.663** | **0.064** | 58.300,67.850..61.500,70.350 | 57.834,67.686..58.643,70.383 |
| `C14` | C84455 | **1.662** | **0.055** | 88.900,24.150..92.100,26.650 | 88.438,23.995..89.247,26.557 |
| `C29` | C84455 | **1.660** | **0.028** | 88.900,62.150..92.100,64.650 | 88.438,62.022..89.247,64.584 |
| `C16` | C84455 | **1.655** | **0.085** | 92.400,42.250..95.600,44.750 | 91.943,42.065..92.752,44.762 |
| `C31` | C84455 | **1.653** | **0.059** | 92.400,80.250..95.600,82.750 | 91.943,80.091..92.752,82.788 |
| `C24` | C77102 | **1.653** | **0.119** | 59.500,63.050..62.700,65.550 | 59.047,62.831..59.856,65.528 |
| `Q3` | C404363 | **1.651** | **0.237** | 73.052,33.223..78.452,39.273 | 72.664,35.322..79.270,40.447 |
| `C15` | C84455 | **1.642** | **0.155** | 94.000,24.250..97.200,26.750 | 93.561,23.995..94.370,26.692 |
| `C30` | C84455 | **1.640** | **0.128** | 94.000,62.250..97.200,64.750 | 93.561,62.022..94.370,64.719 |
| `C17` | C84455 | **1.635** | **0.129** | 97.500,41.350..100.700,43.850 | 97.066,41.121..97.875,43.818 |
| `C32` | C84455 | **1.633** | **0.102** | 97.500,79.350..100.700,81.850 | 97.066,79.148..97.875,81.844 |
| `C50` | C77100 | **1.606** | **0.000** | 123.900,89.750..127.100,92.250 | 123.491,89.666..124.300,92.228 |
| `C49` | C77100 | **1.581** | **0.000** | 120.100,85.850..123.300,88.350 | 119.716,85.755..120.525,88.317 |
| `C11` | C77102 | **1.549** | **0.146** | 67.500,25.050..70.700,27.550 | 70.237,24.804..71.046,27.501 |
| `C26` | C77102 | **1.547** | **0.119** | 67.500,63.050..70.700,65.550 | 70.237,62.831..71.046,65.528 |
| `C12` | C77102 | **1.542** | **0.082** | 72.900,21.750..76.100,24.250 | 75.630,21.568..76.439,24.130 |
| `C27` | C77102 | **1.540** | **0.055** | 72.900,59.750..76.100,62.250 | 75.630,59.595..76.439,62.157 |
| `C9` | C77102 | **1.501** | **0.115** | 60.400,24.750..63.600,27.250 | 63.092,24.535..63.901,27.232 |
| `J5` | C5337088 | **0.962** | **1.537** | 115.530,104.516..124.470,112.266 | 114.053,104.903..125.917,113.803 |
| `J3` | C503996 | **0.715** | **1.447** | 138.208,49.168..152.512,63.852 | 138.186,47.728..153.960,65.393 |
| `J4` | C503996 | **0.714** | **1.447** | 138.208,71.168..152.512,85.852 | 138.186,69.708..153.960,87.373 |
| `J2` | C503996 | **0.713** | **1.447** | 138.208,27.168..152.512,41.852 | 138.186,25.614..153.960,43.413 |

## Graded refs (53)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J1` | C98732 | 270deg @0.00mm | 6.792 | 1.508 | -1.45,-1.51,-12.13,+1.47 | 1568 | 0.050 |
| `Q2` | C404363 | NONE (best 2.87mm) -> JLC's own transform | 1.978 | 0.558 | -0.88,-1.50,+0.32,-2.42 | 1322 | 1.769 |
| `Q4` | C404363 | NONE (best 2.87mm) -> JLC's own transform | 1.952 | 0.532 | -0.88,-1.47,+0.32,-2.39 | 1328 | 1.769 |
| `Q1` | C2760089 | NONE (best 2.85mm) -> JLC's own transform | 1.902 | 0.554 | -0.97,-1.45,+0.33,-2.30 | 1366 | 1.757 |
| `Q6` | C2760089 | NONE (best 2.85mm) -> JLC's own transform | 1.820 | 0.417 | -0.89,-1.32,+0.41,-2.29 | 1323 | 1.757 |
| `Q5` | C404363 | NONE (best 2.87mm) -> JLC's own transform | 1.677 | 0.263 | -0.39,+2.13,+0.82,+1.20 | 1346 | 1.769 |
| `C10` | C77102 | 0deg @0.04mm | 1.669 | 0.091 | -0.47,-0.19,-2.86,-0.13 | 46 | 0.000 |
| `C25` | C77102 | 0deg @0.04mm | 1.663 | 0.064 | -0.47,-0.16,-2.86,+0.03 | 45 | 0.000 |
| `C14` | C84455 | 0deg @0.05mm | 1.662 | 0.055 | -0.46,-0.15,-2.85,-0.09 | 46 | 0.000 |
| `C29` | C84455 | 0deg @0.05mm | 1.660 | 0.028 | -0.46,-0.13,-2.85,-0.07 | 48 | 0.000 |
| `C16` | C84455 | 0deg @0.05mm | 1.655 | 0.085 | -0.46,-0.19,-2.85,+0.01 | 47 | 0.000 |
| `C31` | C84455 | 0deg @0.05mm | 1.653 | 0.059 | -0.46,-0.16,-2.85,+0.04 | 49 | 0.000 |
| `C24` | C77102 | 0deg @0.04mm | 1.653 | 0.119 | -0.45,-0.22,-2.84,-0.02 | 46 | 0.000 |
| `Q3` | C404363 | NONE (best 2.87mm) -> JLC's own transform | 1.651 | 0.237 | -0.39,+2.10,+0.82,+1.17 | 1344 | 1.769 |
| `C15` | C84455 | 0deg @0.05mm | 1.642 | 0.155 | -0.44,-0.25,-2.83,-0.06 | 48 | 0.000 |
| `C30` | C84455 | 0deg @0.05mm | 1.640 | 0.128 | -0.44,-0.23,-2.83,-0.03 | 49 | 0.000 |
| `C17` | C84455 | 0deg @0.05mm | 1.635 | 0.129 | -0.43,-0.23,-2.82,-0.03 | 49 | 0.000 |
| `C32` | C84455 | 0deg @0.05mm | 1.633 | 0.102 | -0.43,-0.20,-2.82,-0.01 | 49 | 0.000 |
| `C50` | C77100 | 0deg @0.05mm | 1.606 | 0.000 | -0.41,-0.08,-2.80,-0.02 | 46 | 0.000 |
| `C49` | C77100 | 0deg @0.05mm | 1.581 | 0.000 | -0.38,-0.10,-2.78,-0.03 | 40 | 0.000 |
| `C11` | C77102 | 0deg @0.05mm | 1.549 | 0.146 | +2.74,-0.25,+0.35,-0.05 | 43 | 0.000 |
| `C26` | C77102 | 0deg @0.05mm | 1.547 | 0.119 | +2.74,-0.22,+0.35,-0.02 | 43 | 0.000 |
| `C12` | C77102 | 0deg @0.05mm | 1.542 | 0.082 | +2.73,-0.18,+0.34,-0.12 | 40 | 0.000 |
| `C27` | C77102 | 0deg @0.05mm | 1.540 | 0.055 | +2.73,-0.16,+0.34,-0.09 | 41 | 0.000 |
| `C9` | C77102 | 0deg @0.04mm | 1.501 | 0.115 | +2.69,-0.22,+0.30,-0.02 | 35 | 0.000 |
| `J5` | C5337088 | 0deg @0.00mm | 0.962 | 1.537 | -1.48,+0.39,+1.45,+1.54 | 4157 | 0.049 |
| `J3` | C503996 | 0deg @0.00mm | 0.715 | 1.447 | -0.02,-1.44,+1.45,+1.54 | 11708 | 0.370 |
| `J4` | C503996 | 0deg @0.00mm | 0.714 | 1.447 | -0.02,-1.46,+1.45,+1.52 | 11719 | 0.370 |
| `J2` | C503996 | 0deg @0.00mm | 0.713 | 1.447 | -0.02,-1.55,+1.45,+1.56 | 11782 | 0.370 |
| `C2` | C2982822 | 0deg @0.03mm | 0.546 | 0.000 | +0.07,+0.36,-0.23,+0.72 | 1437 | 0.000 |
| `C1` | C2982822 | 0deg @0.03mm | 0.544 | 0.000 | +0.07,+0.36,-0.23,+0.71 | 1437 | 0.000 |
| `U8` | C7519 | 270deg @0.01mm | 0.285 | 0.317 | -0.31,-0.32,+0.25,-0.25 | 173 | 0.000 |
| `F1` | C5249699 | NONE (best 3.26mm) -> JLC's own transform | 0.280 | 0.264 | +0.02,-0.26,-0.21,-0.26 | 4454 | 4.960 |
| `U9` | C7519 | 270deg @0.01mm | 0.240 | 0.202 | -0.17,-0.20,+0.25,-0.27 | 151 | 0.000 |
| `U5` | C130056 | 270deg @0.05mm | 0.201 | 0.184 | +0.01,-0.18,-0.04,-0.22 | 334 | 0.000 |
| `RS1` | C127692 | 0deg @0.11mm | 0.167 | 0.091 | -0.16,-0.59,+0.14,+0.26 | 1089 | 0.075 |
| `L1` | C408523 | 0deg @0.38mm | 0.161 | 0.333 | -0.50,-0.33,+0.48,+0.01 | 9140 | 0.000 |
| `D1` | C83846 | 0deg @0.21mm | 0.145 | 0.023 | -0.72,-0.02,+0.62,-0.25 | 866 | 0.000 |
| `Q7` | C78284 | 180deg @0.08mm | 0.143 | 0.030 | -0.04,-0.03,+0.15,-0.23 | 123 | 0.021 |
| `RS2` | C127692 | 0deg @0.11mm | 0.141 | 0.088 | -0.16,-0.56,+0.14,+0.28 | 1078 | 0.075 |
| `U2` | C13755 | 270deg @0.01mm | 0.138 | 0.000 | +1.04,+0.03,-1.19,-0.26 | 1204 | 0.001 |
| `U11` | C13755 | 270deg @0.01mm | 0.116 | 0.000 | +1.04,+0.06,-1.19,-0.24 | 1204 | 0.001 |
| `U4` | C130056 | 270deg @0.05mm | 0.114 | 0.299 | +0.01,-0.30,-0.04,+0.07 | 369 | 0.000 |
| `U12` | C7519 | 270deg @0.01mm | 0.103 | 0.135 | -0.29,+0.07,+0.26,+0.13 | 191 | 0.000 |
| `Q8` | C78284 | 180deg @0.08mm | 0.097 | 0.000 | -0.35,+0.09,+0.24,-0.25 | 125 | 0.021 |
| `SW1` | C2939728 | 0deg @0.50mm | 0.091 | 0.016 | -0.53,-0.02,+0.51,-0.17 | 1854 | 0.000 |
| `U10` | C7519 | 270deg @0.01mm | 0.085 | 0.114 | -0.31,+0.05,+0.25,+0.11 | 173 | 0.000 |
| `U7` | C473910 | 270deg @0.01mm | 0.082 | 0.000 | -0.26,+0.10,+0.16,-0.24 | 154 | 0.000 |
| `D5` | C113976 | 0deg @0.21mm | 0.076 | 0.012 | -0.63,+0.05,+0.71,-0.18 | 881 | 0.000 |
| `L2` | C408523 | 0deg @0.38mm | 0.068 | 0.172 | -0.50,-0.17,+0.48,+0.04 | 9054 | 0.000 |
| `F2` | C6165170 | 0deg @0.09mm | 0.066 | 0.046 | -0.72,-0.20,+0.69,+0.07 | 2128 | 0.000 |
| `U6` | C473910 | 270deg @0.01mm | 0.048 | 0.000 | -0.26,+0.04,+0.16,-0.02 | 154 | 0.000 |
| `U3` | C130056 | 270deg @0.05mm | 0.029 | 0.009 | +0.01,-0.01,-0.04,-0.04 | 338 | 0.000 |

## Not measurable by construction (68) — named, never silently passed

- `C13` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C18` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C19` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C20` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C21` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C22` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C23` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C28` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C3` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C33` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C34` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C35` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C36` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C37` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C38` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C39` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C4` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C40` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C41` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C42` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C43` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C5` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C53` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C54` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `C6` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C7` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C8` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `D10` — body 2.02x1.25 mm is under the 2.0 mm resolvability floor (9.3 px, and erosion costs 4 px)
- `D11` — body 2.02x1.25 mm is under the 2.0 mm resolvability floor (9.3 px, and erosion costs 4 px)
- `D12` — body 2.02x1.25 mm is under the 2.0 mm resolvability floor (9.3 px, and erosion costs 4 px)
- `D2` — body 3.71x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `D3` — body 2.65x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `D4` — body 2.65x1.30 mm is under the 2.0 mm resolvability floor (9.6 px, and erosion costs 4 px)
- `D8` — body 2.02x1.25 mm is under the 2.0 mm resolvability floor (9.3 px, and erosion costs 4 px)
- `D9` — body 2.02x1.25 mm is under the 2.0 mm resolvability floor (9.3 px, and erosion costs 4 px)
- `R1` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R10` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R11` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R13` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R14` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R15` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R16` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R17` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R18` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R19` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R2` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R20` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R21` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R22` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R27` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R28` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R29` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R3` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R30` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R34` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `R35` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `R37` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R38` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R39` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R4` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R40` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R41` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R42` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R5` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R6` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R7` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R8` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R9` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)

## No JLC model at all (1) — nothing to grade

- `R12` — C2984354: no JLC footprint cached (never fetched)

## 23 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `C1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C1` | **POLARITY-FIT-BLIND** | no usable polarity marking on our footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `C2` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C2` | **POLARITY-FIT-BLIND** | no usable polarity marking on our footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D1` | **PAD-GEOM** | pad 1<->2 ours 4.30mm vs JLC 4.72mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D1` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D10` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D10` | **POLARITY-FIT** | the pad-number fit says offset 180, but the MARKING channel disagrees by 180deg: our polarity marking sits at pad 1 (margin 0.69mm) while JLC's sits at pad 2 (margin 0.23mm) — the two librar |
| `D11` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D11` | **POLARITY-FIT** | the pad-number fit says offset 180, but the MARKING channel disagrees by 180deg: our polarity marking sits at pad 1 (margin 0.69mm) while JLC's sits at pad 2 (margin 0.23mm) — the two librar |
| `D12` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D12` | **POLARITY-FIT** | the pad-number fit says offset 180, but the MARKING channel disagrees by 180deg: our polarity marking sits at pad 1 (margin 0.69mm) while JLC's sits at pad 2 (margin 0.23mm) — the two librar |
| `D2` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D3` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D4` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D5` | **PAD-GEOM** | pad 1<->2 ours 4.30mm vs JLC 4.72mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D5` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D5` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D8` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D8` | **POLARITY-FIT** | the pad-number fit says offset 180, but the MARKING channel disagrees by 180deg: our polarity marking sits at pad 1 (margin 0.69mm) while JLC's sits at pad 2 (margin 0.23mm) — the two librar |
| `D9` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D9` | **POLARITY-FIT** | the pad-number fit says offset 180, but the MARKING channel disagrees by 180deg: our polarity marking sits at pad 1 (margin 0.69mm) while JLC's sits at pad 2 (margin 0.23mm) — the two librar |
| `F1` | **PAD-MULTIPLICITY** | pad number(s) 1,2 appear a different number of times on the two footprints (ours {'1': 2, '2': 2} vs JLC {'1': 1, '2': 1}) — a NAMING convention, not a geometry defect; those numbers are fit |
| `F1` | **PAD-GEOM** | pad 1<->2 ours 9.92mm vs JLC 3.40mm (d6.52mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F1` | **PAD-MISMATCH** | best=(3.2600000000000007, False, 90) |
| `F1` | **MOUNT-FALLBACK** | best 3.26mm at 90deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is |
| `F1` | **MODEL-REG** | body center 5.0mm off courtyard, area ratio 0.89, incl. pad_geom_delta=6.52mm -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=0 (authoritative); body asymmetric (0.0mm bbox- |
| `L1` | **PAD-GEOM** | pad 1<->2 ours 11.25mm vs JLC 12.00mm (d0.75mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `L2` | **PAD-GEOM** | pad 1<->2 ours 11.25mm vs JLC 12.00mm (d0.75mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q1` | **PAD-GEOM** | pad 2<->5 ours 5.08mm vs JLC 5.40mm (d0.31mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q2` | **PAD-GEOM** | pad 2<->5 ours 5.08mm vs JLC 5.45mm (d0.37mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q3` | **PAD-GEOM** | pad 2<->5 ours 5.08mm vs JLC 5.45mm (d0.37mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q4` | **PAD-GEOM** | pad 2<->5 ours 5.08mm vs JLC 5.45mm (d0.37mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q5` | **PAD-GEOM** | pad 2<->5 ours 5.08mm vs JLC 5.45mm (d0.37mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q6` | **PAD-GEOM** | pad 2<->5 ours 5.08mm vs JLC 5.40mm (d0.31mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `R12` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C2984354'] |
| `SW1` | **PAD-GEOM** | pad 1<->3 ours 5.00mm vs JLC 4.00mm (d1.00mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |

## Per-ref crops

- `C1` -> `overlay_C1.png`
- `C10` -> `overlay_C10.png`
- `C11` -> `overlay_C11.png`
- `C12` -> `overlay_C12.png`
- `C14` -> `overlay_C14.png`
- `C15` -> `overlay_C15.png`
- `C16` -> `overlay_C16.png`
- `C17` -> `overlay_C17.png`
- `C2` -> `overlay_C2.png`
- `C24` -> `overlay_C24.png`
- `C25` -> `overlay_C25.png`
- `C26` -> `overlay_C26.png`
- `C27` -> `overlay_C27.png`
- `C29` -> `overlay_C29.png`
- `C30` -> `overlay_C30.png`
- `C31` -> `overlay_C31.png`
- `C32` -> `overlay_C32.png`
- `C49` -> `overlay_C49.png`
- `C50` -> `overlay_C50.png`
- `C9` -> `overlay_C9.png`
- `D1` -> `overlay_D1.png`
- `D10` -> `overlay_D10.png`
- `D11` -> `overlay_D11.png`
- `D12` -> `overlay_D12.png`
- `D2` -> `overlay_D2.png`
- `D3` -> `overlay_D3.png`
- `D4` -> `overlay_D4.png`
- `D5` -> `overlay_D5.png`
- `D8` -> `overlay_D8.png`
- `D9` -> `overlay_D9.png`
- `F1` -> `overlay_F1.png`
- `J1` -> `overlay_J1.png`
- `J2` -> `overlay_J2.png`
- `J3` -> `overlay_J3.png`
- `J4` -> `overlay_J4.png`
- `J5` -> `overlay_J5.png`
- `L1` -> `overlay_L1.png`
- `L2` -> `overlay_L2.png`
- `Q1` -> `overlay_Q1.png`
- `Q2` -> `overlay_Q2.png`
- `Q3` -> `overlay_Q3.png`
- `Q4` -> `overlay_Q4.png`
- `Q5` -> `overlay_Q5.png`
- `Q6` -> `overlay_Q6.png`
- `R12` -> `overlay_R12.png`
- `SW1` -> `overlay_SW1.png`

