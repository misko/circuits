# Twin render faithfulness — twin_top.png (`--side top`)

board_sha256: b1c042c695af896b18627c596406157bc5522561c31ac60cc353b11ff065d197
a-render_verdict: PASS
- calibration: **7.4174 px/mm** x, **7.4226 px/mm** y, anisotropy **0.9993** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..150.050 x, 19.950..120.050 y mm
- courtyards drawn (F.CrtYd): **163**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 35 measured / 156 refs with an expected body** (121 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (3 LCSC transform entries)
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (35)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J_PORT1` | C503996 | 0deg @0.00mm | 0.236 | 0.000 | -0.09,+0.57,-0.07,-0.13 | 9219 | 0.370 |
| `J_PORT2` | C503996 | 0deg @0.00mm | 0.225 | 0.000 | -0.04,+0.57,-0.03,-0.13 | 9218 | 0.370 |
| `J_PORT4` | C503996 | 0deg @0.00mm | 0.223 | 0.000 | +0.04,+0.57,-0.08,-0.13 | 9285 | 0.370 |
| `J_PORT3` | C503996 | 0deg @0.00mm | 0.222 | 0.000 | -0.00,+0.57,+0.01,-0.13 | 9215 | 0.370 |
| `L_MAIN` | C15269 | 0deg @0.10mm | 0.180 | 0.102 | +0.02,-0.10,-0.22,-0.19 | 584 | 0.000 |
| `L_PD` | C17700166 | NONE (best 0.52mm) -> JLC's own transform | 0.176 | 0.087 | -0.08,-0.09,-0.12,-0.20 | 3414 | 0.004 |
| `U_PD_BUCK` | C841386 | 0deg @0.00mm | 0.170 | 0.000 | +0.00,-0.05,-0.19,-0.24 | 323 | 0.040 |
| `U_PWR_CTRL` | C130056 | 270deg @0.05mm | 0.157 | 0.028 | -0.08,-0.03,-0.14,-0.20 | 306 | 0.000 |
| `J_DATA` | C165948 | 0deg @0.00mm | 0.148 | 0.000 | +0.00,-0.06,-0.12,-0.21 | 3193 | 0.560 |
| `C_PD_OUT3` | C21397 | 0deg @0.05mm | 0.145 | 0.000 | -0.04,-0.07,-0.11,-0.17 | 299 | 0.000 |
| `C_PD_OUT2` | C21397 | 0deg @0.05mm | 0.139 | 0.000 | -0.03,-0.07,-0.10,-0.17 | 299 | 0.000 |
| `C_PD_OUT1` | C21397 | 0deg @0.05mm | 0.133 | 0.000 | -0.02,-0.07,-0.09,-0.17 | 299 | 0.000 |
| `C_PORT1_BULK` | C21397 | 0deg @0.04mm | 0.130 | 0.000 | -0.05,-0.04,-0.15,-0.12 | 299 | 0.000 |
| `J_POWER` | C165948 | 0deg @0.00mm | 0.122 | 0.000 | +0.00,+0.04,-0.12,-0.25 | 3162 | 0.560 |
| `U_AND_PWR` | C6053 | 270deg @0.06mm | 0.118 | 0.095 | +0.79,-0.09,-0.91,-0.11 | 914 | 0.000 |
| `Y_HUB` | C1985204 | 0deg @0.05mm | 0.118 | 0.000 | +0.05,-0.08,-0.04,-0.15 | 272 | 0.000 |
| `U_PD` | C970725 | 0deg @0.00mm | 0.108 | 0.014 | +1.09,-0.01,-1.13,-0.20 | 795 | 0.000 |
| `U_AND_DATA` | C6053 | 270deg @0.06mm | 0.104 | 0.095 | +0.83,-0.09,-0.86,-0.11 | 952 | 0.000 |
| `C_TRUNK_BULK` | C21397 | 0deg @0.05mm | 0.102 | 0.000 | -0.03,+0.00,+0.01,-0.21 | 292 | 0.000 |
| `U_AGG` | C2878936 | 0deg @0.04mm | 0.101 | 0.000 | +0.06,+0.02,-0.06,-0.23 | 631 | 0.031 |
| `C_PORT2_BULK` | C21397 | 0deg @0.05mm | 0.100 | 0.000 | -0.01,-0.04,-0.11,-0.12 | 300 | 0.000 |
| `Q_DATA1` | C85047 | 180deg @0.20mm | 0.097 | 0.000 | +0.68,+0.01,-0.75,-0.19 | 83 | 0.090 |
| `C_BUCK_OUT2` | C21397 | 0deg @0.05mm | 0.096 | 0.000 | +0.05,-0.06,-0.05,-0.13 | 295 | 0.000 |
| `Q_DATA2` | C85047 | 180deg @0.20mm | 0.094 | 0.000 | +0.62,+0.01,-0.67,-0.19 | 102 | 0.090 |
| `Q_DATA3` | C85047 | 180deg @0.20mm | 0.092 | 0.000 | +0.70,+0.01,-0.73,-0.19 | 84 | 0.090 |
| `U_CTRL` | C640876 | 270deg @0.15mm | 0.091 | 0.016 | +0.99,-0.02,-1.10,-0.13 | 1442 | 0.000 |
| `Q_DATA4` | C85047 | 180deg @0.20mm | 0.090 | 0.000 | +0.71,+0.01,-0.72,-0.19 | 84 | 0.090 |
| `U_EXP` | C558584 | 270deg @0.04mm | 0.086 | 0.024 | +1.29,-0.02,-1.39,-0.12 | 2499 | 0.001 |
| `C_PORT4_BULK` | C21397 | 0deg @0.05mm | 0.082 | 0.000 | +0.07,-0.04,-0.03,-0.12 | 299 | 0.000 |
| `C_PORT3_BULK` | C21397 | 0deg @0.05mm | 0.081 | 0.000 | +0.03,-0.04,-0.07,-0.12 | 296 | 0.000 |
| `C_BUCK_OUT1` | C21397 | 0deg @0.05mm | 0.081 | 0.000 | +0.05,-0.04,-0.05,-0.12 | 299 | 0.000 |
| `U_BUCK` | C5248536 | 270deg @0.06mm | 0.081 | 0.000 | +0.66,+0.02,-0.66,-0.18 | 136 | 0.000 |
| `R_PD_VDD` | C52444 | 0deg @0.02mm | 0.077 | 0.028 | +0.03,-0.05,-0.07,-0.09 | 302 | 0.000 |
| `C_TRUNK_USB` | C136277 | 0deg @0.03mm | 0.071 | 0.003 | +0.58,-0.00,-0.61,-0.14 | 1821 | 0.000 |
| `U_HUB` | C478081 | 0deg @0.04mm | 0.056 | 0.000 | +0.07,+0.00,-0.03,-0.11 | 3951 | 0.000 |

## Not measurable by construction (121) — named, never silently passed

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
- `C_PD_BOOT` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PD_FF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PD_IN1` — body 1.60x3.20 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C_PD_IN2` — body 1.60x3.20 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C_PD_IN_DVDT` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C_PD_IN_HF` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `C_PD_VDD` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT1_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT2_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT3_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PORT4_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR1_IN` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR2_IN` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR3_IN` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR4_IN` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR_CTRL_IN` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR_CTRL_OUT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_PWR_CTRL_OUT_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_TRUNK_HF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_XTAL1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C_XTAL2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `D_PD_TVS` — body 2.00x2.02 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `F_PD` — body 3.20x1.70 mm is under the 2.0 mm resolvability floor (12.6 px, and erosion costs 4 px)
- `R_AGG_ILIM` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_BOOST0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_BOOST1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_CC1` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_CC2` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
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
- `R_ILIM1` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_ILIM2` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_ILIM3` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_ILIM4` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_ILIM_CTRL` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_NONREM0` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_NONREM1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_FB_A` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_FB_B` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_FB_BOT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_FF` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_IN_ILIM` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_PD_IN_OV_BOT` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_PD_IN_UV_MID` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_PD_IN_UV_TOP` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R_PD_UV_BOT` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_UV_TOP` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PD_VBUS` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_CMD4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_PWR_EN1` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
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
- `R_VBUS_BOT` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_VBUS_TOP` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `R_XTAL` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `U_PD_IN` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U_PWR1` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U_PWR2` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U_PWR3` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)
- `U_PWR4` — body 2.01x2.00 mm is under the 2.0 mm resolvability floor (14.8 px, and erosion costs 4 px)

## 4 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `L_PD` | **MOUNT-FALLBACK** | best 0.52mm at 0deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is  |
| `U_AGG` | **PAD-MULTIPLICITY** | pad number(s) 25,26 appear a different number of times on the two footprints (ours {'25': 7, '26': 4} vs JLC {'25': 1, '26': 1}) — a NAMING convention, not a geometry defect; those numbers a |
| `U_HUB` | **PAD-MULTIPLICITY** | pad number(s) 65 appear a different number of times on the two footprints (ours {'65': 18} vs JLC {'65': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROI |
| `U_PWR_CTRL` | **PAD-MULTIPLICITY** | pad number(s) 9 appear a different number of times on the two footprints (ours {'9': 8} vs JLC {'9': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |

## Per-ref crops

- `L_PD` -> `overlay_L_PD.png`
- `U_AGG` -> `overlay_U_AGG.png`
- `U_HUB` -> `overlay_U_HUB.png`
- `U_PWR_CTRL` -> `overlay_U_PWR_CTRL.png`

