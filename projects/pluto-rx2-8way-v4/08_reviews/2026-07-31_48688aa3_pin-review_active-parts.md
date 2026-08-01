subject: pluto-rx2-8way-v4 48688aa3
date: 2026-07-31
reviewer: pin-review
context-given: zero-context
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER

U_MCU

VERDICT: QUESTION

`U_MCU pin 1 (GP0): expected vendor P1 pin 1 at the top-right, with numbering proceeding clockwise down the right edge, across the bottom, then up the left edge vs dossier pad 1 at (+8.70,-10.16) and computed CW winding — MATCH. Evidence: RP2040-Zero-details-7.jpg plus RP2040_Zero.pdf connector P1.`

`U_MCU pin 1–23 (P1 castellated interface): expected 23 vendor-numbered castellated contacts, physically 9 on the right edge, 5 interior bottom contacts, and 9 on the left edge, with no exposed pad vs dossier pads 1–23 in the corresponding geometry and no EP — MATCH. The separate P2/P3 underside contacts GP17–GP25 plus GND are not part of vendor connector P1 and are explicitly non-castellated in the source artifact.`

`U_MCU pin 1–4 (GP0–GP3): expected GPIO/control nets vs dossier SEL_V1, SEL_V2, SEL_V3, SEL_V4 — MATCH in net kind and one-to-one lane symmetry.`

`U_MCU pin 5 (GP4): expected GPIO/load-control net vs dossier LED_STAT — MATCH.`

`U_MCU pin 6–20 (GP5–GP15, GP26–GP29): expected GPIOs that may be unused vs dossier explicit unconnected nets — MATCH.`

`U_MCU pin 21 (3V3): expected the onboard RT9013 3.3 V rail/output, optionally externally driven only under the vendor/source constraints, vs dossier 3V3_MOD — rail kind MATCH; direction cannot be established from the dossier alone.`

`U_MCU pin 22 (GND): expected ground vs dossier GND — MATCH.`

`U_MCU pin 23 (5V/VSYS): expected USB-VBUS/onboard-regulator input node at the top-left vs dossier explicit unconnected net — electrically allowable if USB or legal 3V3 back-powering is the intended supply method, but that powering intent is absent from the permitted evidence.`

`U_MCU pin 1–23 (all functions): expected the dossier to carry the source part functions for the required function↔net comparison vs dossier header “MPN unknown” and every function cell “(not in yaml)”; manual comparison against the allowed vendor artifacts/source part file supports the mapping, but the audit dossier’s provenance is incomplete.`

Only one U_MCU instance is present, so multi-instance symmetry is not applicable.

U_SW

VERDICT: QUESTION

`U_SW pin 1 (LS): expected pin 1 at the top-left and CCW top-view winding—1–6 down the left, 7–12 left-to-right along the bottom, 13–18 up the right, 19–24 right-to-left along the top—vs dossier pad 1 at (-1.90,-1.25), six pads per side, computed CCW — MATCH. Evidence: DOC-75785-4 p20, Figure 22 and Table 8.`

`U_SW pin 1 (LS): expected ground for logic-low selection and improved RF grounding vs dossier GND — MATCH. Evidence: DOC-75785-4 p9 note 1 and p10 Table 5 note 1.`

`U_SW pin 1–24 plus 25 (EP): expected 24 perimeter leads plus one exposed ground pad vs dossier pads 1–24 plus pad 25 EP — MATCH.`

`U_SW pin 3,5,7,14,16,18,21,23 (GND): expected ground vs dossier GND on every pin — MATCH.`

`U_SW pin 25 (EP): expected ground for proper operation vs dossier GND — MATCH. Evidence: DOC-75785-4 p20, Table 8.`

`U_SW pin 8 (VDD): expected a 2.3–5.5 V supply, nominally 3.3 V, vs dossier 3V3 — MATCH. Evidence: DOC-75785-4 p3, Table 2.`

`U_SW pin 9–12 (V1–V4): expected four digital control-input nets vs dossier SW_V1, SW_V2, SW_V3, SW_V4 — MATCH in net kind and lane symmetry.`

`U_SW pin 20 (NC): expected open or GND vs dossier GND — MATCH. Evidence: DOC-75785-4 p20, Table 8 note 2.`

`U_SW pin 2,4,6,13,15,17,24 (RF2,RF3,RF4,RF5,RF6,RF7,RF1): expected RF-port nets held at 0 VDC vs dossier ANT2, ANT3, ANT4, ANT5, ANT6, ANT7, ANT1 — RF net kind MATCH, but the dossiers cannot establish the mandatory 0 VDC condition. Evidence: DOC-75785-4 p20, Table 8 note 1.`

`U_SW pin 19 (RF8): expected an RF8 port at 0 VDC and structural correspondence with RF1–RF7 vs dossier RX1_TAP rather than ANT8 — electrically plausible RF net, but the intentional asymmetry and 0 VDC condition require design context.`

`U_SW pin 22 (RFC): expected the common RF port at 0 VDC vs dossier RX2_OUT — RF net kind MATCH, but the mandatory 0 VDC condition is not established by the allowed evidence.`

Only one U_SW instance is present, so multi-instance symmetry is not applicable.

Combined verdict: QUESTION — no winding, pin-count, exposed-pad, ground, or supply-pin mismatch was found. Release questions are U_MCU dossier traceability/power-source intent and U_SW RF-port DC bias plus the RF8→RX1_TAP asymmetry. No files were edited.
