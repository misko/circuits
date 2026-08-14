review_kind: RF_SCHEMATIC
subject: pluto-rx2-8way-v5 v0.2.0 candidate hardware-only RF schematic with J12
date: 2026-08-14
reviewer: Codex exact-artifact RF schematic reviewer
independence: independent-from-design-author
context-given: exact staged schematic, RF contract, part dossiers and machine verification
source_commit: 9516a13c47e2dfb18865e3fc0ca402e12c7b1c95
artifact_sha256: 9f373e13e6eb008e96d0d90521d585e8e2f17e17d0aa3561ab36ec3c03b32b45
board_sha256: e47f366f5faa1991f1eed963dc882b436cc84e02e463e270e7d6f6d995f3f183
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
agree over 22 nets, 133 connected nodes and 24 no-connects with zero real
discrepancies. ERC has zero error-severity findings.

The exact switch pin map, binary LS-low truth table and `PA0..PA3 -> V1..V4`
mapping agree with the reviewed dossier and RF contract. Passive 10-kohm bias
sets `V4..V1=1000` (ALL_OFF) while U1 VDD is valid and the controller pins are
tri-stated. The 3.3 V switch supply is locally decoupled and referenced to the
same ground domain as the RF return.

J12 adds only an alternate 5 V/GND bench input on the existing `VBUS_RAW` and
GND nets, upstream of the common fuse/clamp/regulator chain. It neither touches
an RF net nor changes the switch bias/default state. J1 and J12 are explicitly
non-isolated and used one at a time; that operating restriction is a power-
interface obligation rather than an RF-path change.

The desired selector path remains 100 MHz–5.9 GHz. AD9363 use outside its
official band is explicitly user-accepted and never promoted to an ADI
guarantee. The intended operator ceiling is 0 dBm; +2.5 dBm is only the cited
receiver absolute maximum. Firmware is absent by user directive, so no
autonomous timing behavior is claimed by this hardware review.

The RF schematic is SOUND. Ordering remains DO-NOT-ORDER until the exact JLC
uploader/process preview and physical first-article tests are complete.
