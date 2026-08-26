# Pluto RX2 eight-way v5 enclosure v0.4.0

Overall status: **INCOMPLETE**

Shell status: **CAD_READY**
Antenna-candidate verification run: **COMPLETE / collision PASS**

Based on immutable PCB release **v0.2.1-2026-08-14**.

This revision separates PCB retention from shell closure. Four M3 × 6 screws
retain the PCB directly to four short base standoffs. Four other M3 × 6 screws
in external corner lugs close the lid to four tall base posts. Removing the
lid therefore leaves the PCB fully fastened instead of allowing it to move
inside the enclosure.

This immutable enclosure release replaces the removable clip concept with a
separate, closed-top, two-screw RX2/reference-antenna adapter. The complete
already-wired L-shaped antenna loads vertically through the adapter's full
rectangular underside opening. Nothing passes through the PCB lid and the
cable is never threaded through a closed bore.

## Full-antenna south arch

The bottom-open south U-arch is governed by the modeled antenna body rather
than the cable:

- candidate lower antenna diameter: **10.00 mm**;
- arch diameter: **10.80 mm**;
- antenna radial clearance: **0.40 mm per side**;
- candidate cable diameter: **2.50 mm**;
- cable radial clearance inside the same arch: **4.15 mm per side**;
- arch center above the closed lid: **5.20 mm**;
- arch crown: **10.60 mm**;
- remaining roof ligament: **3.00 mm**.

The complete antenna-and-cable insertion sweep is `EMPTY`. The arch remains
bottom-open for its full width, so a prewired D10 lower antenna body can move
straight upward with its attached cable before the adapter is fastened.

## Printable files

- `meshes/base.stl`
- `meshes/lid.stl`
- `meshes/insert_coupon.stl`
- `meshes/rx2_antenna_mount.stl`
- `meshes/rx2_antenna_fit_gauge.stl`

The adapter attaches with two M3 x 8 socket-head screws into E-Z LOK
`260-M3-BR` or dimensionally equivalent `260-M3-CR` cold-press inserts in the
reinforced lid bosses. The selected production pilot remains 4.25 mm and is
still subject to the required coupon test.

## Independent PCB and case fasteners

- PCB screws: **4 × M3 × 6**, at H1–H4;
- PCB insert engagement: **4.400 mm**;
- PCB screw-tip clearance: **0.375 mm**;
- case screws: **4 × M3 × 6**, at `(±49.0, ±36.5)` mm;
- case insert engagement: **4.400 mm**;
- case screw-tip clearance: **0.375 mm**;
- base case posts: **9.0 mm diameter**;
- lid closure lugs: **14.0 mm diameter**, with D9.4 post sleeves;
- minimum post-to-PCB-corner clearance: **1.157 mm**.

The connector-wall body remains 96.8 × 71.8 mm. Only the four external
closure lugs extend the total envelope to 112.0 × 87.0 mm, so the SMA and
USB-C connectors are not recessed farther into the shell. No lid column bears
on the PCB, and no PCB screw shares an axis or stack with a case screw.

## Automated evidence

- sealed PCB/STEP/interface bindings: PASS;
- STEP occurrence coverage: 30/30 modeled refs;
- shell verification: CAD_READY, 6/7 checks PASS;
- independent fastener geometry: 13/13 PASS;
- printable meshes: 5/5 PASS;
- exact installed-case/component intersection: EMPTY, 0 mm³;
- accessory selector census: PASS;
- complete antenna/cable insertion sweep: EMPTY;
- antenna versus mount, fasteners, lid, board and cable: EMPTY;
- exact candidate antenna versus sealed STEP components: 0 mm³;
- exact candidate cable versus sealed STEP components: 0 mm³.

`verification/shell-verification.json` is subordinate shell evidence. The
top-level release status is governed by
`verification/antenna-clearance.json`, which remains `INCOMPLETE` because the
actual antenna/cable profile and physical fit have not been evidenced.

The enclosure binds the exact PCB, STEP, and manifest bytes from PCB release
v0.2.1. It does not repair or reseal that PCB release. Its historical
`MANIFEST.txt` names two ignored `.kicad_prl` files that are absent from the
repository; this known parent-release integrity caveat is carried explicitly
and does not change the exact PCB/STEP geometry used here.

## Required physical closure

Before printing this as a production accessory:

1. Measure or obtain a dimensioned drawing for the actual antenna body,
   elbow, taper, upper stalk, cable and termination.
2. Print the antenna fit gauge and confirm the selected body clearance.
3. Print the adapter and verify insertion, retention, rattle and removal with
   the real prewired antenna.
4. Confirm all four PCB screws retain the board with the lid removed; then
   verify the four separate case screws close the lid without loading the PCB.
5. Confirm both antenna-adapter M3 inserts install without boss damage and the
   adapter seats flat without pinching the antenna or cable.
6. Perform the normal board drop-in and simultaneous interface-mating tests.

This release is **not PRINT_VERIFIED, not THERMALLY_VERIFIED, and not an order
authorization**. It is an immutable, discoverable release of the printable
candidate and its complete automated evidence at the status actually achieved.
