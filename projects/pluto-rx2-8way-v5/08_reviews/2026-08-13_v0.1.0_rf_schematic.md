review_kind: RF_SCHEMATIC
subject: pluto-rx2-8way-v5 v0.1.0 hardware-only RF schematic
date: 2026-08-13
reviewer: Codex exact-artifact RF schematic reviewer
independence: independent-from-design-author
context-given: exact staged schematic, RF contract, part dossiers and machine verification
source_commit: 798ef9812019efb9e9857332736926d099192a03
artifact_sha256: 4cd8d314261059a73af7dfe5aa6d019c5c4160e75f09144bafd9e29a4d815f7f
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
requirement: RF-SCH-TOPOLOGY PASS
requirement: RF-SCH-PINMAP PASS
requirement: RF-SCH-DC PASS
requirement: RF-SCH-DEFAULT PASS
p0_findings: 0
p1_findings: 0
p2_findings: 0

# Exact staged RF schematic review

The staged schematic implements one receive-only PE42482A-X absorptive SP8T
between common SMA J2 and antenna SMAs J3–J10. The exported netlist and board
agree over 22 nets, 131 connected nodes and 24 no-connects with zero real
discrepancies. ERC has zero error-severity findings.

The exact switch pin map, binary LS-low truth table and `PA0..PA3 -> V1..V4`
mapping agree with the reviewed dossier and RF contract. Passive 10-kohm bias
sets `V4..V1=1000` (ALL_OFF) while U1 VDD is valid and the controller pins are
tri-stated. The 3.3 V switch supply is locally decoupled and referenced to the
same ground domain as the RF return.

The desired selector path remains 100 MHz–5.9 GHz. AD9363 use outside its
official band is explicitly user-accepted and never promoted to an ADI
guarantee. The intended operator ceiling is 0 dBm; +2.5 dBm is only the cited
receiver absolute maximum. Firmware is absent by user directive, so no
autonomous timing behavior is claimed by this hardware review.

The RF schematic is SOUND. Ordering remains DO-NOT-ORDER until the exact JLC
uploader/process preview and physical first-article tests are complete.
