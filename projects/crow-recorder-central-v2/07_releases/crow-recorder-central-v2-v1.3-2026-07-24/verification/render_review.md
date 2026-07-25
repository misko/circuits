subject: crow-recorder-central-v2 v1.2-staging (07_releases/crow-recorder-central-v2-v1.2-2026-07-24)
date: 2026-07-24
reviewer: render-review (fable-medium, visual)
context-given: release-archive-only
verdict: PASS

# Method

Viewed all 8 v1.2 images (render_top_bare, render_bottom_bare, twin_top,
twin_bottom, twin_iso_nw, twin_iso_se, twin_edge_west, twin_edge_east) plus
v1.1 twin_top as baseline. Because the changes are 0402-scale, I additionally
inspected 3-4x magnified crops of the U1 (TQFP-128) region from both releases
(v1.2 bare + twin vs v1.1 twin, same crop window), a 4x crop of the
south-of-U1 zone, and 3x crops of the west/east halves of the port row.
(v1.1 render_top_bare exceeds the 2000px read limit; v1.1 comparison done on
twin_top, which shows the same silk and parts.)

# Check 1 — new 0402 caps around U1: clear of neighbors

In the magnified v1.2 crops, the decoupling ring around U1 is denser than
v1.1 on the west and south flanks (new parts visible in the C_c5/C_c9/C_c10
and C_d1/C_d2/C_pll2/C_c11/C_c13 clusters). Every 0402 in the ring has its
own distinct pad pair with visible soldermask gap to the next body; no two
bodies touch or overlap in either the bare render or the twin. The tightest
groupings (south row between FB_u33 and FB_u18, and the west column beside
U1's pin bank) still show clear separation at 4x.

# Check 2 — C_b0v9 at its new location

The 0805 C_b0v9 is visibly moved south of U1's south pin bank vs v1.1 (in
the matched twin crops it sits ~one body-length lower, centered in the south
decoupling cluster). Its body sits clear of C_att/C_c1/C_c13/C_c11 and of
FB_u33/FB_u18 on either side. The silkscreen title no longer runs under it:
in v1.1 the title crossed exactly this zone; in v1.2 the title is far to the
west and the C_b0v9 area carries only small refdes labels. No silk-over-body
or body-body collision.

# Check 3 — silkscreen legibility

- Relocated title: "crow-recorder-central-v2  8ch USB audio  C" now sits
  west of the USB-C connector, over open ground plane between the CL1/Rd
  area and the TP3-TP6 test-point row. Fully legible, not over any pads,
  not clipped. (The trailing "C" glyph matches v1.1 — pre-existing, not a
  regression.)
- Per-port warnings: counted all 8 "NOT ETH 5V!" texts, one per port
  (J3..J10 / Dp1..Dp8 positions), 4 in the west half crop and 4 in the east
  half crop. Each is legible and placed on open ground between the fuse and
  TVS parts, not over pads.
- Banner: "NOT ETHERNET — CUSTOM 5V AUDIO PINOUT" present, large, and clear
  below the port row (spans both crops).

# Check 4 — twin renders: parts on pads

In the twin (populated) renders, all bodies around U1's south side sit
centered on their pads — the new 0402s, the moved C_b0v9 (tan 0805 body on
its two pads), C_b3v3, U5 flash, the USB-C, and the crystal Y1 all register
correctly; nothing floating, offset, or rotated relative to v1.1. Iso NW/SE
views agree — component heights and orientations look normal. Known
adjudicated items observed as expected: J1 barrel jack model rides with its
adjudicated offset (MODEL-SELF, visible in edge views as the tall black
body), J2 USB-C body present (MODEL-REG false alarm), RJ45 ports show pads
only with no 3D bodies (no CAD models — expected absence, not a defect).

# Check 5 — bottom side empty

render_bottom_bare and twin_bottom show only pads/vias/traces and through-
hole protrusions (jack legs, JTAG header, mounting holes). Zero component
bodies on the bottom in the twin render, and the edge views (west/east)
show all bodies above the board plane only. All-top assembly confirmed.

# Verdict

PASS. The three v1.2 changes render exactly as described, with no new
collisions, no silk-over-pad, and no placement regressions vs v1.1.
