review_kind: RF_PCB
subject: pluto-rx2-8way-v5 v0.1.0 exact routed RF PCB
date: 2026-08-13
reviewer: Codex exact-artifact RF PCB reviewer
independence: independent-from-design-author
context-given: exact staged board, RF/assembly contracts, impedance record and machine verification
source_commit: 798ef9812019efb9e9857332736926d099192a03
artifact_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
rf_contract_sha256: 101112345ca8b3f6e004b793badb92ae4891da3f54a83a6c42ecb8ddcd37d1c1
assembly_contract_sha256: 993fa63cfbb85f64d1b573a4131d880630a16278226558e597f357f294ce0c4d
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
requirement: RF-PCB-STACKUP PASS
requirement: RF-PCB-IMPEDANCE PASS
requirement: RF-PCB-LAUNCHES PASS
requirement: RF-PCB-RETURN PASS
requirement: RF-PCB-COUPLING PASS
p0_findings: 0
p1_findings: 0
p2_findings: 0

# Exact staged RF PCB review

The exact 90 x 65 mm four-layer board passes KiCad DRC with zero violations,
zero unconnected items and zero schematic-parity findings. All nine RF nets
are branch-free 0.295 mm F.Cu paths with no RF vias or intentional stubs over
a continuous In1.Cu reference plane.

The locked JLC04161H-7628 cross-section uses a 0.2104 mm F.Cu-to-In1 spacing,
0.295 mm finished width and 0.200 mm coplanar gap. The retained official JLC
calculator result is 49.971863887 ohms. The live-versus-published solder-mask
input difference remains an explicit order-time echo requirement rather than
being hidden as tolerance.

All nine 901-143-6RFX launches retain the manufacturer Rev-C five-hole pattern
and outward mating datum. Route-following return fencing passes 18/18 flanks;
the worst aperture is 1.3979 mm against the 1.4000 mm maximum. The U1 ground
pad has exactly nine selectively filled/capped 0.45/0.25 mm vias. All 629
ordinary 0.45/0.20 mm vias remain outside that process family.

The PCB design is SOUND. Ordering remains DO-NOT-ORDER pending JLC's exact
stackup/impedance, selective-via and C429844 through-hole-service previews and
the physical VNA-qualified first article.
