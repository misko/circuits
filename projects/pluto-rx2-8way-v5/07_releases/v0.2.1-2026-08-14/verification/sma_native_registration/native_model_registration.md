# Native model physical registration — `native_top.png`

board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
a-render_verdict: PASS
registration_kind: P-MODEL-REG
render_source: exact project board with provenance-bound native models
model_sha256: 17cbdea22e6ca94e56fb0facf4c7642df6b57fb94bc9835af2bbe51b7e712aba
calibration_px_per_mm: 34.2619 x, 34.2550 y
anisotropy: 1.0002
fit_tolerance_mm: 1.000
courtyard_containment_tolerance_mm: 0.250
overlay: native_top_registration_overlay.png

Orange is F.CrtYd; green is the independent F.Fab body envelope; pink is the populated-minus-bare native-model pixel envelope; cyan is the drilled attachment field. Pink/green agreement alone is not enough: both must also register to the footprint and courtyard.

| ref | centre delta mm | measured beyond F.Fab mm | measured beyond courtyard mm | drilled centres inside | min pad margin mm |
|---|---:|---:|---:|---:|---:|
| J2 | 0.214 | 0.029 | 0.000 | 5/5 | 0.611 |
| J3 | 0.216 | 0.029 | 0.000 | 5/5 | 0.596 |
| J4 | 0.217 | 0.029 | 0.000 | 5/5 | 0.593 |
| J5 | 0.231 | 0.029 | 0.000 | 5/5 | 0.579 |
| J6 | 0.230 | 0.029 | 0.000 | 5/5 | 0.579 |
| J7 | 0.201 | 0.000 | 0.000 | 5/5 | 0.608 |
| J8 | 0.201 | 0.000 | 0.000 | 5/5 | 0.608 |
| J9 | 0.217 | 0.029 | 0.000 | 5/5 | 0.593 |
| J10 | 0.214 | 0.029 | 0.000 | 5/5 | 0.611 |

## Failures

- none
