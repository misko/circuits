# USB-controlled debug hub v0.1.3 — QUICK SOURCING SUPERSEDE / ORDER CANDIDATE

DESIGN: **PASS** for this exact first-article candidate. Independent topology,
pin, layout, render and release-package reviews are retained in `verification/`.

ORDER VERDICT: **ORDER CANDIDATE**. It may enter JLC's uploader; do not pay
until the order-time stackup, impedance, via-process, BOM, rotation, polarity
and THT previews below are accepted.

SOURCING: **PROVISIONAL 33/33**. This release changes supplier identity only
to replace ten zero-availability BOM lines from v0.1.2. Repeat live JLC
assembly allocation and inspect the resolved BOM before payment.

POSTURE: first article only, quantity 5 maximum; production remains HOLD.

FIRMWARE: none generated and none included. Do not upload or request firmware.

Exact PCB SHA-256:
`c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`.

This is a source-owned sourcing supersede of `v0.1.2-2026-08-17`. The PCB,
Gerbers/drills and placement coordinates must remain identical under the
machine supersede gate. The intended substitutions are:

| Old LCSC / MPN | New LCSC / MPN |
|---|---|
| C60491 / RC0402FR-07100KL | C481918 / CRCW0402100KFKED |
| C1525 / CL05B104KO5NNNC | C392963 / TCC0402X7R104K160AT |
| C60490 / RC0402FR-0710KL | C843837 / CRCW040210K0FKEE |
| C327368 / RC0402FR-07165KL | C2483395 / RMCF0402FT165K |
| C52923 / CL05A105KA5NQNC | C326568 / CC0402KRX5R8BB105 |
| C342660 / C3225X7R1C226KT000N | C55530 / CL32B226KOJNNNE |
| C77036 / GRM1885C1H332JA01D | C342849 / C1608C0G1H332JT000N |
| C105871 / RC0402FR-074K7L | C482193 / CRCW04024K70FKED |
| C6053 / 74LVC08APW,118 | C54411084 / 74LVC08APW |
| C130056 / TPS2557DRBR | C2150199 / TPS2557QDRBRQ1 |

ROTATION HOLD: exact-code measurements resolve C2150199 at 0 degrees and
C54411084 at +270 degrees. Both are single-channel measurements, so JLC's
pin-1 preview must be checked for all five TPS2557 placements and both
74LVC08 placements. The normal single-channel preview list still applies.
Use `verification/rotation_human_gate_v013.txt` and
`verification/bom_echo_gate_v013.txt` as the v0.1.3 operator worklists; the
same-named files under `fab/` are retained byte-identical solely because the
sourcing-supersede contract allows only `fab/bom.csv` to change.

CATALOG-CAD NOTE: JLC/EasyEDA exact-code CAD resolved for eight replacement
codes. Its API did not return CAD for C843837 and C2483395 during this run;
both are ordinary non-polarized 0402 resistors with source-locked footprint
and value, but their live JLC resolved-package rows must therefore be checked
explicitly in the uploader. Any package other than 0402/1005 metric is STOP.

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
