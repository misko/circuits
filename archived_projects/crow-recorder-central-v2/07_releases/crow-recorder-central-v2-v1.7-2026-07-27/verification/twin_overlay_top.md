# Twin render faithfulness — twin_top.png (`--side top`)

- calibration: **5.6790 px/mm** x, **5.6869 px/mm** y, anisotropy **0.9986** (tol 0.02) — orthographic, projection valid
- board edge: 9.950..180.050 x, 9.950..130.050 y mm
- courtyards drawn (F.CrtYd): **203**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 22 measured / 177 refs with an expected body** (155 unresolvable, 0 resolvable but NOT measured, 8 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (22)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J2` | C3020560 | NONE (best 4.59mm) -> JLC's own transform | 0.543 | 0.025 | -0.02,+0.27,-0.16,+0.80 | 1774 | 3.086 |
| `F6` | C2649901 | 0deg @0.29mm | 0.248 | 0.199 | -0.60,-0.02,+0.19,+0.30 | 420 | 0.000 |
| `F4` | C2649901 | 0deg @0.29mm | 0.226 | 0.199 | -0.57,-0.02,+0.22,+0.30 | 419 | 0.000 |
| `Q1` | C15127 | 180deg @0.28mm | 0.204 | 0.217 | +0.36,-0.22,-0.73,+0.05 | 56 | 0.071 |
| `F2` | C2649901 | 0deg @0.29mm | 0.204 | 0.199 | -0.54,-0.02,+0.24,+0.30 | 427 | 0.000 |
| `F8` | C2649901 | 0deg @0.29mm | 0.202 | 0.199 | -0.62,-0.02,+0.33,+0.30 | 430 | 0.000 |
| `U2` | C181312 | 270deg @0.00mm | 0.192 | 0.145 | -0.42,-0.15,+0.04,+0.14 | 986 | 0.000 |
| `F7` | C2649901 | 0deg @0.29mm | 0.192 | 0.199 | -0.52,-0.02,+0.26,+0.30 | 431 | 0.000 |
| `U5` | C82317 | 270deg @0.06mm | 0.188 | 0.115 | +1.22,-0.12,-1.58,+0.04 | 722 | 0.000 |
| `Q2` | C20917 | 180deg @0.08mm | 0.180 | 0.130 | +0.65,+0.04,-0.97,+0.13 | 28 | 0.021 |
| `F5` | C2649901 | 0deg @0.29mm | 0.174 | 0.199 | -0.49,-0.02,+0.29,+0.30 | 426 | 0.000 |
| `U3` | C181312 | 270deg @0.00mm | 0.160 | 0.145 | -0.39,-0.15,+0.07,+0.14 | 951 | 0.000 |
| `F3` | C2649901 | 0deg @0.29mm | 0.159 | 0.199 | -0.47,-0.02,+0.32,+0.30 | 413 | 0.000 |
| `L1` | C882626 | 0deg @0.05mm | 0.152 | 0.126 | -0.57,+0.01,+0.26,-0.05 | 189 | 0.000 |
| `F1` | C2649901 | 0deg @0.29mm | 0.138 | 0.190 | -0.43,-0.03,+0.35,+0.29 | 412 | 0.000 |
| `U1` | C6938291 | 270deg @0.00mm | 0.136 | 0.000 | -0.38,-0.35,+0.17,+0.18 | 6039 | 0.000 |
| `U10` | C6035451 | 180deg @0.19mm | 0.135 | 0.147 | -0.43,-0.15,+0.16,+0.10 | 281 | 0.045 |
| `D1` | C87074 | 0deg @0.20mm | 0.118 | 0.035 | -0.93,+0.18,+0.70,-0.13 | 284 | 0.000 |
| `L2` | C237284 | 0deg @0.04mm | 0.104 | 0.000 | -0.43,+0.01,+0.22,-0.05 | 179 | 0.000 |
| `Y1` | C2762192 | 0deg @0.05mm | 0.100 | 0.000 | +0.19,+0.24,-0.37,-0.32 | 96 | 0.000 |
| `U9` | C79924 | 180deg @0.20mm | 0.060 | 0.000 | +0.68,+0.17,-0.75,-0.27 | 56 | 0.032 |
| `J1` | C381116 | 0deg @0.00mm | 0.046 | 0.000 | +0.11,+0.06,-0.20,-0.09 | 3471 | 5.686 |

## Not measurable by construction (155) — named, never silently passed

- `CL1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `CL2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_5V1` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_5V2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_5V3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_BEEP` — body 3.20x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `C_VINR` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_avdd2a` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_avdd2b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_avdd3a` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_avdd3b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_b0v9` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_b1v8` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_b3v3` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_bg` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c10` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c11` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c12` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c13` — body 0.50x1.00 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_c9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_d1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_d2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_d3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_d4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_d5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_d6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_dvdd2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_dvdd3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_e1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_e2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_flash` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_iovdd2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_iovdd3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_ldo2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_ldo3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_micb2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_micb3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_pll1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_pll2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_rst` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_sht` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_u18a` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_u18b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_u33a` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_u33b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_u4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_vb` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_vref2a` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_vref2b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `C_vref3a` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `C_vref3b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cc1M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc1P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc2M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc2P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc3M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc3P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc4M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc4P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc5M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc5P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc6M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc6P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc7M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc7P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc8M` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cc8P` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cd1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd3` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd4` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd5` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd6` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cd8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cin_U10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cin_U7` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cin_U8` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cin_U9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cinh_U7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cinh_U8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cout_U10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Cout_U7` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cout_U8` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `Cout_U9` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Couth_U10` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Couth_U7` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Couth_U8` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `D_USB` — body 1.02x2.50 mm is under the 2.0 mm resolvability floor (5.8 px, and erosion costs 4 px)
- `Dp1` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp2` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp3` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp4` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp5` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp6` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp7` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `Dp8` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `FB_BEEP` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `FB_u18` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `FB_u33` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `F_IN` — body 3.20x1.70 mm is under the 2.0 mm resolvability floor (9.7 px, and erosion costs 4 px)
- `L_pll` — body 2.00x1.30 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `RG1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_bck` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_bg1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_bg2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_cc1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_cc2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_cs` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_fb1a` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_fb1b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_fb2a` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_fb2b` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_inj1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_inj2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_lrck` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_mck1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_mck2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_pg` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_rst` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_scl` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_sda` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_vb1` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_vb2` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `R_vbld` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rd` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rf` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs1M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs1P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs2M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs2P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs3M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs3P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs4M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs4P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs5M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs5P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs6M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs6P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs7M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs7P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs8M` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `Rs8P` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (2.8 px, and erosion costs 4 px)
- `U4` — body 2.00x3.31 mm is under the 2.0 mm resolvability floor (11.4 px, and erosion costs 4 px)
- `U6` — body 1.52x1.52 mm is under the 2.0 mm resolvability floor (8.6 px, and erosion costs 4 px)
- `U7` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)
- `U8` — body 1.60x1.60 mm is under the 2.0 mm resolvability floor (9.1 px, and erosion costs 4 px)

## No JLC model at all (8) — nothing to grade

- `J10` — C9900035627: no JLC footprint cached (never fetched)
- `J3` — C9900035627: no JLC footprint cached (never fetched)
- `J4` — C9900035627: no JLC footprint cached (never fetched)
- `J5` — C9900035627: no JLC footprint cached (never fetched)
- `J6` — C9900035627: no JLC footprint cached (never fetched)
- `J7` — C9900035627: no JLC footprint cached (never fetched)
- `J8` — C9900035627: no JLC footprint cached (never fetched)
- `J9` — C9900035627: no JLC footprint cached (never fetched)

## 23 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `D1` | **PAD-GEOM** | pad 1<->2 ours 4.00mm vs JLC 4.40mm (d0.40mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `D1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D1` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `F1` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F2` | **PAD-GEOM** | pad 1<->2 ours 4.27mm vs JLC 3.70mm (d0.57mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F3` | **PAD-GEOM** | pad 1<->2 ours 4.27mm vs JLC 3.70mm (d0.57mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F4` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F5` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F6` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F7` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `F8` | **PAD-GEOM** | pad 1<->2 ours 4.28mm vs JLC 3.70mm (d0.58mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `J1` | **MODEL-SELF** | JLC model bbox center off JLC's OWN pads by (+2.20,-2.87)mm in their frame - model-internal defect; expect the render to need an adjudicated board_dx/board_dy nudge, and distrust bbox MODEL- |
| `J1` | **MODEL-REG** | body center 5.7mm off courtyard, area ratio 0.72 -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=90 (authoritative); body asymmetric (4.3mm bbox-center offset) so this metri |
| `J10` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J2` | **PAD-GEOM** | pad 1<->2 ours 0.80mm vs JLC 8.64mm (d7.84mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `J2` | **PAD-MISMATCH** | best=(4.594738839150707, False, 90) |
| `J2` | **MOUNT-FALLBACK** | best 4.59mm at 90deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and is |
| `J2` | **MODEL-REG** | body center 3.1mm off courtyard, area ratio 0.70, incl. pad_geom_delta=7.84mm -> DO NOT blind-flip: JLC's footprint mounts this model at rot_z=0 (authoritative); body asymmetric (1.1mm bbox- |
| `J3` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J4` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J5` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J6` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J7` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J8` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `J9` | **FETCH-FAILED** | ['[ERROR] Failed to fetch data from EasyEDA API for part C9900035627'] |
| `Q1` | **PAD-GEOM** | pad 1<->3 ours 2.10mm vs JLC 2.49mm (d0.39mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U10` | **PAD-MULTIPLICITY** | pad number(s) 2 appear a different number of times on the two footprints (ours {'2': 1} vs JLC {'2': 2}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID. N |
| `U4` | **PAD-GEOM** | pad 1<->8 ours 2.70mm vs JLC 3.00mm (d0.30mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |
| `U9` | **PAD-GEOM** | pad 1<->5 ours 2.27mm vs JLC 2.60mm (d0.33mm) - land patterns disagree; adjudicate against the part datasheet's recommended pattern |

