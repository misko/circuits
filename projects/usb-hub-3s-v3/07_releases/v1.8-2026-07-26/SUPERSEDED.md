# SUPERSEDED — v1.8-2026-07-26 · **DO-NOT-ORDER**

**Order from `07_releases/v1.9-2026-07-27/` instead.**

## THIS IS A BOARD DEFECT. THE GERBERS IN THIS DIRECTORY HAVE NO COPPER POUR.

**44287.91 mm2 of copper is missing** from `fab/usb_hub_3s_v2_gerbers.zip` — on
**all four layers**. There is no GND plane, no VIN plane, and no
5VA / 5VC / VBUS / switch-node island. A board fabricated from this zip carries
its 7 A battery trunk and its 6 A and 5 A rails on nothing but the handful of
thin routed stubs that were never meant to carry them, and has no return path.

**This applies equally to `v1.6-2026-07-26` and `v1.7-2026-07-26`**, whose fab
payloads are byte-identical to this one. Those two directories already carry
their one permitted `SUPERSEDED.md` (v1.6 -> v1.7 -> v1.8 -> here), and
`07_releases/contracts.md` allows a sealed release exactly one added file and
"nothing else, ever" — so this file is the DO-NOT-ORDER notice for all three.
The live beacon is `01_docs/STATUS.md`.

## Measured

`skills/jlcpcb-fab/scripts/fab_payload_census.py` (canon **F-POUR** / **F-IDENT**)
opens the shipped zip and grades it against the board in `source/`. Run against
this directory on 2026-07-27:

```
FAIL F-POUR B.Cu:   board declares 14 zone(s) — the SHIPPED gerber has 0 G36 regions
FAIL F-POUR F.Cu:   board declares 20 zone(s) — the SHIPPED gerber has 0 G36 regions
FAIL F-POUR In1.Cu: board declares  1 zone(s) — the SHIPPED gerber has 0 G36 regions
FAIL F-POUR In2.Cu: board declares  1 zone(s) — the SHIPPED gerber has 0 G36 regions
FAIL F-IDENT: In2.Cu (Copper,L3,Inr) and In1.Cu (Copper,L2,Inr) are BYTE-IDENTICAL
      at 18921B AND CARRY 0 G36 REGIONS
F-PAYLOAD FAIL: 5 finding(s), 0 ok
```

The same gate on v1.9: **`F-PAYLOAD OK: 5 check(s) passed`** — 17 / 87 / 1 / 1
G36 regions on B.Cu / F.Cu / In1.Cu / In2.Cu, all four copper gerbers distinct.
Both runs are archived side by side in
`v1.9-2026-07-27/verification/fab_payload_census.txt`.

The crudest version of the same fact: this directory's gerber zip is **88 692
bytes**; v1.9's is **394 534 bytes**. The difference is the copper.

## Root cause

`03_src/post_stitch_fixes.py` section 6, added in v1.6, unfills the copper zones
so it can place vias — and never refills before its own save. That script holds
the **LAST** save in the build pipeline, so the refill guard inside the stitch
driver ran before the save that mattered and guarded nothing.

## Why every gate in this directory says PASS

`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` **refills
the zones IN MEMORY** before it measures. It therefore returns 0 violations /
0 unconnected / 0 parity on a board whose SAVED FILE has no fill. DRC, netlist
parity, the digital twin, the renders, ERC, the assembly battery and the policy
audit were every one of them measuring an in-memory board that was correct,
while the bytes on disk — and the bytes in the zip — were not.

Nothing in this release is retro-edited. Its evidence is a true record of what
those gates reported; the gates were asking the wrong artifact.

## What v1.9 changes

**Only copper.** Netlist parity against this release is **0 differences**
(122 components, 73 nets, 372 nodes, identical) and `fab/cpl.csv` is
**byte-identical**. Placement, connectivity, part selection, rotations and the
CPL datum are exactly what this release sealed.

Two new gates make the class impossible rather than merely detected:

* **M-SHIP read-back** — `route_and_stitch_generic.py verify-fill` reopens the
  saved `.kicad_pcb` **as TEXT** and counts `filled_polygon` blocks. Text rather
  than pcbnew deliberately: pcbnew is the tool whose save behaviour is under
  test, so re-reading through it would share a method with the thing being
  checked (canon M1). Wired into both rebuild scripts.
* **F-PAYLOAD** — `fab_payload_census.py`, above. The only gate downstream of the
  export, which is where this defect lived.

`01_docs/CHANGELOG.md` has the full v1.9 entry.
