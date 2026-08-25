# Pluto RX2 8-way v5 printable enclosure

This is a support-free, two-piece FDM enclosure for the exact 90 x 65 x
1.6 mm `pluto-rx2-8way-v5` PCB. It provides openings for all nine right-angle
SMA jacks, USB-C power, and a shared top service bay for J11 SWD and J12 bench
power. It remains usable when only some SMA positions are populated.

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
pockets, left to right when the recessed labels face you, are 3.85, 3.95,
4.05, and 4.15 mm in the model. Press an insert into the smallest pocket that
accepts it without cracking or visibly whitening the boss. Set
`insert_hole_d` in the SCAD file to that value before exporting the base. Do
not install an insert by melting it with a soldering iron: this insert family
is intended to be cold-pressed.

The flange recess is deliberately 6.10 x 0.80 mm so the PCB rests on a plastic
annulus rather than on the metal flange. Confirm this against one physical
insert before assembling the board.

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

## Export

Run from `projects/pluto-rx2-8way-v5`:

```sh
mkdir -p 06_build/mechanical/pluto-rx2-8way-case
openscad -o 06_build/mechanical/pluto-rx2-8way-case/base.stl -D 'part="base"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/lid.stl -D 'part="lid"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/insert_coupon.stl -D 'part="insert_coupon"' 03_src/mechanical/pluto_rx2_8way_case.scad
openscad -o 06_build/mechanical/pluto-rx2-8way-case/assembled-case.stl -D 'part="installed_case"' -D 'show_reference_board=false' 03_src/mechanical/pluto_rx2_8way_case.scad
```

`lid.stl` is already rotated into its support-free print orientation. To view
the exploded assembly in OpenSCAD, open the source without a `part` override.
`assembled-case.stl` is not a printable part; it is the fixed, installed-
orientation enclosure-only subject used by exact collision verification.

## Print

- Material: PETG preferred for toughness; PLA is suitable for bench use away
  from hot equipment and direct sun.
- Layer height: 0.20 mm.
- Walls: 4 perimeters.
- Top/bottom: at least 5 layers.
- Infill: 25-35%; use 5 solid modifier layers around insert bosses if the
  slicer supports it.
- Supports: off for the base, lid, and insert coupon.
- Orientation: use the exported orientation without rotation.
- Compensate elephant foot if the lid's exterior face becomes tight at the
  perimeter.

The USB opening has 45-degree shoulders and only a 4 mm bridge at its crown.
The lid's screw counterbores have a short 1.4 mm radial bridge at their seat;
both are intentional support-free features.

## Assembly

1. Print and use the insert coupon. Re-export the base if another pocket size
   fits better than the 3.95 mm default.
2. Press four inserts squarely into the base with a vise or arbor/drill press.
   Support the floor directly beneath each boss and stop when the flange is
   seated in its recess. Do not pull an insert into place with a screw.
3. Trim all through-hole leads. None may project more than 4.5 mm below the
   PCB; aim for 2 mm or less.
4. Set the unpowered PCB on the four plastic boss rims. Confirm every SMA body
   sits freely in its lower half-opening and USB-C is centered in its arch.
5. Fit the lid. Its four columns should land around the PCB mounting holes,
   not on parts or solder joints. They have 0.15 mm nominal clearance above
   the PCB to avoid bending it. The inner alignment lip should enter the lid
   without force.
6. Install four M3 x 20 socket-head screws. Tighten in a cross pattern only
   until the wall seam closes. The wall seam sets the stack height; do not
   crush it in an attempt to eliminate the deliberate column clearance.
7. Mate each intended SMA cable and the USB-C cable before powering the board.
   Enlarge a parameter and reprint if a plug housing rubs; do not force a
   connector against the PCB solder joints.

This enclosure is ventilated through its connector and service openings. It
is not weatherproof, RF-shielding, or suitable as a strain-relief point for
heavy coax. Secure coax independently when the board is used outside a bench
setup.

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
  --output projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/pluto-rx2-8way-v5-enclosure-pcb-v0.2.1-cad-ready.zip
```

`CADQUERY_PYTHON` must name a Python environment containing CadQuery/OCP. The
STEP occurrence inventory covers every modeled footprint, and the exact BRep
collision run currently returns an empty intersection for the generated,
proven `installed_case`. Without that backend or its bound receipts, the
verifier returns 2/`INCOMPLETE` rather than guessing. Physical fit still needs
the printed coupon, board drop-in, lid closure, and all cable-mating checks;
neither an OpenSCAD render nor a watertight STL promotes those claims.
