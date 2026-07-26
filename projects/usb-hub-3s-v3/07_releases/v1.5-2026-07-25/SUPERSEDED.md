# SUPERSEDED — v1.5-2026-07-25 is **DO-NOT-ORDER**

**Order from `07_releases/v1.6-2026-07-26/` instead.**

## Why: 11 of this release's 108 CPL rows are off JLC's placement datum

A new **A-POS** gate measured every CPL row against the convention JLC actually
uses — **a part is positioned from the bounding box of its PAD CENTRES** — and
found that this release's exporter had been emitting `fp.GetPosition()`, the
KiCad footprint **ANCHOR**. Those two points coincide only when a land happens
to be symmetric about its anchor, and on this board's connectors they are far
apart:

| ref | what it is | offset from JLC's datum |
|---|---|---|
| **J1** | AMASS XT60 — **the battery inlet** | **4.6861 mm** |
| **J2 / J3 / J4** | USB-A receptacles | **3.7346 mm** each |
| **J5** | USB-C receptacle, **0.500 mm pitch** | **1.4975 mm** |
| Q4 / Q5 / Q6 | PowerPAK power MOSFETs | 0.0625 mm each |

**Every external connector on the board is affected**, the worst by nearly 5 mm,
and JLC places the part where the CPL says — so every pad on those parts is off
by that amount. On J5, 1.4975 mm against a 0.500 mm pitch is three full pitches.

This is **not** a rotation defect. It is orthogonal to the C1/C2 rotation problem
that made v1.4 DO-NOT-ORDER, and no render, 3D view or assembly preview image
would have shown it — the geometry in `source/` is correct; only the numbers in
`fab/cpl.csv` are wrong.

## What v1.6 does about it

The exporter now computes the pad-array centre (`placement_datum()`). In v1.6 all
**119** CPL rows are graded against it and the worst residual is **0.00050 mm**
against a 0.05 mm tolerance. J1's row reads `(27.0, -40.4)`, the pad-array centre,
where v1.5 shipped `(30.0, -44.0)`.

## v1.6 is also a COPPER revision, so it is not a paperwork re-issue

The changes below are real hardware differences; `fab/` is **not** byte-identical
to this release.

- **H3 mounting hole was a short of the 6 A rail to GND through a screw.**
  MEASURED on this release, on filled copper: F.Cu carried GND at 1.850 mm **and
  5VA at 1.850 mm**, B.Cu 5VA at 1.850 **and** GND at 1.851 — 0.250 mm of bare
  laminate and ~20 um of solder mask, on both faces. Every M3 fastener bridges it,
  including the smallest cap head. v1.5's only mitigation was a sentence about
  nylon standoffs in its ORDER_README.
- **H4** VBUSA3 reached 4.152 mm (inside a DIN 9021 washer); **In2's 9-12.6 V VIN
  plane** sat 1.850 mm from every 1.600 mm drill.
- **VBUS ampacity**: each of VBUSA1/2/3 ran 13.554 mm of 0.500 mm B.Cu at exactly
  the class floor, carrying ~2 A. Now 0.800 mm.
- **All six power MOSFETs** carried ONE 100 %-area paste aperture over a
  14.897 mm2 exposed pad; IPC-7093 asks 50-80 % as an array. Now a 2x2
  window-pane at 65.0 %.
- **USB-C delivery corner**: F2 had ZERO vias on either pad at 0.775 W and PMID
  crossed layers on two. Now 4 per F2 pad, PMID 13, VBUSC 15, 3 per J5 VBUS pair.
  (These close this release's own review items B2 and B3.)
- **Zero fiducials** on a board whose smallest machine-placed pitch is 0.500 mm.
  v1.6 has three.
- **5 status indicators added** — none existed, so nothing on the board could tell
  you the pack was live or a port had latched off.

## And a documentation defect that this release inherited

This release's paperwork instructs the user to set **`PSU_MAX_CURRENT=5000`** in
the Pi's bootloader EEPROM. **That is a Raspberry Pi 5 setting and the confirmed
load is a Pi 4, which has no such option.** A Pi 4 does not negotiate PD for its
power input at all — it is a plain 5 V sink at 5 V / 3 A. The instruction was
un-followable. See ADR-0004; ADR-0001 is marked `superseded-by: 0004`.

The correction also moves the delivery margin from **+15.0 mV to +244.2 mV** with
no hardware change, which retires this release's own warning that "15 mV of paper
slack is not a margin you ship on" — it was a true statement about the wrong load.

## Status of this directory

**IMMUTABLE.** Nothing in it has been edited; this file is an addition. The
evidence, reviews and MANIFEST remain as sealed for the record.
