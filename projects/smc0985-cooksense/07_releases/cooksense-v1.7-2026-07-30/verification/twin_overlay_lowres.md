# Twin render faithfulness — twin_top.png (`--side top`)

- calibration: **5.1356 px/mm** x, **5.1249 px/mm** y, anisotropy **1.0021** (tol 0.02) — orthographic, projection valid
- board edge: 11.950..200.050 x, 9.950..102.050 y mm
- courtyards drawn (F.CrtYd): **243**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 51 measured / 208 refs with an expected body** (156 unresolvable, 1 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## FAIL — 1 ref(s): the render disagrees with the geometry

| ref | LCSC | centre delta mm | outward mm | expected | measured |
|---|---|---|---|---|---|
| `U_LDO` | C6186 | **1.248** | **0.116** | 18.255,66.750..25.365,73.250 | 20.128,66.927..25.970,73.366 |

## FAIL — 1 ref(s) that SHOULD have been measurable and were not

- `Q_SWDRVRHA` — only 13 body pixels found (floor 20) — not a body

## Graded refs (51)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `U_LDO` | C6186 | 180deg @0.27mm | 1.248 | 0.116 | +1.87,+0.18,+0.61,+0.12 | 576 | 0.190 |
| `J_KEY_MATRIX` | C2683602 | 0deg @0.01mm | 0.628 | 0.124 | -0.32,-0.19,-0.93,+0.06 | 1284 | 0.084 |
| `J_MODE` | C485354 | 180deg @0.00mm | 0.517 | 0.031 | +1.13,-0.28,-0.11,+0.09 | 1012 | 0.900 |
| `J_RH_EXHAUST` | C189896 | 0deg @0.00mm | 0.492 | 0.183 | -0.28,+0.75,-0.05,+0.18 | 836 | 0.097 |
| `Q_STOPDRV` | C8545 | 180deg @0.08mm | 0.370 | 0.074 | +0.33,-0.07,-1.00,-0.24 | 28 | 0.021 |
| `J_PWR` | C587657 | 180deg @0.00mm | 0.368 | 0.029 | -0.30,+0.07,+0.07,+0.63 | 945 | 0.580 |
| `J_THERM_A` | C265111 | 0deg @0.01mm | 0.352 | 0.084 | -0.18,+0.62,+0.00,+0.06 | 1189 | 0.027 |
| `J_THERM_B` | C265111 | 0deg @0.01mm | 0.351 | 0.081 | -0.18,+0.62,+0.01,+0.06 | 1188 | 0.027 |
| `Q_SWDRVRHE` | C8545 | 180deg @0.08mm | 0.350 | 0.010 | +0.33,-0.01,-1.01,-0.18 | 28 | 0.021 |
| `Q_COIL` | C15127 | 180deg @0.28mm | 0.325 | 0.112 | +0.15,-0.11,-0.80,+0.11 | 32 | 0.071 |
| `U_ULNA` | C165895 | 270deg @0.15mm | 0.303 | 0.127 | +1.21,-0.13,-1.80,-0.02 | 1933 | 0.000 |
| `Q_SWDRVA` | C8545 | 180deg @0.08mm | 0.272 | 0.113 | +0.40,-0.11,-0.94,+0.11 | 27 | 0.021 |
| `U_LATCHG` | C22046 | 180deg @0.21mm | 0.253 | 0.086 | +0.54,-0.09,-0.91,-0.25 | 38 | 0.000 |
| `U_COMP2` | C7984 | 270deg @0.24mm | 0.244 | 0.222 | +1.08,+0.24,-1.22,+0.22 | 335 | 0.000 |
| `U_OPTO` | C125121 | 270deg @0.24mm | 0.240 | 0.215 | -0.88,+0.11,+0.41,-0.20 | 632 | 0.000 |
| `CE1` | C2887273 | 0deg @0.03mm | 0.229 | 0.108 | -0.66,-0.07,+0.30,-0.23 | 904 | 0.000 |
| `D_TVS` | C113974 | 0deg @0.21mm | 0.228 | 0.333 | -1.03,+0.14,+0.58,-0.14 | 380 | 0.000 |
| `U_AND1` | C22046 | 180deg @0.21mm | 0.227 | 0.014 | +0.23,+0.18,-0.64,+0.01 | 47 | 0.000 |
| `Q_SWRHE` | C15127 | 180deg @0.28mm | 0.222 | 0.063 | +0.31,+0.23,-0.64,+0.06 | 44 | 0.071 |
| `J_ESTOP` | C160403 | 0deg @0.00mm | 0.205 | 0.006 | -0.35,-0.28,-0.05,+0.38 | 462 | 0.047 |
| `U_CAND2` | C22046 | 180deg @0.21mm | 0.191 | 0.140 | +0.54,-0.14,-0.91,+0.08 | 46 | 0.000 |
| `U_CAND1` | C22046 | 180deg @0.21mm | 0.189 | 0.074 | +0.62,-0.07,-0.83,-0.24 | 38 | 0.000 |
| `J_RH_AMBIENT` | C189896 | 0deg @0.00mm | 0.189 | 0.097 | -0.20,+0.16,+0.04,+0.18 | 845 | 0.097 |
| `U_ADC` | C16939 | 270deg @0.27mm | 0.187 | 0.220 | +0.80,-0.22,-1.12,+0.03 | 787 | 0.000 |
| `U_AND3` | C22046 | 180deg @0.21mm | 0.184 | 0.014 | +0.37,+0.18,-0.69,+0.01 | 46 | 0.000 |
| `Q_REV` | C15127 | 180deg @0.28mm | 0.184 | 0.160 | +0.49,-0.16,-0.85,+0.06 | 20 | 0.071 |
| `U_OSCLR` | C22046 | 180deg @0.21mm | 0.182 | 0.075 | +0.65,+0.05,-0.99,+0.07 | 36 | 0.000 |
| `U_DECD` | C5620 | 270deg @0.27mm | 0.181 | 0.172 | +1.08,-0.17,-1.43,+0.07 | 735 | 0.000 |
| `J_LOADCELL` | C157991 | 180deg @0.08mm | 0.180 | 0.166 | -0.17,-0.04,-0.17,-0.08 | 1851 | 0.975 |
| `U_SCHM` | C6820 | 270deg @0.15mm | 0.171 | 0.285 | +0.82,-0.29,-1.10,+0.09 | 690 | 0.000 |
| `U_AND2` | C22046 | 180deg @0.21mm | 0.164 | 0.014 | +0.30,+0.18,-0.56,+0.01 | 47 | 0.000 |
| `U_SR1` | C10092 | 270deg @0.27mm | 0.158 | 0.051 | +1.15,+0.19,-1.35,+0.05 | 705 | 0.000 |
| `U_DECDEN` | C22046 | 180deg @0.21mm | 0.156 | 0.245 | +0.38,-0.25,-0.68,+0.17 | 64 | 0.000 |
| `Q_SWB` | C15127 | 180deg @0.28mm | 0.154 | 0.063 | +0.62,+0.23,-0.71,+0.06 | 23 | 0.071 |
| `Q_SWRHA` | C15127 | 180deg @0.28mm | 0.154 | 0.063 | +0.62,+0.23,-0.71,+0.06 | 28 | 0.071 |
| `Q_COILDRV` | C8545 | 180deg @0.08mm | 0.153 | 0.112 | +0.32,-0.11,-0.63,+0.11 | 44 | 0.021 |
| `Q_SWDRVB` | C8545 | 180deg @0.08mm | 0.148 | 0.063 | +0.65,+0.23,-0.68,+0.06 | 23 | 0.021 |
| `U_DECUEN` | C22046 | 180deg @0.21mm | 0.144 | 0.013 | +0.62,+0.18,-0.83,+0.01 | 37 | 0.000 |
| `U_DECU` | C5620 | 270deg @0.27mm | 0.138 | 0.172 | +1.12,-0.17,-1.38,+0.07 | 735 | 0.000 |
| `U_ULNB` | C165895 | 270deg @0.15mm | 0.134 | 0.127 | +1.20,-0.13,-1.42,-0.02 | 1942 | 0.000 |
| `U_TC` | C2653162 | 270deg @0.06mm | 0.133 | 0.158 | -0.53,-0.16,+0.27,+0.11 | 488 | 0.000 |
| `U_EXP` | C558584 | 270deg @0.04mm | 0.128 | 0.216 | -0.50,-0.22,+0.27,+0.12 | 1245 | 0.001 |
| `D_KSTOP` | C8678 | 0deg @0.20mm | 0.121 | 0.078 | -0.98,+0.17,+0.75,-0.09 | 230 | 0.000 |
| `F1` | C89650 | 0deg @0.29mm | 0.118 | 0.105 | -0.49,-0.20,+0.27,+0.11 | 304 | 0.000 |
| `U_FAULTAND` | C22046 | 180deg @0.21mm | 0.117 | 0.159 | +0.62,-0.16,-0.83,+0.06 | 50 | 0.000 |
| `D_REVCLAMP` | C8678 | 0deg @0.20mm | 0.108 | 0.070 | -0.97,+0.13,+0.76,-0.13 | 229 | 0.000 |
| `U_ONESHOT` | C133954 | 270deg @0.27mm | 0.103 | 0.172 | +0.87,-0.07,-1.05,+0.17 | 744 | 0.000 |
| `U_COMP` | C7984 | 270deg @0.24mm | 0.075 | 0.087 | +1.08,-0.09,-1.22,+0.09 | 342 | 0.000 |
| `U_WD` | C7719 | 270deg @0.01mm | 0.048 | 0.112 | +0.68,-0.11,-0.78,+0.11 | 53 | 0.002 |
| `J_PI` | C35165 | NONE (best 2.54mm) -> JLC's own transform | 0.047 | 0.000 | -1.45,+23.04,+1.53,-22.99 | 708 | 0.000 |
| `Q_SWA` | C15127 | 180deg @0.28mm | 0.012 | 0.112 | +0.66,-0.11,-0.68,+0.11 | 29 | 0.071 |

## Not measurable by construction (156) — named, never silently passed

- `C_3V3` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_3V3A1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `C_3V3A2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_ADCV` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_ADCV2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_AND1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_AND2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_AND3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_CAND1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_CAND2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_COMP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_COMP2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_DECD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_DECDEN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_DECU` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_DECUEN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_DVDT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_EFIN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_EXP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FAULTAND` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_FLT7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_IN1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `C_IN2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_KR` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `C_LATCHA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_LATCHB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_LATCHG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_LDOIN` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `C_LDOOUT` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `C_MR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_OENAND` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_OS` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_OS2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_OSCLR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_OSV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_SCHM` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_SR1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_STOPINV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_STOPR` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `C_SWA` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_SWB` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_SWRHA` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_SWRHE` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_TCAV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_TCD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_TCDV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_TCNA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_TCPA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `C_ULNA` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_ULNB` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (4.1 px, and erosion costs 4 px)
- `C_WD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `D_COILEN` — body 1.30x2.50 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `D_ESD_IN` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `D_ESTOP` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `D_LCCLK` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `D_LCDAT` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `FB1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (6.7 px, and erosion costs 4 px)
- `R_AND1PD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_AND2PD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_BID0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_BID1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_CLMPA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_CLMPB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_COILENPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_COILENS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_CTRREQPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_CTRSAFEPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_DECDPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_DECUPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_ESTOPOKPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_ESTOPOKSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_ESTOPPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_ESTOPS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_FAULTPU` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_FAULTSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_FLCPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_FSETNPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_GPB3PD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_HOSTAUTHPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_HSG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_HYS1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_HYS2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_ILM` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_KEY` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (8.2 px, and erosion costs 4 px)
- `R_KRSTPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_LCCLK` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_LCDAT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_MCUENPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_MODEHWPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_MODEHWSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_MODEPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_MR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OE` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OPENB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OPENT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OPTOLED` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (4.2 px, and erosion costs 4 px)
- `R_OS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OS2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OVB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_OVT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_PG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_RAENAPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_RAENBPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_RAENRHAPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_RAENRHEPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REARMPU` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_REF7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SCLA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SCLB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SDAA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SDAB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SER7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SHIELD` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (4.2 px, and erosion costs 4 px)
- `R_STOP` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (8.2 px, and erosion costs 4 px)
- `R_STOPPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_STOPRAIL` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (4.2 px, and erosion costs 4 px)
- `R_STOPREQNPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SWPUA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SWPUB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SWPURHA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_SWPURHE` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_TCN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_TCP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_TEMPOK` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_TEMPOKSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_TH1` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (8.2 px, and erosion costs 4 px)
- `R_TH2` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (8.2 px, and erosion costs 4 px)
- `R_WDOKPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_WDOKSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `R_WDPETPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.6 px, and erosion costs 4 px)
- `U_EFUSE` — body 2.02x2.00 mm is under the 2.0 mm resolvability floor (10.3 px, and erosion costs 4 px)
- `U_LATCHA` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (10.3 px, and erosion costs 4 px)
- `U_LATCHB` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (10.3 px, and erosion costs 4 px)
- `U_OENAND` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (10.3 px, and erosion costs 4 px)
- `U_STOPINV` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (10.3 px, and erosion costs 4 px)

## 36 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `CE1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_COILEN` | **PAD-GEOM** | pad 1<->2 ours 2.10mm vs JLC 2.40mm (d0.30mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D_COILEN` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_COILEN` | **POLARITY-FIT-BLIND** | no usable polarity marking on our footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D_ESD_IN` | **PAD-GEOM** | pad 1<->2 ours 2.10mm vs JLC 2.40mm (d0.30mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D_ESD_IN` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_ESTOP` | **PAD-GEOM** | pad 1<->2 ours 2.10mm vs JLC 2.40mm (d0.30mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D_ESTOP` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_KSTOP` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.40mm (d0.40mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D_KSTOP` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_KSTOP` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D_LCCLK` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_LCDAT` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_REVCLAMP` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.40mm (d0.40mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D_REVCLAMP` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_REVCLAMP` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D_TVS` | **PAD-GEOM** | pad 1<->2 ours 4.30mm vs JLC 4.72mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D_TVS` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D_TVS` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `F1` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `J_PI` | **MIRRORED** | mirror fit 0.00mm vs non-mirror 2.54mm |
| `Q_COIL` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q_REV` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q_SWA` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q_SWB` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q_SWRHA` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `Q_SWRHE` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_ADC` | **PAD-GEOM** | pad 1<->16 ours 4.95mm vs JLC 5.48mm (d0.53mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_AND1` | **PAD-GEOM** | pad 1<->6 ours 2.27mm vs JLC 2.70mm (d0.43mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_AND2` | **PAD-GEOM** | pad 1<->6 ours 2.27mm vs JLC 2.70mm (d0.43mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_AND3` | **PAD-GEOM** | pad 1<->6 ours 2.27mm vs JLC 2.70mm (d0.43mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_CAND1` | **PAD-GEOM** | pad 1<->6 ours 2.28mm vs JLC 2.70mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_CAND2` | **PAD-GEOM** | pad 1<->6 ours 2.28mm vs JLC 2.70mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_COMP` | **PAD-GEOM** | pad 1<->8 ours 4.95mm vs JLC 5.42mm (d0.47mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_COMP2` | **PAD-GEOM** | pad 1<->8 ours 4.95mm vs JLC 5.42mm (d0.47mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_DECD` | **PAD-GEOM** | pad 1<->16 ours 4.95mm vs JLC 5.48mm (d0.53mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_DECDEN` | **PAD-GEOM** | pad 1<->6 ours 2.28mm vs JLC 2.70mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_DECU` | **PAD-GEOM** | pad 1<->16 ours 4.95mm vs JLC 5.48mm (d0.53mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_DECUEN` | **PAD-GEOM** | pad 1<->6 ours 2.28mm vs JLC 2.70mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_FAULTAND` | **PAD-GEOM** | pad 1<->6 ours 2.27mm vs JLC 2.70mm (d0.43mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_LATCHG` | **PAD-GEOM** | pad 1<->6 ours 2.28mm vs JLC 2.70mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_LDO` | **PAD-GEOM** | pad 2<->4 ours 6.30mm vs JLC 5.94mm (d0.36mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_ONESHOT` | **PAD-GEOM** | pad 1<->16 ours 4.95mm vs JLC 5.48mm (d0.53mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_OPTO` | **PAD-GEOM** | pad 1<->4 ours 9.53mm vs JLC 10.00mm (d0.47mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_OSCLR` | **PAD-GEOM** | pad 1<->6 ours 2.28mm vs JLC 2.70mm (d0.42mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U_SR1` | **PAD-GEOM** | pad 1<->16 ours 4.95mm vs JLC 5.48mm (d0.53mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |

## Per-ref crops

- `CE1` -> `overlay_CE1.png`
- `D_COILEN` -> `overlay_D_COILEN.png`
- `D_ESD_IN` -> `overlay_D_ESD_IN.png`
- `D_ESTOP` -> `overlay_D_ESTOP.png`
- `D_KSTOP` -> `overlay_D_KSTOP.png`
- `D_LCCLK` -> `overlay_D_LCCLK.png`
- `D_LCDAT` -> `overlay_D_LCDAT.png`
- `D_REVCLAMP` -> `overlay_D_REVCLAMP.png`
- `D_TVS` -> `overlay_D_TVS.png`
- `F1` -> `overlay_F1.png`
- `J_PI` -> `overlay_J_PI.png`
- `Q_COIL` -> `overlay_Q_COIL.png`
- `Q_REV` -> `overlay_Q_REV.png`
- `Q_SWA` -> `overlay_Q_SWA.png`
- `Q_SWB` -> `overlay_Q_SWB.png`
- `Q_SWRHA` -> `overlay_Q_SWRHA.png`
- `Q_SWRHE` -> `overlay_Q_SWRHE.png`
- `U_ADC` -> `overlay_U_ADC.png`
- `U_AND1` -> `overlay_U_AND1.png`
- `U_AND2` -> `overlay_U_AND2.png`
- `U_AND3` -> `overlay_U_AND3.png`
- `U_CAND1` -> `overlay_U_CAND1.png`
- `U_CAND2` -> `overlay_U_CAND2.png`
- `U_COMP` -> `overlay_U_COMP.png`
- `U_COMP2` -> `overlay_U_COMP2.png`
- `U_DECD` -> `overlay_U_DECD.png`
- `U_DECDEN` -> `overlay_U_DECDEN.png`
- `U_DECU` -> `overlay_U_DECU.png`
- `U_DECUEN` -> `overlay_U_DECUEN.png`
- `U_FAULTAND` -> `overlay_U_FAULTAND.png`
- `U_LATCHG` -> `overlay_U_LATCHG.png`
- `U_LDO` -> `overlay_U_LDO.png`
- `U_ONESHOT` -> `overlay_U_ONESHOT.png`
- `U_OPTO` -> `overlay_U_OPTO.png`
- `U_OSCLR` -> `overlay_U_OSCLR.png`
- `U_SR1` -> `overlay_U_SR1.png`

