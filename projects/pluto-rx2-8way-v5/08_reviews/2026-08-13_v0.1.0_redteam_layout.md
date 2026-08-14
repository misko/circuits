review_kind: redteam_layout
subject: Pluto RX2 8-Way v5 v0.1.0 staged hardware release
date: 2026-08-13
reviewer: Codex independent layout, power-integrity, thermal and manufacturability reviewer
independence: fresh exact-artifact review; no design-author verdict inherited
evidence_scope: staged hardware release v0.1.0-2026-08-13 only
source_commit: 798ef9812019efb9e9857332736926d099192a03
release: projects/pluto-rx2-8way-v5/07_releases/v0.1.0-2026-08-13
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-artifact layout review

## Verdict

The exact staged board is **SOUND** for a local prototype-fabrication handoff.
I found no P0, P1 or P2 layout, connectivity, RF-return, power-integrity,
thermal, drill, via-process or board-level manufacturability defect. Production
remains **HOLD** and the order verdict remains **DO-NOT-ORDER** until the real
JLCPCB uploader and order preview preserve the authored process, placement and
part choices, and the physical first article passes its acceptance plan.

## Evidence

| Lens | Exact-release result |
|---|---|
| Artifact binding | Released PCB SHA-256 is `43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3`; the source checkout is exactly commit `798ef9812019efb9e9857332736926d099192a03`. |
| Connectivity and rules | A fresh KiCad 10.0.4 DRC on the exact PCB reports 0 violations, 0 unconnected items and 0 schematic-parity discrepancies (fresh report SHA-256 `34e787e916dcabbd7e9a1d856ec8638222a72ac381b16ed4214e097cfbc4c04`). The independently staged DRC and standalone-archive DRC also report 0/0/0. |
| Routing | The board has 242 track segments, 638 vias and four filled zones. All nine RF nets are continuous 0.295 mm F.Cu routes with no RF via or layer change. |
| RF return and coupling control | In1.Cu is an uninterrupted RF reference plane; In2.Cu is a second intentional ground plane. All 18 fence flanks pass, with 1.3979 mm worst aperture against the 1.4000 mm limit. Each SMA has four plated ground posts. |
| Power integrity | `VBUS_RAW` and `VBUS_PROTECTED` use 0.30 mm F.Cu routes; 3V3 uses 0.25 mm F.Cu. U3 input/output capacitors are each 1.875 mm from the associated supply pad, U1's local 100 nF capacitor is 1.22 mm away, and U2's is 2.403 mm away. The declared 3V3 load ceiling is 20 mA. |
| Thermal margin | The conservative U3 calculation is 44.825 mW and approximately 7.6 degrees C rise, well below the documented 238 mW board-dependent ceiling; first-article temperature remains authoritative. |
| Via process | Fresh grading covers 638/638 vias: 629 ordinary 0.45/0.20 mm untreated vias and exactly nine U1 exposed-pad 0.45/0.25 mm filled-and-capped vias. There are no partial or drill-disjoint classifications. |
| Drill/profile | PTH data contains the two via drill families, nine 1.50 mm SMA signal holes and 36 1.70 mm SMA ground-post holes. NPTH contains four 3.20 mm mounting holes and two 0.65 mm tooling/fiducial holes. The nominal board outline is 90 x 65 mm. |
| Assembly population | The exact release has 36 board footprints, 29 CPL placements and seven explicitly exempt unpopulated board-only items, with zero unexplained references; worst placement-datum error is 0.0005 mm at J1. |

## Findings and order controls

No board change is requested by this review. The remaining stops are external
execution and qualification controls, not hidden local passes:

- JLCPCB must echo the exact JLC04161H-7628 four-layer controlled-impedance
  stack and must not change the authored 0.295/0.200 mm RF geometry.
- JLCPCB must accept selective fill/cap for only the nine 0.25 mm U1 vias and
  leave the 629 ordinary 0.20 mm vias untreated.
- The uploader must accept all nine C429844 right-angle SMA connectors for the
  declared through-hole wave/manual process; refusal requires a separately
  generated hand-solder release.
- The resolved BOM and placement preview must preserve exact part codes,
  manufacturer lands, rotations, polarity and connector orientation.
- First-article rail, current, temperature, mechanical-fit and all-path RF
  measurements must pass before production use.

Severity summary: P0/P1/P2 design findings **0/0/0**. The exact hardware may
advance to uploader validation and a controlled first-article order, but this
record is not an order authorization.
