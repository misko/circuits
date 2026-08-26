# Twin render faithfulness — twin_top.png (`--side top`)

board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
a-render_verdict: PASS
- calibration: **7.4174 px/mm** x, **7.4251 px/mm** y, anisotropy **0.9990** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..150.050 x, 19.950..110.050 y mm
- courtyards drawn (F.CrtYd): **137**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 30 measured / 129 refs with an expected body** (99 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (1 LCSC transform entry)
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (30)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J_UP` | C86462 | 0deg @0.17mm | 0.325 | 0.000 | +1.22,+1.46,-1.85,-1.62 | 9759 | 0.180 |
| `J_PORT1` | C503996 | 0deg @0.00mm | 0.233 | 0.000 | -0.09,+0.57,-0.07,-0.13 | 9202 | 0.370 |
| `J_PORT2` | C503996 | 0deg @0.00mm | 0.223 | 0.000 | -0.04,+0.57,-0.03,-0.13 | 9203 | 0.370 |
| `J_PORT4` | C503996 | 0deg @0.00mm | 0.220 | 0.000 | +0.04,+0.57,-0.08,-0.13 | 9269 | 0.370 |
| `J_PORT3` | C503996 | 0deg @0.00mm | 0.219 | 0.000 | -0.00,+0.57,+0.01,-0.13 | 9199 | 0.370 |
| `U_BUCK` | C5248536 | 270deg @0.06mm | 0.187 | 0.106 | +0.54,-0.11,-0.78,-0.18 | 127 | 0.000 |
| `U_PWR_CTRL` | C130056 | 270deg @0.05mm | 0.170 | 0.045 | -0.08,-0.05,-0.14,-0.22 | 340 | 0.000 |
| `C_TRUNK_USB` | C136277 | 0deg @0.03mm | 0.155 | 0.078 | +0.54,-0.08,-0.65,-0.21 | 1850 | 0.000 |
| `L_MAIN` | C15269 | 0deg @0.10mm | 0.149 | 0.095 | +0.17,-0.09,-0.08,-0.19 | 575 | 0.000 |
| `U_PWR4` | C130056 | 270deg @0.05mm | 0.139 | 0.092 | +0.01,-0.09,-0.18,-0.13 | 341 | 0.000 |
| `C_PORT1_BULK` | C342660 | 0deg @0.04mm | 0.138 | 0.000 | -0.05,-0.05,-0.15,-0.13 | 299 | 0.000 |
| `U_PWR1` | C130056 | 270deg @0.05mm | 0.134 | 0.092 | +0.02,-0.09,-0.17,-0.13 | 316 | 0.000 |
| `Y_HUB` | C1985204 | 0deg @0.05mm | 0.130 | 0.000 | +0.05,-0.09,-0.04,-0.17 | 275 | 0.000 |
| `U_PWR3` | C130056 | 270deg @0.05mm | 0.125 | 0.092 | -0.03,-0.09,-0.09,-0.13 | 323 | 0.000 |
| `U_PWR2` | C130056 | 270deg @0.05mm | 0.116 | 0.092 | +0.06,-0.09,-0.13,-0.13 | 311 | 0.000 |
| `C_BUCK_OUT2` | C342660 | 0deg @0.05mm | 0.112 | 0.000 | +0.06,-0.07,-0.04,-0.15 | 299 | 0.000 |
| `C_PORT2_BULK` | C342660 | 0deg @0.05mm | 0.110 | 0.000 | -0.01,-0.05,-0.11,-0.13 | 300 | 0.000 |
| `Q_DATA3` | C85047 | 180deg @0.20mm | 0.109 | 0.000 | +0.70,+0.01,-0.60,-0.20 | 86 | 0.090 |
| `U_CTRL` | C640876 | 270deg @0.15mm | 0.106 | 0.033 | +0.99,-0.03,-1.10,-0.15 | 1454 | 0.000 |
| `Q_DATA1` | C85047 | 180deg @0.20mm | 0.104 | 0.000 | +0.68,+0.01,-0.75,-0.20 | 82 | 0.090 |
| `U_EXP` | C558584 | 270deg @0.04mm | 0.103 | 0.041 | +1.29,-0.04,-1.39,-0.14 | 2502 | 0.001 |
| `Q_DATA2` | C85047 | 180deg @0.20mm | 0.101 | 0.000 | +0.62,+0.01,-0.67,-0.20 | 100 | 0.090 |
| `C_TRUNK_BULK` | C342660 | 0deg @0.05mm | 0.097 | 0.000 | +0.02,-0.05,-0.08,-0.13 | 299 | 0.000 |
| `C_BUCK_OUT1` | C342660 | 0deg @0.05mm | 0.095 | 0.000 | +0.06,-0.06,-0.04,-0.13 | 299 | 0.000 |
| `C_PORT4_BULK` | C342660 | 0deg @0.05mm | 0.094 | 0.000 | +0.07,-0.05,-0.03,-0.13 | 299 | 0.000 |
| `C_PORT3_BULK` | C342660 | 0deg @0.05mm | 0.093 | 0.000 | +0.03,-0.05,-0.07,-0.13 | 296 | 0.000 |
| `Q_DATA4` | C85047 | 180deg @0.20mm | 0.071 | 0.000 | +0.71,+0.14,-0.58,-0.20 | 83 | 0.090 |
| `U_HUB` | C478081 | 0deg @0.04mm | 0.071 | 0.000 | +0.07,-0.01,-0.03,-0.12 | 3955 | 0.000 |
| `U_AND_DATA` | C6053 | 270deg @0.06mm | 0.059 | 0.000 | +0.83,+0.02,-0.86,-0.13 | 944 | 0.000 |
| `U_AND_PWR` | C6053 | 270deg @0.06mm | 0.058 | 0.000 | +0.93,+0.02,-0.91,-0.13 | 892 | 0.000 |

## Not measurable by construction (99) — named, never silently passed

- `C_AGG_DVDT` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C_AGG_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_AGG_TIMER` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C_AND_DATA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_AND_PWR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_BST` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_BUCK_IN` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C_CTRL_VDD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_CTRL_VUSB` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_DATA1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_DATA2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_DATA3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_DATA4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_EXP_VDD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_18` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_18PLL` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_A1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_A2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_A3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_A4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_A_BULK` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_CR_BULK` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_CR_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_DD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_PLL` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_HUB_RESET` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT1_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT2_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT3_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT4_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR1_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR2_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR3_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR4_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR_CTRL_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR_CTRL_OUT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR_CTRL_OUT_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_TRUNK_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_XTAL1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_XTAL2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `J_PWR` — a part with NO expected body — so nothing this gate can mask out — sits within 0.5 mm: FID3 (0.09 mm); the two would merge into one component
- `R_AGG_ILIM` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_AGG_OV_BOT` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_AGG_UV_MID` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_AGG_UV_TOP` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_BOOST0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_BOOST1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_CFG0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_CFG1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_CFG2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_CTRL_RESET` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_CMD1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_CMD2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_CMD3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_CMD4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OE1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OE2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OE3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OE4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OK1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OK2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OK3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DATA_OK4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DIS6N` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DIS6P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DIS7N` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_DIS7P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_EXP_RESET` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_GANG` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_HUB_RESET` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_I2C_SCL` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_I2C_SDA` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_ILIM1` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_ILIM2` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_ILIM3` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_ILIM4` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_ILIM_CTRL` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_NONREM0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_NONREM1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_EN1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_EN2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_EN3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_EN4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_RBIAS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_SWAP7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_VBUS_BOT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_VBUS_TOP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_XTAL` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `U_AGG` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)

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

