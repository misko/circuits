# Pluto RX2 8-way v5 printable enclosure

This is a support-conscious split enclosure for the exact 90 × 65 × 1.6 mm
`pluto-rx2-8way-v5` PCB release `v0.2.1-2026-08-14`. It preserves access to
all nine right-angle SMA jacks, USB-C power, and the J11/J12 top service bay.
The connector-relative lid labels are the larger `A1` through `A8` markings.

The PCB and shell now use **independent fasteners**. Four M3 × 6 screws retain
the PCB directly to its four base standoffs. Four different M3 × 6 screws in
external corner lugs close the lid to tall base posts. Removing the lid cannot
release the PCB or leave it free to move inside the powered enclosure.

The revised base is an **open support deck**, not a lower shell. It has a flat
2.40 mm printable foundation, four PCB support/insert pillars, and four
independent case posts, but no surrounding sidewall or alignment lip. This
removes the predecessor load path that allowed the base perimeter to reach the
SMA bodies before the PCB seated on its intended supports.

This revision adds a **separate, closed-top, bottom-loaded RX2/reference
antenna adapter**. Here, “top” means the exterior/top side of the PCB
enclosure. The complete right-angle antenna already has its cable attached;
the cable is not threaded through a closed hole. Instead, the adapter is
lowered over the complete assembly. The antenna and cable translate upward
through one 58 × 31 mm rounded-rectangular underside opening. A bottom-open
D10.8 U-arch in the adapter's south wall clears the complete D10 lower antenna
body—not merely the cable—so the already-wired assembly can slide into place
without threading. In service the cable continues straight south (`-Y`) and
horizontally on the exterior.

The PCB lid below the adapter remains closed except for the two fastener
stacks. There is no antenna/cable lid pass-through, hidden throat, internal
cable run, S-bend, or snap geometry.

Two M3 × 8 socket-head screws attach the adapter to two E-Z LOK inserts in
reinforced lid bosses. The upright aperture fixes translation, two roof-hung
rails key the horizontal D10 candidate branch, and the south full-body U-arch
fixes its exit axis. A short open-bottom compliant key narrows only a 4 mm
section near the antenna elbow/tongue from the rigid 10.8 mm rail gap to
9.75 mm. Its 11.75 mm mouth and 1.0 mm lead-in preserve slide-in loading. The
lid becomes the cavity floor only after the adapter seats. This topology
captures the candidate against lift and gross rotation without loading a
Pluto+ SMA connector.

## Honest status

This design is **`INCOMPLETE`**, not `PRINT_VERIFIED`. User photographs show
that the predecessor base bore on SMA bodies and that the predecessor antenna
adapter was loose. The revised pillar-only base and localized key have not yet
been printed. The supplied STL is authoritative evidence for a flexible
holder's clearance concept, not for the antenna itself. The modeled D10/D8.75
antenna and D2.50 cable are conservative candidate witnesses. Automated
collision and insertion-path checks cannot qualify physical retention,
rattle, PCB seating, printer-process fit, or the unmeasured cable termination.

Production requires one authoritative antenna/cable profile from calipers or
a dimensioned vendor drawing:

- horizontal branch OD and shoulder-to-upright-axis length;
- lower upright OD, taper/shoulder, upper upright OD, and usable length;
- elbow/fillet maximum envelope;
- attached cable OD, termination/ferrule envelope, and exit direction;
- any external bend-radius and strain-relief requirement after the U-channel.

`rx2_antenna_fit_gauge.stl` provides actual open-bottom channel gaps of 9.50,
9.75, 10.00, and 10.25 mm with the same 11.75 mm mouth and 1.0 mm lead-in.
It can select a printer/material-specific snug gap only; it cannot qualify the
complete L profile, key length, elbow placement, or attached cable.

## Supplied-holder evidence

The original user files are preserved without modification in `reference/`:

- `user-antenna-holder-reference.stl`, SHA-256
  `a1e74e1611c6b9027d5c63d88bc9293ca1ad833619e40cb52d8556bd1cd1030f`,
  14,303,684 bytes;
- `user-clearance-reference.png`, SHA-256
  `fa11c8a1376bdc0d80fc2e80a17872a27423fed0575a5d7faea16b94124b4486`,
  53,857 bytes.

`reference/antenna-holder-measurement.json` binds the exact files and the
measurement/interpretation method. The STL is one watertight manifold holder
with five stations at 23.75 mm pitch. Each station has a bottom-open/outward
D9.75 U-path, a D9.75 lower vertical grip, a D9.75→D8.75 taper, a D8.75 top
throat, and a D19.75 four-petal split collar. The 0.40 mm diagonal slots prove
that those voids rely on flex. They must not be copied as rigid D10 cavities.

The rigid loading path therefore keeps 0.40 mm radial clearance around the
conservative D10 lower L envelope. Only the short roof-hung key copies the
holder-evidenced D9.75 grip gap, D11.75 mouth, and R1 lead-in. That key is
deliberately compliant and has 0.125 mm nominal radial overlap with the D10
candidate witness. D9.75/D8.75 remain holder-void evidence, not claimed
antenna measurements; the rigid design does not copy the D8.75 top throat.

## Adapter geometry and loading path

| Check | Value / assertion |
|---|---:|
| Adapter envelope | 64.0 × 37.0 × 13.6 mm |
| Perimeter wall / closed roof | 3.0 / 3.0 mm |
| Underside relief | 58.0 × 31.0 mm, R1.5; x ±29, y -10…21 |
| Candidate horizontal/lower-upright OD | 10.0 / 10.0 mm |
| Candidate taper / upper upright | D10→D8.75 at z20…30 / D8.75 |
| Rigid radial clearance | 0.40 mm; D10.8 rail gap/aperture |
| Roof-hung locator rails | 2.0 mm thick; z1.2…10.6; y -2…18 |
| Localized compliant key | 9.75 mm gap; 11.75 mm open mouth; R1 lead; 4.0 mm candidate length |
| Key candidate overlap | 0.125 mm radial against the conservative D10 witness; physical test required |
| Fit coupon actual gaps | 9.50 / 9.75 / 10.00 / 10.25 mm |
| Body-to-lid / body-to-roof gaps | 0.20 / 0.40 mm |
| Upright aperture north extent / wall | y21.9 / 2.1 mm |
| Cable witness | D2.50, straight south, center z5.20 above lid |
| Open-bottom full-antenna U-arch | D10.80; 0.40 mm radial clearance around the D10 body |
| Cable clearance within arch | 4.15 mm radial around the D2.50 witness |
| Exterior entry transition | 1.0 mm long, constant D10.80 profile |
| U-arch crown / roof ligament | z10.60 / 3.00 mm |
| Vertical insertion sweep | 45.0 mm, complete antenna+cable assembly |
| Mount-to-service-opening gap | 4.30 mm |
| U-arch to service opening | 4.30 mm in Y |
| Mount-to-north-label nominal gap | 1.10 mm |

The rectangular relief and D10.8 upright aperture overlap: the relief reaches
y=21.0, while the aperture continues to y=21.9 from z=0 through the roof.
Thus the full D10 upright footprint reaches the underside with no hidden
undercut. Roof-hung rails leave the D10.8 vertical path open below them.

The deterministic `part="insertion_sweep_vs_rigid_mount"` selector sweeps each
convex antenna/cable primitive through the full 45 mm straight-Z insertion
path and intersects that swept volume with the rigid adapter geometry. An
empty export is required. The separate `part="antenna_vs_compliant_key"`
selector must be solid: it proves the declared localized grip overlap without
mislabeling that interference as rigid clearance. Printed insertion and
retention still remain required.

Access-zone checks use conservative configured plug envelopes:

- the north SMA plug envelope remains 3.5 mm from the adapter;
- each east/west SMA plug envelope remains 8.0 mm from it;
- the cable's lower surface is 14.05 mm above the USB-C arch top where their
  plan views cross;
- the D10.80 full-antenna U-arch stays 4.30 mm north of the J11/J12 service-opening envelope;
- the 45 mm cable witness extends 9.1 mm beyond the south case edge and never
  enters the PCB enclosure.

## Insert authority and screw stack

Use only the coupon-qualified E-Z LOK E-Z Press flanged M3-0.5 family
`260-M3-BR` or dimensionally equivalent `260-M3-CR`:

- 4.216 mm nominal body diameter;
- 5.537 mm flange diameter;
- 4.775 mm overall length;
- **4.25 mm production pilot**, physically selected as the smallest reliable
  printed fit;
- 6.10 × 0.80 mm flange recess.

Do not substitute a generic heat-set insert. These inserts are cold-pressed.
Four PCB standoffs and four independent case posts in the base, plus the two
reinforced antenna-adapter bosses in the lid, preserve the same 4.25 mm pilot
authority.

| Independent PCB/case fastener dimension | Value |
|---|---:|
| PCB screws | 4 × M3 × 6 socket-head cap |
| PCB insert engagement / tip clearance | 4.400 / 0.375 mm |
| Case screws | 4 × M3 × 6 socket-head cap |
| Case axes | (±49.0, ±36.5) mm, outside PCB corners |
| Base case post / lid lug diameters | 9.0 / 14.0 mm |
| Post-to-PCB-corner clearance | 1.157 mm |
| Case insert engagement / tip clearance | 4.400 / 0.375 mm |
| Lid screw-head recess | 0.800 mm |
| Lid wall around D9.4 post sleeve | 2.300 mm radial |

The four board inserts enter the standoffs from above and remain below the
PCB. The PCB screws bear directly on the board at H1–H4. The four case inserts
enter the tall base posts from above; the lid's D14 external lugs slide over
those posts and carry only shell-closing load. No lid column bears on the PCB,
and none of the eight PCB/case screws shares an axis or stack.

| RX2 adapter fastener dimension | Value |
|---|---:|
| Screws | 2 × M3 × 8 socket-head cap |
| Screw-head bearing plane above lid | 2.700 mm |
| Insert engagement | 4.175 mm |
| Screw-tip clearance | 0.600 mm |
| Roof skin above blind insert pilot | 0.825 mm |
| Lid-boss wall at flange recess | 1.450 mm |
| Adapter screw-column radial wall | 2.850 mm (D12 around D6.3 well) |

Inserts enter from the lid underside, so upward load seats each flange into a
reinforced 9-to-12 mm boss. The D12 adapter columns carry screw-head load to
the lid. Do not use the antenna cable as a lifting handle.

## PCB-derived enclosure geometry

| Feature | Case-local position, mm |
|---|---|
| PCB outline | 90 × 65 |
| Mounting holes | (-40,-27.5), (40,-27.5), (-40,27.5), (40,27.5) |
| North SMA centers | x=-30,-15,0,15,30; y=32.5 |
| West/east SMA centers | x=-45/+45; y=4.5,-13.5 |
| USB-C mouth | x=0; y=-32.5 |
| J11 SWD / J12 bench power | (-21,-23.5) / (-11,-24.5) |

The PCB bottom is 7.80 mm above the case exterior floor. The SMA RF centerline
and wall seam are at Z=19.70 mm. The inside lid face is Z=24.70 mm and the
case top is Z=27.10 mm. The base has no lower perimeter wall: its 96.8 × 71.8
mm foundation is open on every side above Z=2.40 mm. Four external closure
posts/lugs make the total envelope 112.0 × 87.0 mm. The lid supplies the upper
connector skirt and the closed adapter sits on its exterior top plane.

## Print and assembly

Print PETG at 0.20 mm layers with a 0.4 mm nozzle, four perimeters, at least
five top/bottom layers, and 25–35% infill. Disable supports for all five parts.
`base.stl` prints foundation-down; the PCB pillars and case posts rise directly
from the deck with every side open.
`lid.stl` prints exterior-face-down. `rx2_antenna_mount.stl` prints its closed
top face on the bed, so the rectangular underside cavity, roof-hung rails,
screw wells, and bottom-open full-body U-arch grow upward without trapped support.

Assembly sequence:

1. Reconfirm the 4.25 mm insert coupon on the production printer/material.
   Starting with the loosest antenna channel coupon, select a snug gap without
   forcing or marring the real antenna; do not assume 9.75 mm will be correct
   for every printer/material.
2. Press four board inserts into the short base standoffs and four case inserts
   into the tall external base posts, all from above. Press the two antenna
   adapter inserts into the lid underside bosses. Support each feature
   directly; do not melt or screw-pull.
3. Install the unpowered PCB and retain it independently with four M3 × 6
   screws at H1–H4. Before fitting the lid, prove the PCB is simultaneously
   seated on all four supports, cannot rock, and has visible clearance around
   every SMA/USB-C body. Verify it remains secure with all case screws absent.
4. Lower the lid over the four base posts and close it with the separate four
   M3 × 6 case screws. Confirm no case screw loads or contacts the PCB, then
   complete all-interface mating checks.
5. Place the complete pre-wired L antenna on the closed lid exterior: upright
   at `(0,16.5)`, horizontal branch toward south, attached cable continuing
   straight south. Nothing passes through the lid.
6. Hold the adapter above the assembly. Align the upright with the D10.8 top
   aperture and the complete D10 lower antenna body with the bottom-open
   D10.8 south U-arch.
7. Lower the adapter straight down. The entire L assembly enters the one
   rectangular underside opening; the antenna body and attached cable rise
   through the full-body U-arch from below.
   **Do not thread the cable through any bore.**
8. Confirm the adapter seats flat, antenna and cable are free in the U-arch, service bay
   remains usable, and antenna/cable are not pinched. Install the two M3 × 8
   screws alternately and only snug them enough to prevent adapter motion.

For removal, disconnect power, remove both M3 × 8 screws, and lift the adapter
straight upward while supporting the antenna. The pre-wired assembly exits the
same open underside/U-channel path. Do not pull it out by the cable.

The enclosure is not weatherproof or RF-shielding.

## Reproducible skill pipeline

From the repository root:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml \
  --root projects/pluto-rx2-8way-v5 \
  --build-dir projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell

uv run --offline --with cadquery python \
  skills/pcb-enclosure/scripts/inspect_step.py \
  projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/3d/pluto_rx2_8way_v5.step \
  --interface projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/board-interface.json \
  --output projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-inspection.json \
  --component-mesh projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-components.stl

uv run --offline --with cadquery python \
  skills/pcb-enclosure/scripts/build_collision.py \
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

uv run --offline --with cadquery python \
  projects/pluto-rx2-8way-v5/03_src/mechanical/verify_antenna_clearance.py \
  --config projects/pluto-rx2-8way-v5/03_src/mechanical/enclosure.yaml \
  --generation projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/generation.json \
  --scad projects/pluto-rx2-8way-v5/03_src/mechanical/pluto_rx2_8way_case.scad \
  --step projects/pluto-rx2-8way-v5/07_releases/v0.2.1-2026-08-14/3d/pluto_rx2_8way_v5.step \
  --step-inspection projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/step-inspection.json \
  --holder-stl projects/pluto-rx2-8way-v5/03_src/mechanical/reference/user-antenna-holder-reference.stl \
  --holder-png projects/pluto-rx2-8way-v5/03_src/mechanical/reference/user-clearance-reference.png \
  --holder-measurement projects/pluto-rx2-8way-v5/03_src/mechanical/reference/antenna-holder-measurement.json \
  --candidate-contract projects/pluto-rx2-8way-v5/03_src/mechanical/reference/antenna-adapter-candidate-contract.json \
  --build-dir projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell \
  --report projects/pluto-rx2-8way-v5/06_build/mechanical/pluto-split-shell/antenna-clearance.json
```

The generic verifier binds the sealed PCB/STEP and exact installed-case
collision evidence. `antenna-clearance.json` separately binds the non-printable
antenna reference, pillar-only base, full-body U-arch, rigid continuous
insertion sweep, declared compliant-key overlap, exact STEP/base/component
checks, board drop-in checkpoints, and access-zone calculations. A passing CAD pipeline does not promote
the accessory above `INCOMPLETE` until the missing antenna/cable and physical
fit evidence exists.

The immutable enclosure release carries the generic shell receipt only as a
subordinate `CAD_READY` result. Its top-level manifest remains `INCOMPLETE`
and includes the raw holder evidence, candidate contract, non-printable
antenna/cable witnesses, and accessory receipt. Do not use the generic
packager alone because its schema cannot express that accessory qualification
boundary.
