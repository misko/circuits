subject: crow-recorder-central v1.0 (pre-seal, git tree at HEAD 2026-07-22)
date: 2026-07-22
reviewer: render-review (Claude Opus 4.8, fresh-context visual — bare + twin renders + assembly + schematic PNGs)
context-given: zero-context (8 render images only; no design tree)
verdict: PASS-WITH-NOTES

---
VERBATIM REVIEW FOLLOWS
---

I've reviewed all eight images (top/bottom copper, four twin 3D views, assembly drawing, and schematic), cropping the dense and safety-critical areas for legibility. Here is my complete fresh-eyes review.

## Per-image confirmation

- **bare_top.png** — Reviewed in full plus zoomed crops of the MCU, both ADCs, the power/barrel cluster, and the USB-C edge. Layout matches the brief.
- **bare_bottom.png** — Mostly a ground/pour side with a few short routes, backside pads for the barrel jack and USB-C mount posts. Nothing off-board, no stray copper islands of concern.
- **twin_top / twin_bottom / twin_iso_nw / twin_iso_se** — Consistent placement. Only U1 (MCU), U2/U3 (ADCs), the two buck inductors and a handful of others render with 3D bodies; the RJ45s and most passives show as bare footprints = **no 3D model available, not unplaced** (verified populated via assembly drawing). Nothing mis-rotated, off-pad, or off-board in any iso view.
- **assembly_top-1.png** — Read block-by-block; all refdes/values consistent with the schematic.
- **schematic-1.png** — Single sheet, 15 numbered functional blocks + 8 port blocks, all legible.

## Design vs. brief — all present and correct
- TQFP-128 MCU **U1 = XU316-1024-TQ128** (XMOS xcore.ai), center, with visible pin-1 chamfer triangle (top-left) and a thermal exposed pad w/ via array. Good.
- Two TSSOP ADCs **U2 / U3 = PCM1865** (ch1-4 / ch5-8), flanking the MCU.
- Two bucks **U10 (3V3) / U11 (0V9)** with inductors L10/L11, lower-left.
- **USB-C J12** (USB4105-GF-A) bottom-center; **barrel jack J9** (DC-005) left edge.
- 8× RJ45 **J1–J8**, with **J7 & J8 clearly silked "PORT 7 DNP" / "PORT 8 DNP"** = the 2 by-design DNPs. Board carries a prominent **"NOT ETHERNET — CUSTOM 5V/AUDIO PINOUT"** banner (good, prevents a dangerous mis-plug into a real switch).
- Power-entry disclaimer consistent: schematic block 1 says "barrel(pop) / terminal(DNP)", silk says "5V TERM DNP" over J11. Consistent.

## Observations

**P1 — Verify USB-C mating opening actually reaches the board bottom edge.**
Image: bare_top.png / bt_usbedge crop. J12's lower mounting posts sit roughly a few mm in from the bottom board edge, with the "crow-recorder-central v1.0" / "J12" silk in the gap between the connector and the edge. On a horizontal USB-C receptacle the plastic body/opening normally overhangs past the front posts, so this is *probably* fine — but a fresh set of eyes cannot confirm the opening is flush/overhanging vs. set back. If it's set back, a cable won't seat. Confirm the connector's front face reaches or overhangs the edge (and same sanity-check for barrel jack J9's insertion axis at the left edge).

**P2 — Refdes/value crowding in the per-port protection rows and ADC input clusters.**
Images: assembly_top-1.png (as_conn crop), bare_top ADC crops. In the assembly drawing the per-port annotations (TPD2E2006 / PTC / AD3400x beep / gate values) overlap heavily between adjacent ports, and the ADC-coupling clusters (R60-R62, C54-C57, etc.) are dense. On the actual board silk (bare_top) the reference designators remain individually legible; this is a drawing-density cosmetic note, not a board defect.

**P2 — Twin 3D renders lack models for most parts (RJ45s, passives, connectors).**
Not a defect per the modeling rule — populated status confirmed via assembly drawing/CPL. Noted only so a downstream reviewer doesn't misread the bare footprints as unpopulated.

## Verdict
**PASS-WITH-NOTES** — No P0/brick-level issues. Layout, polarity/pin-1 marks, DNP labeling, and the "NOT ETHERNET" safety banner all look correct. The one thing worth a physical/DRC-edge check before fab is the **USB-C (J12) opening-to-board-edge clearance** (P1 verify); everything else is cosmetic.
