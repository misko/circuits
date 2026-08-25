# Pluto RX2 eight-way v5 enclosure v0.2.0

Status: **CAD_READY**

Based on immutable PCB release: **v0.2.1-2026-08-14**

This immutable enclosure release retains the existing split shell and its
physically selected 4.25 mm production insert pilot, then adds a separate
two-screw RX2/reference-antenna clip. It also replaces the old lid markings
`ANT1` through `ANT8` with substantially larger `A1` through `A8` markings.
No older PCB or enclosure release was edited.

## Printable files

- `meshes/base.stl`
- `meshes/lid.stl`
- `meshes/insert_coupon.stl`
- `meshes/rx2_antenna_clip.stl`
- `meshes/rx2_clip_fit_coupon.stl`

All five meshes are single-component, edge-manifold, consistently oriented,
positive-volume solids. The exported lid is exterior-face down; the separate
clip and both coupons use their broad flat face on the bed. Supports are not
required by the authored geometry.

## RX2 clip construction

The clip attaches at two points to prevent rotation. Two M3 x 8 socket-head
screws enter two E-Z LOK `260-M3-BR` or dimensionally equivalent
`260-M3-CR` cold-press inserts from above. The inserts are pressed from the
lid underside into reinforced bosses that flare from 9.00 to 12.00 mm and
reuse the already selected 4.25 mm pilot. Do not substitute a generic
heat-set insert.

The fastener stack is asserted in the bound SCAD and generated successfully:

- minimum flange-pocket radial wall: 1.450 mm;
- roof skin above the blind pilot: 0.825 mm;
- M3 x 8 thread engagement: 4.175 mm;
- screw-tip clearance: 0.600 mm;
- shallow socket-head locating recess: 0.500 mm.

Inserts enter from below, so an upward antenna pull reacts the insert flange
into the boss and lid roof. The assembled lid remains removable; the clip tail
has at least 1.0 mm nominal clearance from the SWD/5V service-opening envelope.

## Antenna and cable fit is not yet authoritative

The rendered reference antenna is a candidate witness, not a sourced part.
Legacy SPF fixture source suggests a 9.0–10.0 mm body family but carries no
authoritative drawing or MPN. The production source defaults to 10.0 mm only
to make a CAD candidate, while `rx2_clip_fit_coupon.stl` provides 9.0, 9.5,
10.0, and 10.5 mm snap stations.

The one missing production measurement is the **outside diameter across a
straight cylindrical antenna grip zone at least 14 mm long**. Measure that
zone and print the ladder before selecting or revising the production clip.
Do not force the antenna into the default clip.

The pigtail witness is 2.50 mm OD with a deliberate 15.0 mm centerline bend
and a post-bend open-top snap strain relief. Bind the actual cable MPN and
respect its datasheet bend radius before physical qualification. Pluto+
documentation establishes the short-edge order `TX2 · RX2 · RX1 · TX1`, but
standard versus RP-SMA remains unconfirmed; verify the real mating cable.

## Automated verification

- exact subject bindings: 5/5 PASS;
- connector/interface coverage: 62/62 PASS;
- configured fastener geometry: 9/9 PASS;
- printable meshes: 5/5 PASS;
- clean package replay: 5/5 STL byte identities reproduced exactly;
- sealed STEP occurrence coverage: 30/30 modeled footprint refs;
- exact STEP-component/installed-case intersection: EMPTY, 0 mm^3;
- thermal-plan consistency: 2/2 PASS;
- physical evidence: INCOMPLETE, 0/3.

The exact collision subject includes the new underside lid bosses and the
installed external clip, but excludes the antenna and cable witnesses. The
empty result therefore proves that the reinforced lid clears every component
solid present in the sealed PCB STEP; it does not prove antenna fit or cable
mating.

## Remaining physical validation

1. Print and qualify the 4.25 mm insert coupon using the intended printer,
   material, orientation, and process.
2. Print the antenna clip ladder and select a non-marring retained fit against
   the measured 14 mm-or-longer body zone.
3. Print the base, lid, and selected clip; install four base inserts and two
   underside lid inserts without cracks, spin-out, or pull-out tendency.
4. Confirm the assembled PCB drops in, the lid closes freely, and all nine
   SMA, USB-C, SWD, and bench-power interfaces mate simultaneously.
5. Install the actual reference antenna and pigtail; verify the antenna remains
   supported with the Pluto end disconnected and the cable does not violate
   its minimum bend radius.

Until those observations are recorded, this release is **not
PRINT_VERIFIED**, thermally verified, or evidence of an authoritative antenna
fit.

The self-contained replay package is in `package/`. It contains the exact PCB,
STEP, interface, authored SCAD, five printable meshes, installed-case mesh,
exact collision evidence, verification receipt, and path-rebased replay
configuration. The authored-accessory selector contract rejects unknown names
and canonicalizes ASCII-STL facet order, so a clean replay reproduces the raw
mesh hashes rather than only equivalent volumes.
