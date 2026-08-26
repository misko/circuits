# Twin render faithfulness — twin_top_hires.png (`--side top`)

- calibration: **15.2259 px/mm** x, **15.2117 px/mm** y, anisotropy **1.0009** (tol 0.02) — orthographic, projection valid
- board edge: 11.950..200.050 x, 9.950..102.050 y mm
- courtyards drawn (F.CrtYd): **243**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 52 measured / 208 refs with an expected body** (156 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- overlay: `twin_top_hires_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (52)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J_KEY_MATRIX` | C2683602 | 0deg @0.01mm | 0.948 | 0.000 | -0.10,+3.31,-1.78,-3.50 | 5901 | 0.084 |
| `J_ESTOP` | C160403 | 0deg @0.00mm | 0.809 | 0.018 | +1.35,-0.38,+0.27,+0.34 | 3860 | 0.047 |
| `J_PWR` | C587657 | 180deg @0.00mm | 0.330 | 0.126 | -0.40,-0.01,+0.14,+0.62 | 11122 | 0.580 |
| `Q_SWA` | C15127 | 180deg @0.28mm | 0.222 | 0.175 | -0.58,+0.05,+0.20,+0.18 | 936 | 0.071 |
| `Q_SWB` | C15127 | 180deg @0.28mm | 0.200 | 0.174 | -0.55,-0.17,+0.22,-0.05 | 957 | 0.071 |
| `U_TC` | C2653162 | 270deg @0.06mm | 0.174 | 0.192 | -0.69,-0.19,+0.46,-0.06 | 5467 | 0.000 |
| `U_DECU` | C5620 | 270deg @0.27mm | 0.162 | 0.218 | -0.53,-0.22,+0.36,-0.06 | 10083 | 0.000 |
| `U_DECUEN` | C22046 | 180deg @0.21mm | 0.162 | 0.216 | -0.42,-0.22,+0.32,-0.09 | 1371 | 0.000 |
| `Q_SWDRVB` | C8545 | 180deg @0.08mm | 0.162 | 0.174 | -0.54,-0.17,+0.31,-0.05 | 963 | 0.021 |
| `CE1` | C2887273 | 0deg @0.03mm | 0.152 | 0.144 | -0.65,+0.04,+0.41,+0.14 | 9558 | 0.000 |
| `J_THERM_A` | C265111 | 0deg @0.01mm | 0.150 | 0.190 | -0.29,-0.24,-0.01,+0.23 | 12975 | 0.027 |
| `U_DECD` | C5620 | 270deg @0.27mm | 0.146 | 0.218 | -0.49,-0.22,+0.40,-0.06 | 10260 | 0.000 |
| `Q_SWRHA` | C15127 | 180deg @0.28mm | 0.136 | 0.174 | -0.47,-0.17,+0.31,-0.05 | 946 | 0.071 |
| `U_AND1` | C22046 | 180deg @0.21mm | 0.135 | 0.196 | -0.42,-0.20,+0.38,-0.07 | 1340 | 0.000 |
| `U_AND3` | C22046 | 180deg @0.21mm | 0.135 | 0.196 | -0.38,-0.20,+0.36,-0.07 | 1321 | 0.000 |
| `U_AND2` | C22046 | 180deg @0.21mm | 0.134 | 0.196 | -0.40,-0.20,+0.40,-0.07 | 1340 | 0.000 |
| `U_COMP` | C7984 | 270deg @0.24mm | 0.130 | 0.128 | -0.58,+0.05,+0.32,-0.06 | 4770 | 0.000 |
| `U_COMP2` | C7984 | 270deg @0.24mm | 0.130 | 0.128 | -0.58,+0.05,+0.32,-0.05 | 4766 | 0.000 |
| `Q_SWRHE` | C15127 | 180deg @0.28mm | 0.126 | 0.174 | -0.45,-0.17,+0.33,-0.05 | 954 | 0.071 |
| `U_CAND2` | C22046 | 180deg @0.21mm | 0.122 | 0.183 | -0.35,-0.18,+0.38,-0.06 | 1373 | 0.000 |
| `F1` | C89650 | 0deg @0.29mm | 0.121 | 0.070 | -0.51,-0.17,+0.31,+0.05 | 3648 | 0.000 |
| `Q_SWDRVA` | C8545 | 180deg @0.08mm | 0.119 | 0.065 | -0.51,+0.07,+0.27,-0.07 | 859 | 0.021 |
| `J_RH_EXHAUST` | C189896 | 0deg @0.00mm | 0.118 | 0.015 | -0.12,-0.11,+0.11,+0.35 | 8503 | 0.097 |
| `J_RH_AMBIENT` | C189896 | 0deg @0.00mm | 0.118 | 0.076 | -0.18,-0.11,+0.18,+0.35 | 8509 | 0.097 |
| `Q_SWDRVRHA` | C8545 | 180deg @0.08mm | 0.115 | 0.174 | -0.45,-0.17,+0.39,-0.05 | 947 | 0.021 |
| `U_LATCHG` | C22046 | 180deg @0.21mm | 0.113 | 0.149 | -0.44,+0.02,+0.29,+0.15 | 1349 | 0.000 |
| `D_REVCLAMP` | C8678 | 0deg @0.20mm | 0.105 | 0.105 | -1.01,+0.04,+0.80,-0.06 | 2952 | 0.000 |
| `U_ADC` | C16939 | 270deg @0.27mm | 0.102 | 0.066 | -0.51,+0.04,+0.31,-0.07 | 10053 | 0.000 |
| `J_MODE` | C485354 | 180deg @0.00mm | 0.102 | 0.006 | +0.07,-0.26,+0.13,+0.21 | 10030 | 0.900 |
| `Q_SWDRVRHE` | C8545 | 180deg @0.08mm | 0.098 | 0.157 | -0.41,-0.16,+0.37,-0.03 | 989 | 0.021 |
| `D_TVS` | C113974 | 0deg @0.21mm | 0.092 | 0.100 | -0.80,+0.02,+0.63,-0.09 | 4355 | 0.000 |
| `U_ULNA` | C165895 | 270deg @0.15mm | 0.088 | 0.108 | -0.54,+0.01,+0.41,+0.11 | 22130 | 0.000 |
| `J_THERM_B` | C265111 | 0deg @0.01mm | 0.082 | 0.122 | -0.22,-0.24,+0.06,+0.23 | 13045 | 0.027 |
| `Q_REV` | C15127 | 180deg @0.28mm | 0.079 | 0.133 | -0.46,+0.01,+0.39,+0.13 | 1001 | 0.071 |
| `U_SR1` | C10092 | 270deg @0.27mm | 0.067 | 0.065 | -0.51,+0.05,+0.38,-0.05 | 10046 | 0.000 |
| `U_LDO` | C6186 | 180deg @0.27mm | 0.065 | 0.120 | -0.53,-0.00,+0.64,-0.06 | 8217 | 0.190 |
| `U_ULNB` | C165895 | 270deg @0.15mm | 0.062 | 0.108 | -0.42,+0.01,+0.47,+0.11 | 22125 | 0.000 |
| `J_LOADCELL` | C157991 | 180deg @0.08mm | 0.055 | 0.130 | -0.09,-0.13,+0.08,+0.02 | 19084 | 0.975 |
| `U_DECDEN` | C22046 | 180deg @0.21mm | 0.053 | 0.048 | -0.44,+0.00,+0.36,-0.07 | 1287 | 0.000 |
| `Q_COIL` | C15127 | 180deg @0.28mm | 0.050 | 0.021 | -0.47,+0.03,+0.37,-0.04 | 927 | 0.071 |
| `Q_STOPDRV` | C8545 | 180deg @0.08mm | 0.048 | 0.012 | -0.45,+0.03,+0.39,-0.10 | 929 | 0.021 |
| `D_KSTOP` | C8678 | 0deg @0.20mm | 0.047 | 0.000 | -0.90,+0.02,+0.84,-0.09 | 2933 | 0.000 |
| `U_OSCLR` | C22046 | 180deg @0.21mm | 0.039 | 0.004 | -0.40,+0.01,+0.34,-0.06 | 1283 | 0.000 |
| `J_PI` | C35165 | NONE (best 2.54mm) -> JLC's own transform | 0.034 | 0.000 | -1.49,+23.02,+1.53,-22.96 | 8501 | 0.000 |
| `U_ONESHOT` | C133954 | 270deg @0.27mm | 0.034 | 0.027 | -0.47,+0.03,+0.42,-0.07 | 10074 | 0.000 |
| `U_WD` | C7719 | 270deg @0.01mm | 0.029 | 0.000 | -0.30,+0.03,+0.24,-0.04 | 1225 | 0.002 |
| `U_FAULTAND` | C22046 | 180deg @0.21mm | 0.026 | 0.022 | -0.42,+0.05,+0.38,-0.09 | 1293 | 0.000 |
| `U_OPTO` | C125121 | 270deg @0.24mm | 0.022 | 0.024 | -0.67,+0.08,+0.69,-0.05 | 9136 | 0.000 |
| `Q_COILDRV` | C8545 | 180deg @0.08mm | 0.019 | 0.002 | -0.44,+0.03,+0.40,-0.04 | 904 | 0.021 |
| `U_SCHM` | C6820 | 270deg @0.15mm | 0.013 | 0.007 | -0.44,+0.14,+0.45,-0.12 | 8582 | 0.000 |
| `U_EXP` | C558584 | 270deg @0.04mm | 0.012 | 0.000 | -0.55,+0.04,+0.52,-0.04 | 13708 | 0.001 |
| `U_CAND1` | C22046 | 180deg @0.21mm | 0.011 | 0.014 | -0.39,+0.03,+0.41,-0.04 | 1285 | 0.000 |

## Not measurable by construction (156) — named, never silently passed

- `C_3V3` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_3V3A1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `C_3V3A2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_ADCV` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_ADCV2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_AND1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_AND2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_AND3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_CAND1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_CAND2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_COMP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_COMP2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_DECD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_DECDEN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_DECU` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_DECUEN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_DVDT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_EFIN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_EXP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FAULTAND` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_FLT7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_IN1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `C_IN2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_KR` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `C_LATCHA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_LATCHB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_LATCHG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_LDOIN` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `C_LDOOUT` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `C_MR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_OENAND` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_OS` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_OS2` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_OSCLR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_OSV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_SCHM` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_SR1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_STOPINV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_STOPR` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `C_SWA` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_SWB` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_SWRHA` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_SWRHE` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_TCAV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_TCD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_TCDV` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_TCNA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_TCPA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `C_ULNA` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_ULNB` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (12.2 px, and erosion costs 4 px)
- `C_WD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `D_COILEN` — body 1.30x2.50 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `D_ESD_IN` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `D_ESTOP` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `D_LCCLK` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `D_LCDAT` — body 2.50x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `FB1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (19.8 px, and erosion costs 4 px)
- `R_AND1PD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_AND2PD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_BID0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_BID1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_CLMPA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_CLMPB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_COILENPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_COILENS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_CTRREQPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_CTRSAFEPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_DECDPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_DECUPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_ESTOPOKPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_ESTOPOKSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_ESTOPPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_ESTOPS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_FAULTPU` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_FAULTSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_FLCPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_FSETNPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_GPB3PD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_HOSTAUTHPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_HSG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_HYS1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_HYS2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_ILM` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_KEY` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (24.4 px, and erosion costs 4 px)
- `R_KRSTPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_LCCLK` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_LCDAT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_MCUENPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_MODEHWPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_MODEHWSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_MODEPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_MR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OE` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OPENB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OPENT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OPTOLED` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (12.3 px, and erosion costs 4 px)
- `R_OS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OS2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OVB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_OVT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_PG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_RAENAPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_RAENBPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_RAENRHAPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_RAENRHEPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REARMPU` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_REF7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SCLA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SCLB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SDAA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SDAB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SER7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SHIELD` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (12.3 px, and erosion costs 4 px)
- `R_STOP` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (24.4 px, and erosion costs 4 px)
- `R_STOPPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_STOPRAIL` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (12.3 px, and erosion costs 4 px)
- `R_STOPREQNPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SWPUA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SWPUB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SWPURHA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_SWPURHE` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_TCN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_TCP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_TEMPOK` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_TEMPOKSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_TH1` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (24.4 px, and erosion costs 4 px)
- `R_TH2` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (24.4 px, and erosion costs 4 px)
- `R_WDOKPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_WDOKSER` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `R_WDPETPD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (7.6 px, and erosion costs 4 px)
- `U_EFUSE` — body 2.02x2.00 mm is under the 2.0 mm resolvability floor (30.5 px, and erosion costs 4 px)
- `U_LATCHA` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (30.5 px, and erosion costs 4 px)
- `U_LATCHB` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (30.5 px, and erosion costs 4 px)
- `U_OENAND` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (30.5 px, and erosion costs 4 px)
- `U_STOPINV` — body 2.11x2.00 mm is under the 2.0 mm resolvability floor (30.5 px, and erosion costs 4 px)

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

