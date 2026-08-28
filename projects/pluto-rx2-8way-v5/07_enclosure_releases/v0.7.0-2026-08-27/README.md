# Pluto RX2 eight-way v5 enclosure v0.7.0

Immutable **INCOMPLETE** candidate for fabricated PCB release
`v0.2.1-2026-08-14`.

This revision preserves the v0.6.0 pillar-only base, independent PCB/case
fasteners, and RX2 antenna mount/fit gauge. It replaces the upper perimeter
skirt with a roof-only lid:

- J1-J10 have no continuous connector-facing case wall;
- the roof stops at `Edge.Cuts`, adding 0.0 mm nominal mating-plane setback;
- J11/J12 use a south-edge-open service notch;
- four localized closure lugs remain outside every schema-v1 candidate
  connector corridor; and
- the exact installed case has 0 mm³ collision with the sealed STEP assembly.

The case does **not** solve the board's intrinsic 0.0 mm positive SMA exposure
or its 15/18 mm connector pitch. The 2.40 mm base foundation still projects
3.40 mm beyond `Edge.Cuts` below connector height. The shared connector
receipt is `INCOMPLETE` (48 of 50 facts unknown), so complete mates, grips,
tools, torque/reaction paths, cables, bends, simultaneous service operations,
tolerances, and deck clearance require exact authority and physical tests.

## Printable payload

- `meshes/base.stl`
- `meshes/lid.stl`
- `meshes/insert_coupon.stl`
- `meshes/rx2_antenna_mount.stl`
- `meshes/rx2_antenna_fit_gauge.stl`

Print the insert and antenna fit coupons before the case. The modeled 4.25 mm
insert pilot is a prior from the documented Pluto coupon lineage; the D8.50
antenna key and D9.55 upright aperture remain unverified compliant-fit
candidates. Stop if insertion mars the antenna or requires damaging force.

## Evidence boundary

Automated evidence passes the schema-v1 geometry boundary, exact STEP
inspection (30/30 modeled refs), one-component/manifold mesh checks, the
installed-position collision check, and the project RX2 non-fit/full-body
selectors. Governing scopes `shell`, `board_retention`, `antenna_accessory`,
and `thermal` are all published as `INCOMPLETE`.

Required physical work includes insert and antenna coupons, four-support PCB
seating/load path, lid-off retention, closure independence, actual connector
mating/hand-start/tighten/remove with populated neighbors, cable strain/deck
clearance, antenna insertion/retention/cycles, and thermal soak.

This candidate is not order-ready, weatherproof, or RF-shielding.
