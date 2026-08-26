subject: pluto-rx2-8way-v4 v1.1 exact layout/RF artifact
date: 2026-08-01
reviewer: redteam-agent (GPT-5 layout/thermal/power-integrity lens)
context-given: full-tree
independence: independent-from-design-author
review_kind: redteam_layout
source_commit: bc1fb1003cd9b7f06c70b15d973c5c018d0ff458
board_sha256: 72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7
design_verdict: SOUND
order_verdict: ORDER

# Fresh adversarial layout / RF / physical review

No open P0 or P1 layout, RF-return, thermal, power-integrity, mechanical, or
manufacturability defect was found in the exact board.

| Subject | Independent measured result |
|---|---|
| KiCad gate | 0 violations / 0 unconnected / 0 schematic parity |
| Resistor/module separation | 0.220 mm copper and 0.730 mm courtyard gap; 0 overlaps; 0 paste intrusions; 0.090 mm fabrication floor |
| RF copper | eight arms on F.Cu, 0.360 mm wide, no arm vias; routed spread 0.1657 mm <= 1.0 mm |
| Return plane | In1.Cu has no tracks and carries the continuous GND zone; the SW_V4/ANT4 control crossing is on In2.Cu |
| Fence | 22/22 arm sides; worst interior aperture 1.1769 mm <= 1.1910 mm |
| Field solve | 52.0877 ohm, epsilon-effective 3.173354, converged residual below 2e-9; inside 45..55 ohm acceptance |
| Placement/render | all 27 CPL bodies present; 11/11 resolvable bodies independently pixel-checked within 1.00 mm |
| Fabrication | four distinct copper layers, one realized pour on each; drill/edge/mask/paste outputs present |

The five repaired resistors are deliberately connected to their module pads by
explicit routed copper; the positive gap means the parts do not borrow or
overlap the RP2040-Zero land pattern. The module underside keepout remains
clear. Local switch decoupling and filtered bulk capacitance remain on the
correct rail side, and no new neckdown or heat-concentration defect was found.

Sourcing is CLEAR for all 11 placed BOM lines, so the prototype-order verdict
is ORDER. Selecting controlled impedance, filled/capped POFV and plug-in SMA
assembly, plus checking the uploader preview, are order-execution controls.
X-ray/TDR/VNA/module/thermal tests are required before production or service
use; they are post-order first-article acceptance, not circular pre-order
requirements.

Severity summary: P0 0; P1 design defects 0; P1 execution/first-article
controls 2; neither contradicts the SOUND design or ORDER verdict.

