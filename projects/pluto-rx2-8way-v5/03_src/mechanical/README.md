# Pluto RX2 8-way v5 printable enclosure

This is a support-free, two-piece FDM enclosure for the exact 90 x 65 x
1.6 mm `pluto-rx2-8way-v5` PCB. It provides openings for all nine right-angle
SMA jacks, USB-C power, and a shared top service bay for J11 SWD and J12 bench
power. It remains usable when only some SMA positions are populated.

The lid now accepts a **separate** printable RX2/reference-antenna clip. Two
M3 x 8 socket-head screws attach that clip to two E-Z LOK inserts pressed from
the lid underside. The clip holds a candidate 10 mm right-angle antenna body
at two open-top snap stations, keeps its weight off the Pluto+ RX2 connector,
and guides an RG316-class pigtail through a 15 mm-radius bend and a post-bend
snap strain relief. `rx2_clip_fit_coupon.stl` is mandatory because no
authoritative antenna drawing or cable MPN is currently bound to this design.

The Pluto+ mechanical record identifies the short-edge RF order as
`TX2 · RX2 · RX1 · TX1` and the RX2 jack as a right-angle SMA-family female
connector. It does **not** yet settle standard versus RP-SMA or provide an
authoritative enclosure/antenna model. This enclosure therefore uses a cable,
never a rigid direct mate, and treats the antenna and cable solids in renders
as clearance witnesses rather than sourced production geometry.

The case uses the PCB's four 3.2 mm mounting holes. Four M3 x 20 socket-head
screws pass through the lid, printed spacer columns, and PCB into four flanged
M3 inserts in the base. No separate lid fasteners are needed.

## Insert assumption and calibration

The default pocket targets the E-Z LOK E-Z Press flanged M3-0.5 insert
`260-M3-BR` or dimensionally equivalent `260-M3-CR`:

- 4.216 mm nominal body diameter
- 5.537 mm flange diameter
- 4.775 mm overall length
- 3.962 mm (5/32 inch) manufacturer starting hole

FDM holes commonly print undersize. Print `insert_coupon.stl` first. Its four
pockets, left to right when the recessed labels face you, are 4.15, 4.25,
4.35, and 4.45 mm in the model. Physical coupon testing selected 4.25 mm as
the smallest reliable fit, so the production base and enclosure contract use
a 4.25 mm pilot. Do not install an insert by melting it with a soldering iron:
this insert family is intended to be cold-pressed.

The flange recess is deliberately 6.10 x 0.80 mm so the PCB rests on a plastic
annulus rather than on the metal flange. Confirm this against one physical
insert before assembling the board.

The two new lid bosses reuse that exact insert family and 4.25 mm pilot. They
flare from 9.00 mm at the insert flange to 12.00 mm at the roof and project
3.50 mm into the lid interior. The resulting minimum flange-pocket radial wall
is 1.45 mm. Inserts enter from the underside, so an upward clip pull seats each
insert flange into the reinforced boss instead of extracting it.

The clip screw stack is explicit and checked in the authored source:

| RX2 clip fastener dimension | Value |
|---|---:|
| Screw | M3 x 8 socket-head cap, two required |
| Clip plate / head locating recess | 3.20 / 0.50 mm |
| Insert engagement | 4.175 mm |
| Screw-tip clearance inside insert | 0.600 mm |
| Roof skin above blind insert pilot | 0.825 mm |
| Minimum boss wall at flange recess | 1.450 mm |

Do not substitute a generic heat-set insert: the pocket, pull direction, and
stack above are specific to E-Z LOK `260-M3-BR` or dimensionally equivalent
`260-M3-CR` cold-press inserts.

## RX2 antenna fit authority

Legacy SPF fixture source records two unsourced candidate antenna families in
the 9.0–10.0 mm body range. That is useful for a coupon ladder, but is not an
authoritative production dimension. The clip source therefore defaults to
10.0 mm and the fit coupon provides 9.0, 9.5, 10.0, and 10.5 mm snap stations.

The one missing production measurement is the **outside diameter across a
straight cylindrical antenna grip zone at least 14 mm long**. Measure that
zone with calipers, then print the ladder and select the station that retains
the real body without crushing or marring it. Do not force an antenna into the
10.0 mm default. A selected ladder station qualifies only the antenna clip;
it does not qualify the complete enclosure or promote it to `PRINT_VERIFIED`.

The modeled cable is a 2.50 mm-OD RG316-class candidate with a 15.0 mm
centerline bend. Bind the actual pigtail MPN and respect its datasheet minimum
bend radius before treating the route as production-qualified. The open guide
rails and post-bend snap station deliberately react cable pulls into the
separate clip, not into the Pluto+ RX2 SMA jack.

## PCB-derived geometry

All positions are transformed directly from the current KiCad board:

| Feature | Case-local position, mm |
|---|---|
| PCB outline | 90 x 65 |
| Mounting holes | (-40,-27.5), (40,-27.5), (-40,27.5), (40,27.5) |
| North SMA centers | x = -30,-15,0,15,30; y = 32.5 |
| West/east SMA centers | x = -45/+45; y = 4.5,-13.5 |
| USB-C mouth | x = 0; y = -32.5 |
| J11 SWD | (-21,-23.5) |
| J12 bench power | (-11,-24.5) |

The PCB bottom is 7.80 mm above the case exterior floor. This leaves 5.40 mm
above the 2.40 mm floor for trimmed through-hole tails. The SMA RF centerline
is 19.70 mm above the case floor, and the seam is placed on that centerline.
The inside of the lid is 1.50 mm above the SMA's specified 13.80 mm top-side
envelope.

The case is approximately 96.8 x 71.8 x 27.1 mm. The SMA cable-access opening
flares from 10.2 mm at the board side to 12.0 mm at the outside wall. Measure
the coupling nut on the intended SMA cable; increase
`sma_opening_inner_d`/`sma_opening_outer_d` if it exceeds these clearances.

The enlarged lid markings are `A1` through `A8`; only the new enclosure
revision uses those labels. The five north labels remain at x = -30, -15, 0,
15, 30 mm and the four side labels retain their original connector-relative
orientation. A conservative source assertion keeps the north clip edge at
least 1.0 mm from the label envelope. The clip tail also remains at least
1.0 mm east of the SWD/5V service-opening envelope, preserving lid removal
and service access.

## Export

Run from `projects/pluto-rx2-8way-v5`:

```sh
mkdir -p 06_build/mechanical/pluto-rx2-8way-case
openscad -o 06_build/mechanical/pluto-rx2-8way-case/base.stl -D 'part="base"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/lid.stl -D 'part="lid"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/insert_coupon.stl -D 'part="insert_coupon"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/rx2_antenna_clip.stl -D 'part="rx2_antenna_clip"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/rx2_clip_fit_coupon.stl -D 'part="rx2_clip_fit_coupon"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/assembled-case.stl -D 'part="installed_case"' -D 'show_reference_board=false' 03_src/mechanical/pluto_rx2_8way_case.scad
```

`lid.stl` is already rotated into its support-free print orientation. The RX2
clip and both coupons export exterior/label face up with a broad flat build
face; do not rotate them. To view the exploded assembly in OpenSCAD, open the
source without a `part` override. `assembled-case.stl` is not a printable part;
it is the fixed, installed-orientation enclosure-only subject used by exact
collision verification and includes the installed clip but no antenna/cable
witness.

## Print

- Material: PETG preferred for toughness; PLA is suitable for bench use away
  from hot equipment and direct sun.
- Layer height: 0.20 mm.
- Walls: 4 perimeters.
- Top/bottom: at least 5 layers.
- Infill: 25-35%; use 5 solid modifier layers around insert bosses if the
  slicer supports it.
- Supports: off for the base, lid, both coupons, and RX2 antenna clip.
- Orientation: use the exported orientation without rotation.
- Compensate elephant foot if the lid's exterior face becomes tight at the
  perimeter.

The RX2 clip grows only vertical walls and 45-degree snap lips from its flat
plate; the cable path is open from above and contains no trapped support. The
lid prints exterior-face down, so its two reinforced insert bosses and
top-facing insert recesses grow upward in print orientation.

The USB opening has 45-degree shoulders and only a 4 mm bridge at its crown.
The lid's screw counterbores have a short 1.4 mm radial bridge at their seat;
both are intentional support-free features.

## Assembly

1. Print and use both coupons. The current production insert pocket is
   4.25 mm; revise and re-export the base **and lid** if a changed printer
   process needs another size. Select an antenna clip station from the real
   body; do not assume the 10.0 mm candidate.
2. Press four inserts squarely into the base with a vise or arbor/drill press.
   Support the floor directly beneath each boss and stop when the flange is
   seated in its recess. Do not pull an insert into place with a screw.
3. With the lid removed and its inside facing up, press two more of the **same
   E-Z LOK inserts** squarely into the two flared lid bosses. Support the roof
   immediately around each boss. Stop with both flanges seated; do not melt or
   screw-pull the inserts into place.
4. Place the separate clip on the lid exterior and install two M3 x 8
   socket-head screws. The shallow head recesses locate rather than bury the
   heads. Tighten only until the clip cannot rotate; the modeled stack leaves
   4.175 mm engagement and 0.600 mm nominal tip clearance.
5. Trim all through-hole leads. None may project more than 4.5 mm below the
   PCB; aim for 2 mm or less.
6. Set the unpowered PCB on the four plastic boss rims. Confirm every SMA body
   sits freely in its lower half-opening and USB-C is centered in its arch.
7. Fit the lid. Its four columns should land around the PCB mounting holes,
   not on parts or solder joints. They have 0.15 mm nominal clearance above
   the PCB to avoid bending it. The inner alignment lip should enter the lid
   without force.
8. Install four M3 x 20 socket-head screws. Tighten in a cross pattern only
   until the wall seam closes. The wall seam sets the stack height; do not
   crush it in an attempt to eliminate the deliberate column clearance.
9. Snap the straight 14 mm-or-longer zone of the reference antenna body into
   both open-top stations. Mate its pigtail at the south end, lay the cable in
   the 15 mm-radius guide, and snap it into the post-bend strain relief. The
   antenna body must remain supported if the Pluto end is disconnected.
10. Mate each intended SMA cable and the USB-C cable before powering the board.
   Enlarge a parameter and reprint if a plug housing rubs; do not force a
   connector against the PCB solder joints.

This enclosure is ventilated through its connector and service openings. It
is not weatherproof or RF-shielding. The RX2 clip is only for the lightweight
candidate antenna and RG316-class pigtail shown; secure heavier coax
independently when the board is used outside a bench setup.

## Reusable skill canary

`enclosure.yaml` binds the exact hand-tuned SCAD above as the authored CAD
authority for the shared `pcb-enclosure` skill. The skill copies those bytes
unchanged, exports every declared printable part, and binds the resulting
meshes and the fixed `installed_case` collision subject to the sealed PCB/STEP
subject. The PCB release manifest is bound separately so the dependency is the
exact sealed v0.2.1 archive rather than a version label alone. The built-in
generic enclosure engine is not used for this design.

Run from the repository root:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/extract_board_interface.py \
  projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/source/pluto_rx2_8way_v5.kicad_pcb \
  -o projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/board-interface.json \
  --access-ref J1 --access-ref J2 --access-ref J3 --access-ref J4 \
  --access-ref J5 --access-ref J6 --access-ref J7 --access-ref J8 \
  --access-ref J9 --access-ref J10 --access-ref J11 --access-ref J12

/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml \
  --root projects/pluto-rx2-8way-v5 \
  --build-dir projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell

/usr/bin/python3 skills/pcb-enclosure/scripts/inspect_step.py \
  projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/3d/pluto_rx2_8way_v5.step \
  --interface projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/board-interface.json \
  --output projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-inspection.json \
  --component-mesh projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-components.stl

"$CADQUERY_PYTHON" skills/pcb-enclosure/scripts/build_collision.py \
  --step projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/3d/pluto_rx2_8way_v5.step \
  --step-inspection projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-inspection.json \
  --component-mesh projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-components.stl \
  --generation projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/generation.json \
  --assembled-case-mesh projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/assembled-case.stl \
  --board-bottom-z-mm 7.8 \
  --output projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/clearance-intersection.stl \
  --report projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/collision.json

/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure.py \
  projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml \
  --root projects/pluto-rx2-8way-v5 \
  --build-dir projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell \
  --step-inspection projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-inspection.json \
  --collision-mesh projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/clearance-intersection.stl \
  --collision-report projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/collision.json \
  --report projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/verification.json \
  --target cad

/usr/bin/python3 skills/pcb-enclosure/scripts/render_enclosure.py \
  projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/enclosure.scad \
  --output projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/assembly.png \
  --size 1800,1300

/usr/bin/python3 skills/pcb-enclosure/scripts/package_enclosure.py \
  projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml \
  --root projects/pluto-rx2-8way-v5 \
  --build-dir projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell \
  --output projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/pluto-rx2-8way-v5-enclosure-pcb-v0.2.1-rx2-clip-cad-ready.zip
```

`CADQUERY_PYTHON` must name a Python environment containing CadQuery/OCP. The
STEP occurrence inventory covers every modeled footprint, and the exact BRep
collision run currently returns an empty intersection for the generated,
proven `installed_case`. Without that backend or its bound receipts, the
verifier returns 2/`INCOMPLETE` rather than guessing. Physical fit still needs
the printed coupon, board drop-in, lid closure, and all cable-mating checks;
neither an OpenSCAD render nor a watertight STL promotes those claims.
