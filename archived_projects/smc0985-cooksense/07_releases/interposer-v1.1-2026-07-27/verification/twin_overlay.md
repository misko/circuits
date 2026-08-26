# Twin render faithfulness — twin_top.png (`--side top`)

- calibration: **17.8189 px/mm** x, **17.8308 px/mm** y, anisotropy **0.9993** (tol 0.02) — orthographic, projection valid
- board edge: 9.950..64.050 x, 9.950..56.050 y mm
- courtyards drawn (F.CrtYd): **27**; footprints with no courtyard on EITHER layer: 0
- **COVERAGE: 1 measured / 1 refs with an expected body** (0 unresolvable, 0 resolvable but NOT measured, 0 with no JLC model at all)
- tolerance: **1.00 mm** on both the centre delta and the outward excursion
- overlay: `twin_top_courtyard_overlay.png`

**Red** = footprint courtyard (what gets fabricated). **Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body (mesh x JLC's own model transform x board placement). **Magenta** = MEASURED body (pixels). **Blue** = board edge.

A body outside its red box with green and magenta AGREEING is a **3D-model** defect with no board exposure — gerbers and CPL derive from pads, never from the model. Green and magenta DISAGREEING is a **render** defect: the picture is not the board, and any visual review done on it is void.

## Graded refs (1)

| ref | LCSC | fit | centre delta mm | outward mm | edge deltas L,T,R,B mm | body px | courtyard excursion mm |
|---|---|---|---|---|---|---|---|
| `J_KEY_MATRIX` | C2683602 | 0deg @0.01mm | 0.165 | 0.049 | -0.38,-0.06,+0.05,+0.12 | 19015 | 0.084 |

