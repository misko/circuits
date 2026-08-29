# Pluto RX2 eight-way v5 enclosure v0.8.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v0.2.1-2026-08-14**

Enclosure predecessor: **v0.7.0-2026-08-27**

This immutable successor replaces the predecessor lid's four weak, nearly
tangent D14 screw-lug/roof necks with full-height blended load paths while
preserving the roof-only connector-service topology. The 2.4 mm roof, base
datum, RX2 antenna mount, and fit gauge remain on the same exact PCB/STEP and
connector authorities.

The two south lid joints use D14 inboard roots. The two north joints use D12
roots because an all-D14 trial intersected the exact populated STEP by
1.322689 mm3 at the outer north SMA bodies. The selected D14-south/D12-north
design has an exact installed collision of **0 mm3**. Conservative clearances
to the represented legacy service candidates are 4.88 mm at the north SMA
bank, 3.09 mm at the side SMA banks, 29.10 mm at USB-C, and 3.01 mm at the
J11/J12 top-service region. No continuous wall or skirt crosses a J1-J10
mating axis.

Exact vertical mesh sections measure 104.01-105.04 mm2 with a 14.00 mm throat
at the south lid roots, and 90.28 mm2 with a 12.01 mm throat at the north lid
roots. Corresponding independently measured members are 103.60 mm2 south and
100.32 mm2 north; root/member area ratios are 1.004-1.014 south and 0.900
north. The lid sleeves are D9.8 over D9 case posts (0.40 mm nominal radial
clearance), and lid screw bores are D3.8 for M3 hardware.

The structural census also covers the four base case posts, four PCB pillars,
two lid antenna-mount bosses, two antenna-mount screw columns, and both
intentional flexure rails. In total the contract closes 18 critical
attachments, 12 load cases, 5 printable parts, and 90 structural assertions.
The exact mesh-visible structural screen passes all declared sections and
reinforcement thresholds.

The additional load census traces north/south and east/west connector
mate/unmate, cable pull/bend, and SMA hand/wrench reaction through all four
H1-H4 clamp roots without crediting an open case wall or connector body.
Connector, solder-joint, PCB, screw-clamp, and tool capacity remain
unquantified. Installed antenna axial/lateral reaction continues through both
lid bosses, every lid closure web, and every base-post root; antenna insertion
and removal are constrained to the detached hood before its screws are fitted.

## Printable files

- `meshes/base.stl` — open foundation with four tapered PCB-pillar roots and
  four tapered independent case-post roots;
- `meshes/lid.stl` — reinforced roof-only plate with four broad blended
  closure webs and two tapered antenna-mount bosses;
- `meshes/insert_coupon.stl` — D4.15-D4.45 insert-fit ladder;
- `meshes/rx2_antenna_mount.stl` — bottom-loading RX2 antenna hood; and
- `meshes/rx2_antenna_fit_gauge.stl` — non-installed fit-selection gauge.

The PCB remains retained independently by four M3 screws on H1-H4. Four
separate M3 screws close the case at C1-C4, so removing the lid does not
release the PCB.

## Automated evidence

- all 5 printables regenerate deterministically from the bound authored SCAD;
- every printable is one closed, edge-manifold, consistently oriented mesh;
- exact root/member probes pass the complete 18-attachment structural census;
- all 12 declared load cases are referenced by at least one critical joint;
- exact installed-case collision against the represented STEP is `EMPTY`,
  exactly **0 mm3**;
- the connector-assembly receipt covers the declared enclosure interfaces but
  remains `INCOMPLETE` because exact mate, tool, grip, rear-termination, cable,
  and bend envelopes are not fully known; and
- the antenna candidate replay passes its conservative CAD checks while
  keeping physical fit `INCOMPLETE`.

The renders are visual-review evidence only.

## Why status remains INCOMPLETE

No canonical printer/build volume or pinned slicer, material profile, and
toolpath is bound. Whole-part local thickness and self-intersection analysis
are not implemented. No physical print establishes insert fit, board seating,
closure torque, one-corner twist, lid removal, repeated service, roof warp or
creep, antenna reaction, simultaneous connector service, or thermal behavior.
Connector mate/unmate force, cable pull/bend, and SMA hand/wrench reaction
also require quantified physical proof across the connector-to-PCB-to-H1-H4
load chain.
The two antenna-mount rails intentionally remain compliant and require the
declared physical insertion/removal test.

Before promotion:

1. Slice all five exact meshes with a pinned printer/material/profile and
   inspect every layer without repair, rescaling, auto-orientation, or hidden
   support changes.
2. Print the insert coupon and qualify the exact insert lot and PETG process.
3. Torque and cycle all four closure joints, including one-corner preload,
   chassis twist, lid pry/removal, warp, and antenna-reaction cases.
4. Verify PCB seating, lid-off retention, and antenna-mount insertion,
   retention, cable clearance, and repeated service.
5. Mate the real USB-C and all SMA assemblies with representative cables and
   tools, then run the declared roof-covered thermal soak.

This release is not `CAD_READY`, `PRINT_VERIFIED`, `THERMALLY_VERIFIED`,
order-ready, or a production-fit claim.

## Release-root replay

The release-local closure includes exact PCB authorities, connector evidence,
authored CAD, all printable meshes, generation/collision receipts, the FDM
contract and receipt, and the exact replay compilers/helpers. Replay must
regenerate all five printables and the installed case, reproduce the FDM
receipt byte-for-byte, preserve the exact 0 mm3 collision result, and reopen
the complete payload census without modifying the parent PCB release or any
predecessor enclosure.
