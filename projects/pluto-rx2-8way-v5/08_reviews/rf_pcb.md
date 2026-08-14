review_kind: RF_PCB
subject: pluto-rx2-8way-v5 v0.2.1 candidate exact routed RF PCB with J12
date: 2026-08-14
reviewer: Codex exact-artifact RF PCB reviewer
independence: independent-from-design-author
context-given: exact staged board, RF/assembly contracts, impedance record and machine verification
source_commit: 9516a13c47e2dfb18865e3fc0ca402e12c7b1c95
artifact_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
rf_contract_sha256: 625acbc4c6f40b1a521c011399c0617fa5ec02817a3bccac31f2b149918b00bb
assembly_contract_sha256: 32010672589d173592fa3466def51be65d145002650f5577d9ec21aa571701ac
evidence_sha256: rf_realized_bundle 2893a81003f5c90ea962d9ce627c2170896652ce7cf58ff2666c48571c859cc8
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
and outward mating datum. The independent native-model registration gate
passes all 9 model instances and all 45 drilled attachment centres; the model
body agrees with F.Fab and remains inside F.CrtYd. Route-following return
fencing passes 18/18 flanks; the worst aperture is 1.3979 mm against the
1.4000 mm maximum.

The U1 ground pad has exactly nine selectively filled/capped 0.45/0.25 mm
vias. The other 615 ordinary 0.45/0.20 mm vias are outside that process family.
The J12 increment remains confined to the south service/power area on
`VBUS_RAW` and GND. The final saved-board checks grade all nine branch-free RF
paths, preserve zero RF vias, pass all 18 route-fence flanks, and report DRC,
unconnected items and schematic parity at 0/0/0.

The PCB design is SOUND. Ordering remains DO-NOT-ORDER pending JLC's exact
stackup/impedance, selective-via and C429844/C225477 through-hole-service previews and
the physical VNA-qualified first article.
