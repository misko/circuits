review_kind: RF_PCB
subject: Pluto RX2 8-Way v5 exact routed RF PCB 4cf5c818
date: 2026-08-13
reviewer: Codex independent exact-artifact RF PCB reviewer
independence: independent-from-design-author
context-given: exact RF contract, manufacturer lands, stackup/solver evidence, board artifact, assembly contract, and authoritative findings ledger
review_stage: exact-final
source_commit: 4cf5c818684e4c39f594b50a567fb086b9cf6f13
artifact_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
assembly_contract_sha256: b85a19f96355d42f2cc2b60d8d00e74551c035e6117c2d25b1f7ff7c37b4b341
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

# Canonical RF PCB verdict

**SOUND / DO-NOT-ORDER.** This canonical record points to the independent
exact-artifact review in
[`2026-08-13_4cf5c818_rf_pcb.md`](2026-08-13_4cf5c818_rf_pcb.md). Its subject
is source commit `4cf5c818` and board SHA-256 `39251c24...017acd`.
P0/P1/P2 findings are **0/0/0**.

## Exact-subject evidence

- The complete predecessor-to-final delta corrects J11's dossier `mates:`
  value to its physical role `plug`, adds the explicit keyed FFSD receptacle
  relationship, and updates status/changelog prose. It changes no schematic,
  RF/assembly rule, board, route or build artifact. Samtec Rev-FX independently
  confirms exposed male terminal-strip posts and `-K` keying for mating with
  FFSD. P-ESC passes 13/13 dossiers.
- Fresh exact-board DRC reports 0 violations, 0 unconnected items and 0
  schematic-parity issues. RF-contract coverage passes. P-PADSEP grades
  12,971 inter-footprint pad pairs and 17,058 paste-to-foreign-copper pairs
  without overlap or intrusion.
- Every RF net is a branch-free, two-ended 0.295-mm F.Cu chain with no RF via.
  Lengths are 14.5039 mm common; 22.4079 mm ANT1/8; 35.0974 mm ANT2/7;
  31.5010 mm ANT3/6; and 36.5926 mm ANT4/5.

## RF requirement summary

- **STACKUP / IMPEDANCE:** saved JLC04161H-7628 structure uses the 0.2104-mm,
  Dk-4.4 top dielectric and solid In1 reference. Retained official-JLC evidence
  gives 49.971863887 ohm for 0.295-mm width and 0.20-mm CPWG gap; the published
  outer-copper cross-check is 49.6433949568 ohm at 0.296 mm.
- **LAUNCHES:** all nine 901-143-6RFX launches match the Rev-C 1.50-mm signal,
  four 1.70-mm ground-hole pattern on the +/-2.54-mm grid and the 11.6-mm
  outward mating-face datum.
- **RETURN:** In1 is a continuous filled GND sheet after each expected SMA
  signal antipad. Four SMA ground posts and U1's perimeter/EP plus protected
  3x3 GND-via field close endpoint returns. Fence grading passes 18/18 flanks;
  worst aperture is 1.3979 mm against the 1.4000-mm limit.
- **COUPLING:** outside the U1 launch region, minimum RF-to-foreign-signal edge
  gap is 1.4433 mm, inter-arm gap 0.6923 mm, RF-to-non-GND-via gap 5.7637 mm,
  RF-to-board-edge 11.4525 mm and RF-to-M3-hole-edge 10.2342 mm.
- **PROCESS:** zero router-created SMD-land vias. Via grading finds exactly
  nine filled/capped 0.45/0.25-mm U1-pad-25 vias and 629 untreated
  0.45/0.20-mm ordinary vias, with no partially protected site.

## Order blockers

- The JLC uploader must echo exact C429844 for all J2-J10 rows as accepted
  wave/manual THT assembly. Refusal stops release and requires a separate
  hand-solder population contract and CPL. Final MANIFEST paperwork must use
  the generated `not_assembled:` line.
- Hard-stop on any mismatch in line-by-line BOM/CPL allocation,
  JLC04161H-7628 stackup/impedance echo, full U1 0.25-mm fill/cap drill-family
  selection, J11 pin-1 orientation, critical D1/J1/U1/SMA previews, or stock
  allocation.
- Exact plotted RF_FAB review and first-article VNA measurement remain open.

The design is sound on the exact reviewed bytes; the open items are order,
fabrication-package and first-article verification gates, not PCB design
findings.
