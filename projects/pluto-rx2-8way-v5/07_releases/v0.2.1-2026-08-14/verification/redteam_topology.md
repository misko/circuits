review_kind: redteam_topology
subject: pluto-rx2-8way-v5 v0.2.1-2026-08-14 hardware topology review
date: 2026-08-14
reviewer: Codex adversarial topology, protection and ratings lens
context-given: exact hardware artifacts and retained primary authorities
source_commit: 57687a87c09dd1aac6cec52fb68c34286b0dab36
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Adversarial hardware topology review

The exact schematic implements one receive-only absorptive PE42482A-X
common-to-one-of-eight topology. Passive V4..V1=`1000` selects ALL_OFF while
3V3 is valid and the controller is high impedance. The desired 100 MHz--5.9
GHz selector path and AD9363-as-AD9361 risk remain explicitly user accepted,
not an ADI guarantee. RF centres are 0 VDC-only because no series DC blocks
are fitted.

USB-C J1 and bench header J12 are non-isolated alternative 4.75--5.5 V inputs
used one at a time. Both feed `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`.
CC1/CC2 have independent 5.1-kohm pulls and ESD protection; USB data remains
absent. Electrical invariants pass 34/34, component parity passes 30/30, ERC
has zero error-severity findings and final PCB DRC is 0/0/0.

The routing and model-registration changes alter neither connectivity nor the
reset default. P0/P1/P2 findings are 0/0/0 and the design is **SOUND**.
Firmware is absent and no dwell behavior is claimed. Uploader/process and
first-article electrical/RF tests remain external stop gates.
