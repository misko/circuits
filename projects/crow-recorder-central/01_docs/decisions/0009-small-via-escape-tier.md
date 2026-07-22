> Adopted 2026-07-21 into crow-recorder-central from archived_projects/crow-array-central (provenance ADR 0011; re-verified by this project's own gates before any release). Original text follows.

# ADR-0009 — fine-pitch escape uses the JLC 6L SMALL-VIA option (corrects ADR-0008's "standard tier, no advanced vias")

Status: accepted 2026-07-18. Refines ADR-0008 (6-layer escalation): the layer
budget was right, but the "JLC 6L standard tier (0.45/0.3 vias, no advanced
small-via option)" claim did not survive DRC.

## Context — the 0.4 mm-pitch via-in-pad escape cannot use 0.45/0.30 vias

The XU316 is a TQFP-128 at 0.4 mm pitch. KRT escaped several peripheral pins
as **via-in-pad** (a via dropped in the SMD pad, 0.25-0.30 mm dia / 0.15 mm
drill). The stitcher then normalised every sub-floor via UP to the standard
tier 0.45/0.30. At 0.45 mm diameter on a 0.4 mm pitch:

- Two adjacent via-in-pad vias sit 0.4 mm apart -> 0.45 mm copper OVERLAPS ->
  a hard SHORT (the TDO/TDI pair: 6 shorting_items).
- A 0.45 barrel / 0.30 drill encroaches the neighbour pads -> 24 hole_clearance
  (drill within 0.125-0.194 mm of a different-net pad, < the 0.2 mm floor).

This is golden-rule-5 territory (0.4 mm pitch = nothing fits between pads at
standard geometry). Relocating 0.45 vias into the congested escape channel did
not converge (TDO's dogbone always clipped pad 38; the channel is saturated).

## Decision — ship the fine-pitch escape at the JLC 6L small-via option

- Escape vias stay at **0.30 mm dia / 0.15 mm drill** (0.075 mm annular). At
  0.30 mm a via-in-pad keeps a 0.10 mm copper gap at 0.4 mm pitch (no short)
  and 0.20 mm hole-to-copper to neighbours. `stitch_and_fill.py` normalises
  the sub-floor floor to 0.30/0.15 (was 0.45/0.30); `generate_rules.py` sets
  `min_via_diameter 0.30 / min_through_hole 0.15`.
- The bulk grid + GND service/rescue vias stay 0.6/0.3 and 0.45/0.3 standard;
  only the fine-pitch escape needs the option, but JLC prices the option on
  the SMALLEST via, so it applies board-wide.
- The commission brief's DRU already asked for a 0.25 mm via drill floor
  ("min via 0.45/0.25"), i.e. it had ALREADY invoked the sub-0.30-drill
  small-via option; 0.15 mm is JLC's floor for that same option, so no new
  process class is introduced — only a smaller drill within it.
- The one adjacent pair that still fails at 0.30/0.15 (TDO/TDI, drills 0.18 mm
  apart) is fixed by a placement nudge: `route_fixups.py` dogbones TDO out of
  pad 37 south into the escape channel (F.Cu dogbone + B.Cu bridge), which is
  exactly the ADR-0004 straight-out escape the pair should have used.

## Consequence

- **Cost rises** vs the plain 6L standard board: JLC's small-via (advanced /
  <0.30 mm drill) option adds a per-order fee. Reported in the release cost
  headline alongside the 6L + 176x122 mm drivers.
- DRC via-congestion classes (6 shorts + 1 hole_to_hole + 24 hole_clearance)
  all clear. The DRU capability floors (D20) + this tier are what turn the
  inflated 101-count report into only genuine violations.
- If a future spin wants to avoid the small-via fee, the lever is a package
  change (fixed by the commission) or an every-other-pad F.Cu-only escape on
  the affected pins — not a via-size change (0.45 does not fit).
