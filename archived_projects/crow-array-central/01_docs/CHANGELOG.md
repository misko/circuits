# Changelog — crow-array-central

## v1.0 — 2026-07-18

First orderable release (ORDER GATED — field-test sequence, ORDER_README §1).
Central synchronized recorder for the crow-array commission: one
XU316-1024-TQ128-I24 + two shared-clock PCM1865 ADCs expose six of eight
RJ45 audio ports as an async UAC2 USB-HS device to a Pi 5. Design highlights
and their decisions: 6-layer stackup (ADR-0008/D18 — 4L would not close the
XU316 escape + distributed power + 8 beeper-gate lines); JLC small-via
option 0.30/0.15 for the 0.4mm-pitch TQFP-128 via-in-pad escape
(ADR-0009/D21); power distributed as DRU-floored tracks on the 4 signal
layers, GND = In1+In4 planes + F/In2/In3/B pours + stitch (D15); Q9 AO3401A
reverse-polarity P-FET oriented by the body-diode figure DRAIN=input/
SOURCE=load (ADR-0007/D19); RJ45 5V/GND contact map matches the sealed pod
v1.0 (D28, git 17ceffe) contact-for-contact; power-neck DRU exemptions with
IPC-2152 margin math (D25); functional silk labels (D29); 2 waived
`Zone[GND]<->Zone[GND]` headless-fill micro-slivers (ADR-0010, zero
electrical impact). Board 176.15 x 122.15 mm; cost EXCEEDS the $79-90
target (6L + small-via + XU316 consign, ORDER_README §2). Gates: ERC
severity-all 0; DRC severity-all + refill + parity 0 violations / 0 parity /
exactly 2 waived Zone-Zone unconnected; audit PASS (incl. I11 EP-vias,
I12 mate/keepout); stock coded lines >=5x qty5 except the designated XU316
consign line; jlc_twin exit 0 (zero mirrors, 19 evidence-backed
adjudications); fresh-context pin reviews 4/4 PASS; render review
PASS-WITH-NOTES; policy_audit FULL zero FAIL (15 PASS / 3 WAIVED / 6 HUMAN /
2 N-A). Provenance: git_sha 7f077e1, git_dirty false, KiCad 10.0.4,
promoted route artifact 03_src/route/final.kicad_pcb.
Released: 07_releases/v1.0-2026-07-18
