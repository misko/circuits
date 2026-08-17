# Pluto RX2 8-way v5 — hardware design archive

## STOP — DO NOT ORDER THIS ARCHIVE AS-IS

SOURCING: CLEAR
ORDER VERDICT: DO-NOT-ORDER
DESIGN VERDICT: SOUND

This is a hardware-only candidate assembled from source commit
`c9a59c15c31478b623ab9002ca094cbc1d719bb9`. Firmware generation has been
stopped at the user's direction. The PCB and local fabrication evidence are
inspectable here, but autonomous switching is not qualified and this archive
does not authorize fabrication.

Product boundary: one Pluto RX input switched to at most eight 50-ohm SMA
antenna ports. The requested operating range is 100 MHz to 5.9 GHz. Operation
of the Pluto's AD9363 outside its published range by applying an AD9361 profile
is an explicit user-accepted experimental risk, not a guaranteed specification.
The board is USB-C powered only; it carries no USB data.

PCB: 90.1 x 65.1 mm, four copper layers, 1.6 mm nominal, JLCPCB controlled
impedance process. Assembly target: quantity five first articles, top side,
13 BOM rows and 29 placements. All 29 CPL bodies are represented in the 3D
twin. J2-J10 are through-hole SMA connectors intentionally included in the
assembly scope, subject to JLC acceptance of part C429844 and its THT service.

## 1. PCB uploader gate

- Upload `fab/pluto_rx2_8way_v5_gerbers.zip` and select JLC04161H-7628,
  four layers and 1.6 mm finished thickness.
- Request 50-ohm controlled impedance for the 0.295 mm F.Cu traces over the
  solid In1.Cu ground plane, with 0.200 mm coplanar gap and 0.2104 mm prepreg.
  The recorded JLC calculation is 49.9719 ohms; uploader stackup confirmation
  remains mandatory.
- Apply copper-paste fill and copper cap only to the nine 0.45/0.25 mm U1 vias.
  Do not fill/cap the 629 ordinary 0.45/0.20 mm routing and stitching vias.
- Confirm all four copper layers, board outline, PTH/NPTH mapping, solder-mask
  openings and RF launch geometry. Reject unreviewed DFM edits.

## 2. Assembly uploader gate

- Upload `fab/bom.csv` and `fab/cpl.csv` for five top-side assemblies. Require
  exactly 13 BOM rows and 29 resolved placements.
- Save JLC's resolved BOM and compare every code, value, reference group and
  quantity with `verification/bom_echo_gate.txt`. Same-day stock was 13/13;
  catalog availability is not an allocation guarantee.
- Review JLC's actual placement preview for every reference, especially U1
  pin 1, D1 polarity, J1/J11 orientation and all nine edge SMA connectors.
- Obtain explicit acceptance for C429844 and J2-J10 as through-hole assembly.
  If JLC will not assemble them, stop and revise the assembly plan rather than
  silently ordering incomplete boards.

## 3. Functional prerequisites and first article

- Do not claim autonomous operation until a separately requested, reviewed and
  verified controller image exists and is programmed through keyed connector
  J11. The board supplies its own power; a Pi or debug adapter must not source
  power into J11.
- Execute `verification/FIRST_ARTICLE_TEST_PLAN.md`. Full acceptance requires
  electrical, control-timing and VNA evidence from physical first articles.
- Treat 0 dBm as the maximum operating RF input. The +2.5 dBm switch rating is
  an absolute maximum, not an operating target.

## 4. Archive integrity

`MANIFEST.txt`, when generated at seal time, hashes every archived file except
itself and identifies the exact source commit. `source/` includes the KiCad
project, routed board, schematic, rules, exported netlist, authoring TSX and
vendored footprints. `fab/`, `pdf/`, `3d/` and `verification/` retain the
manufacturing and review evidence without relying on the stopped firmware
worktree.
