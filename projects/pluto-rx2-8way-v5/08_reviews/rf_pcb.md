review_kind: RF_PCB
subject: pluto-rx2-8way-v5 v0.2.0 candidate exact routed RF PCB with J12
date: 2026-08-14
reviewer: Codex exact-artifact RF PCB reviewer
independence: independent-from-design-author
context-given: exact staged board, RF/assembly contracts, impedance record and machine verification
source_commit: 9516a13c47e2dfb18865e3fc0ca402e12c7b1c95
artifact_sha256: e47f366f5faa1991f1eed963dc882b436cc84e02e463e270e7d6f6d995f3f183
board_sha256: e47f366f5faa1991f1eed963dc882b436cc84e02e463e270e7d6f6d995f3f183
rf_contract_sha256: 101112345ca8b3f6e004b793badb92ae4891da3f54a83a6c42ecb8ddcd37d1c1
assembly_contract_sha256: 32010672589d173592fa3466def51be65d145002650f5577d9ec21aa571701ac
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
pad has exactly nine selectively filled/capped 0.45/0.25 mm vias. All 628
ordinary 0.45/0.20 mm vias remain outside that process family.

The J12 increment is confined to the south service/power area. Every one of the
236 earlier route tracks and 57 earlier route vias was preserved to the
nanometre comparison limit before restitching; the promoted route adds only two
0.30-mm `VBUS_RAW` segments from J12.1. The final independent saved-board
checks pass DRC 0/0/0, leave all nine RF paths unchanged, and grade 9 protected
plus 628 ordinary vias. The one fewer ordinary return via is a stitch-site
exclusion caused by the new connector envelope, not an RF-path or fence loss;
all 18/18 route-fence flanks still meet the aperture bound.

The PCB design is SOUND. Ordering remains DO-NOT-ORDER pending JLC's exact
stackup/impedance, selective-via and C429844/C225477 through-hole-service previews and
the physical VNA-qualified first article.
