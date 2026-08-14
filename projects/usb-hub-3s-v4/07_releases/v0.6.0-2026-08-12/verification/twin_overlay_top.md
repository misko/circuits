# Twin render faithfulness — twin_top.png (`--side top`)

board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
a-render_verdict: PASS
- calibration: **7.4174 px/mm** x, **7.4251 px/mm** y, anisotropy **0.9990** (tol 0.02) — orthographic, projection valid
- board edge: 19.950..150.050 x, 19.950..110.050 y mm
- courtyards drawn (F.CrtYd): **95**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 36 measured / 70 refs with an expected body** (34 unresolvable, 0 resolvable but NOT measured, 6 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- pixel measurement: **populated-minus-same-camera-bare RGB delta** (threshold 12)
- expected-model register: `twin_adjudications.yaml` (7 LCSC transform entries)
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (36)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `C22` | C2919856 | 0deg @0.03mm | 0.443 | 0.288 | -0.81,-0.29,-0.02,-0.02 | 3582 | 0.000 |
| `C10` | C342660 | 0deg @0.05mm | 0.294 | 0.128 | -0.48,-0.23,-0.04,-0.03 | 348 | 0.000 |
| `C7` | C342660 | 0deg @0.05mm | 0.291 | 0.108 | -0.49,-0.21,-0.05,-0.01 | 346 | 0.000 |
| `C9` | C342660 | 0deg @0.05mm | 0.283 | 0.034 | -0.48,-0.13,-0.04,-0.08 | 326 | 0.000 |
| `C6` | C342660 | 0deg @0.05mm | 0.282 | 0.040 | -0.49,-0.11,-0.05,-0.05 | 326 | 0.000 |
| `C8` | C342660 | 0deg @0.05mm | 0.279 | 0.067 | -0.49,-0.17,-0.05,+0.03 | 347 | 0.000 |
| `C11` | C342660 | 0deg @0.05mm | 0.278 | 0.088 | -0.48,-0.19,-0.04,+0.01 | 348 | 0.000 |
| `C5` | C77102 | 0deg @0.05mm | 0.275 | 0.051 | -0.47,-0.15,-0.03,-0.09 | 338 | 0.000 |
| `C4` | C77102 | 0deg @0.05mm | 0.264 | 0.091 | -0.47,-0.19,-0.03,+0.00 | 359 | 0.000 |
| `C13` | C39232 | 0deg @0.05mm | 0.263 | 0.020 | -0.47,-0.11,-0.03,-0.05 | 347 | 0.000 |
| `U1` | C7125816 | 0deg @0.23mm | 0.224 | 0.248 | -0.25,-0.03,-0.20,+0.07 | 4472 | 0.017 |
| `C3` | C77102 | 0deg @0.05mm | 0.219 | 0.106 | +0.04,-0.21,+0.34,-0.01 | 342 | 0.000 |
| `C2` | C77102 | 0deg @0.05mm | 0.211 | 0.089 | +0.04,-0.19,+0.34,+0.00 | 342 | 0.000 |
| `C25` | C342660 | 0deg @0.05mm | 0.204 | 0.108 | +0.02,-0.21,+0.32,-0.01 | 333 | 0.000 |
| `U4` | C206199 | 270deg @0.11mm | 0.198 | 0.000 | +0.03,-0.18,-0.03,-0.22 | 637 | 0.008 |
| `C24` | C342660 | 0deg @0.05mm | 0.191 | 0.013 | +0.02,-0.11,+0.32,-0.05 | 317 | 0.000 |
| `C26` | C342660 | 0deg @0.05mm | 0.185 | 0.067 | +0.02,-0.17,+0.32,+0.03 | 336 | 0.000 |
| `J5` | C3020560 | 0deg @0.15mm | 0.166 | 0.036 | -0.39,-0.14,+0.25,-0.16 | 6418 | 0.125 |
| `C18` | C264054 | 0deg @0.03mm | 0.162 | 0.292 | -0.59,-0.29,+0.51,-0.02 | 4063 | 0.000 |
| `U2` | C5219289 | 0deg @0.01mm | 0.142 | 0.068 | +0.04,-0.27,-0.06,-0.02 | 2410 | 0.025 |
| `C23` | C136277 | 0deg @0.03mm | 0.137 | 0.271 | -0.48,-0.27,+0.48,-0.00 | 3936 | 0.000 |
| `C17` | C264054 | 0deg @0.03mm | 0.136 | 0.265 | -0.59,-0.27,+0.51,+0.00 | 4049 | 0.000 |
| `D3` | C7519 | 270deg @0.01mm | 0.125 | 0.173 | -0.16,-0.47,+0.17,+0.22 | 312 | 0.000 |
| `U6` | C206199 | 270deg @0.11mm | 0.118 | 0.000 | +0.03,-0.10,-0.03,-0.14 | 631 | 0.008 |
| `U9` | C2155765 | 0deg @0.00mm | 0.107 | 0.000 | -0.05,-0.04,-0.02,-0.16 | 1318 | 0.000 |
| `D2` | C7519 | 270deg @0.01mm | 0.098 | 0.173 | -0.16,-0.44,+0.17,+0.25 | 312 | 0.000 |
| `D1` | C83846 | 0deg @0.21mm | 0.097 | 0.013 | -0.71,+0.03,+0.63,-0.20 | 1528 | 0.000 |
| `U5` | C206199 | 270deg @0.11mm | 0.091 | 0.000 | +0.03,-0.07,-0.03,-0.11 | 633 | 0.008 |
| `D4` | C7519 | 270deg @0.01mm | 0.085 | 0.173 | -0.16,-0.36,+0.17,+0.19 | 346 | 0.000 |
| `C1` | C88744 | 0deg @0.03mm | 0.084 | 0.146 | -0.15,-0.56,+0.13,+0.39 | 4029 | 0.000 |
| `U3` | C473913 | 270deg @0.10mm | 0.084 | 0.000 | +0.05,-0.02,-0.01,-0.14 | 903 | 0.000 |
| `SW1` | C273394 | 0deg @0.00mm | 0.077 | 0.206 | -0.21,-0.07,+0.06,+0.11 | 4406 | 0.000 |
| `Q1` | C264098 | NONE (best 0.89mm) -> JLC's own transform | 0.071 | 0.059 | +0.10,-0.06,-0.23,+0.01 | 700 | 0.184 |
| `C19` | C264054 | 0deg @0.03mm | 0.063 | 0.185 | -0.59,-0.19,+0.51,+0.08 | 4056 | 0.000 |
| `U7` | C473910 | 270deg @0.01mm | 0.058 | 0.089 | -0.27,+0.03,+0.29,+0.09 | 317 | 0.000 |
| `U8` | C473910 | 270deg @0.01mm | 0.008 | 0.000 | -0.27,+0.04,+0.29,-0.03 | 310 | 0.000 |

## Not measurable by construction (34) — named, never silently passed

- `C12` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C14` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C15` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C16` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C20` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C21` — body 1.00x0.50 mm is under the 2.0 mm resolvability floor (3.7 px, and erosion costs 4 px)
- `C29` — body 1.60x3.20 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `C30` — body 1.60x0.80 mm is under the 2.0 mm resolvability floor (5.9 px, and erosion costs 4 px)
- `D5` — body 3.71x1.60 mm is under the 2.0 mm resolvability floor (11.9 px, and erosion costs 4 px)
- `D6` — body 1.00x1.00 mm is under the 2.0 mm resolvability floor (7.4 px, and erosion costs 4 px)
- `F1` — a part with NO expected body — so nothing this gate can mask out — sits within 0.5 mm: TP1 (0.00 mm); the two would merge into one component
- `R1` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R10` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R11` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R12` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R13` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R14` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R15` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R16` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R17` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R18` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R19` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R2` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R20` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R21` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R22` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R23` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R26` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R3` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R4` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R6` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R7` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R8` — body 0.81x1.62 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)
- `R9` — body 1.62x0.81 mm is under the 2.0 mm resolvability floor (6.0 px, and erosion costs 4 px)

## No JLC model at all (6) — nothing to grade

- `J1` — C3817933: no JLC footprint cached (never fetched)
- `J2` — C5815149: JLC footprint declares no 3D model
- `J3` — C5815149: JLC footprint declares no 3D model
- `J4` — C5815149: JLC footprint declares no 3D model
- `R24` — C861251: no JLC footprint cached (never fetched)
- `R5` — C855851: no JLC footprint cached (never fetched)

## 9 ref(s) flagged by jlc_twin

| ref | status | detail |
|---|---|---|
| `C17` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C18` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C19` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C22` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `C23` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D1` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `D1` | **POLARITY-FIT-BLIND** | no usable polarity marking on JLC's footprint — the numbering-free channel cannot run, so ONLY the human order-preview gate stands between this part and a 180deg reversal |
| `D5` | **POLARITY-CHECK** | 2-pad polarized part: verify the model's polarity marking vs our silk in the render (if the model is unmarked, verify via the JLC order preview) - machine checks cannot see a 180-flipped sym |
| `Q1` | **PAD-MULTIPLICITY** | pad number(s) 5,6,7 appear a different number of times on the two footprints (ours {'5': 2, '6': 2, '7': 2} vs JLC {'5': 1, '6': 1, '7': 1}) — a NAMING convention, not a geometry defect; tho |
| `Q1` | **MOUNT-FALLBACK** | best 0.89mm at 270deg, over 0.5mm — body mounted at JLC's OWN footprint transform (offset 0, their model rot_z), NOT at the failed fit. The render is therefore what JLC's own CAD says, and i |
| `U3` | **PAD-MULTIPLICITY** | pad number(s) 21 appear a different number of times on the two footprints (ours {'21': 2} vs JLC {'21': 1}) — a NAMING convention, not a geometry defect; those numbers are fitted by CENTROID |

## Per-ref crops

- `C17` -> `overlay_C17.png`
- `C18` -> `overlay_C18.png`
- `C19` -> `overlay_C19.png`
- `C22` -> `overlay_C22.png`
- `C23` -> `overlay_C23.png`
- `D1` -> `overlay_D1.png`
- `D5` -> `overlay_D5.png`
- `Q1` -> `overlay_Q1.png`
- `U3` -> `overlay_U3.png`

