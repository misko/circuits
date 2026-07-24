subject: crow-recorder-central-v2 v1.1 staging (pre-seal)
date: 2026-07-24
reviewer: render-review (zero-context sub-agent, Fable 5 medium)
context-given: release-archive verification renders + twin report + BRIEF/ARCHITECTURE (curated; journals/STATUS/08_reviews excluded)
verdict: PASS

---

RENDER REVIEW of crow-recorder-central-v2 v1.1 staged release complete. All eight verification renders plus twin_report.txt and missing_models.txt examined; zoomed crops made for every MODEL-REG/MODEL-SELF/POLARITY-CHECK part.

| Finding | Severity | Evidence |
|---|---|---|
| D1 (SMA, POLARITY-CHECK) polarity CONSISTENT: model cathode band on WEST end; silk shows closed cathode bar + pin-1 dot on WEST end, box open at anode end | disposition, no defect | twin_top 10x crop (band west) vs render_top_bare 9x crop (silk bar west) |
| J1 barrel (MODEL-SELF/MODEL-REG): mouth faces WEST edge (opening visible head-on in twin_edge_west), THT leads protrude below board = in holes; body renders ~5mm east of its courtyard — matches the declared model-internal bbox defect (-2.20,+4.43mm in JLC's own frame), not a placement error; bare render pads/courtyard sit correctly at the edge | P2 (adjudicated model artifact) | twin_edge_west, twin_top crop, render_top_bare |
| J2 USB-C (MODEL-REG): leads/shell posts land on our pad field, shell pads straddle body symmetrically, mouth faces SOUTH board edge; slight (~1-2mm) apparent setback consistent with the reported 1.1mm model bbox asymmetry. No rotation flip warranted. Order-preview eyeball still owed per the adjudication note | P2 (false-alarm confirmed visually; ORDER_README action outstanding) | twin_top 3x crop, twin_iso_nw/se |
| J3-J10 RJ45 bank: bodiless as expected (C9900035627 adjudicated no-CAD, consign, excluded from CPL — not "unplaced"; missing_models.txt shows 0 missing of 172 modeled). Footprints along north edge, courtyards overhang outward, THT + latch holes present and uniform x8 | no defect | twin_top, render_top_bare, missing_models.txt |
| Silk: 8x "NOT ETH 5V!" present (one per jack), banner "NOT ETHERNET — CUSTOM 5V AUDIO PINOUT" and pinout legend "1,2=AUDIO+/- 3,6=+5VBEEP/RTN 4,5&7,8=+5VAUD/GND" all legible; board name + "5V IN (GST25A05)", "JTAG 1V8" legible | no defect | render_top_bare, twin_top |
| Refdes clutter in the two ADC decoupling clusters (labels overlap tracks/each other, e.g. Rs4M/Cc2M region) — readable at zoom, cosmetic only | P2 | render_top_bare |
| Q1/Q2/U9/U4/F1-F8/U10 (adjudicated rows): bodies present and centered on courtyards (MODEL-REG 0.00-0.07mm), no visible lead-off-pad | no defect | twin_top, twin_report MODEL-REG-OK lines |
| Bottom side: no part bodies (all-top CPL), sparse routing, no copper/mask anomalies; edge profiles show nothing overhanging except J1 at the west edge | no defect | render_bottom_bare, twin_bottom, twin_edge_west/east |

No P0/P1 defects found. The three machine flags (J1 MODEL-SELF/REG, J2 MODEL-REG, D1 POLARITY-CHECK) all disposition as false alarms / known model artifacts on visual inspection; no rotation overrides proposed. Only carried obligation: the J2 and J3-J10 order-time JLC preview eyeballs already recorded in ORDER_README.

RENDER REVIEW: PASS