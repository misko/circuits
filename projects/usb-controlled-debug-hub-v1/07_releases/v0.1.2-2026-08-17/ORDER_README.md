# USB-controlled debug hub v0.1.2 — DESIGN RELEASE / DO NOT ORDER

DESIGN: **PASS** for this exact first-article candidate. Independent topology,
pin, layout, render and release-package reviews are retained in `verification/`.

ORDER VERDICT: **DO NOT ORDER** until the JLC order-time stackup, impedance,
via-process, BOM, rotation, polarity and THT previews below are accepted.

SOURCING: **CLEAR 33/33** on 2026-08-17 for five boards; repeat actual JLC
assembly allocation immediately before payment.

POSTURE: first article only, quantity 5 maximum; production remains HOLD.

FIRMWARE: none generated and none included. Do not upload or request firmware.

Exact PCB SHA-256:
`c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`.

Exact connector-orientation subject:
`8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97`.
Machine geometry passes 5/5 and the user/product owner approved the hash-bound
views on 2026-08-17 (`verification/orientation_approval.md`).

Upload `fab/usb_controlled_debug_hub_gerbers.zip` for PCB fabrication, then
upload `fab/bom.csv` and `fab/cpl.csv` separately for assembly.

STACKUP HOLD: select four-layer JLC04161H-7628, nominal 1.6 mm, outer copper
35 µm, inner copper 15.2 µm, 0.2104 mm 7628 prepregs, 1.065 mm core and
ENIG. Select controlled impedance and obtain JLC's final 90-ohm differential
solve/coupon for the provisional 0.2332 mm trace / 0.15 mm gap / 0.30 mm
clearance geometry. Any different solve is STOP and requires source review.

VIA HOLD: selectively paste-fill and copper-cap the complete 0.46/0.20 mm via
family only. Do not fill/cap the ordinary 0.70/0.35 mm family. Preserve the
uploader/manufacturer acknowledgement before payment.

ASSEMBLY HOLD: double-sided SMT must preview as 129 top + 9 bottom placements.
Purchase THT/wave-selective assembly for J_PWR, J_UP and J_PORT1–J_PORT4.
F_IN is intentionally absent from BOM/CPL; manually install exact Keystone
3568 plus Littelfuse 0297004.WXNV after PCBA.

Before payment, preserve and review JLC's resolved BOM echo, every rotation and
polarity preview, all six THT mappings, the selective-via acknowledgement,
final stackup/impedance result and fresh actual assembly allocation. Any
redirect, substitution, DNP, side, rotation, polarity or placement mismatch is
a STOP condition.

First power remains HOLD until the release-bound first-article checklist is
AUTHORIZED with population, exposed-pad, resistance and current-limit evidence.
Production remains held pending USB 2.0 Hi-Speed traffic/eye testing,
simultaneous four-port load/drop measurements, transient and thermal tests,
and connector-lot qualification.
