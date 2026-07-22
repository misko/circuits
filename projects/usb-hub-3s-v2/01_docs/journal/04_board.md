# Journal — usb-hub-3s-v2 board backend (placement/route)

## 2026-07-22 — start (schematic gate → board backend)
- did: Resumed from schematic-gate handoff. Audited the netlist for the hand-written
  KiCad backend and found TWO source defects that blocked/would-corrupt the board:
  1. **9 specialty parts had EMPTY footprints** (C1/C2 polymer, L1/L2 inductor,
     RS1/RS2/RS3 shunt, F1 fuse holder, U1 TPS25740A) — v2's 02_parts/*/part.yaml
     lacked `footprint:` fields (v1's carried them) and 3 part folders did not exist.
     FIX: added `footprint:` to TPS25740ARGER (Texas_RGE0024H_VQFN-24 EP2.7x2.7 ThermalVias)
     + lcsc:C5249699 to 3568; copied v1's proven part.yaml for the shunt(2512)/
     polymer(CP_Elec_6.3x7.7)/inductor(L_Sunlord_MWSA1206S-6R8) folders; copied v1's
     usb_hub_3s.pretty custom-footprint lib into 03_src/lib.
  2. **Layout-mode net merge: BOOT_A absorbed VCC_A** — the converter's default
     `--mode layout` merged buck-A's BOOT_A and VCC_A by wire-endpoint coincidence,
     SHORTING boot diode D3 (both pads on one net) and tying VCC=BOOT. Buck C was
     correct (identical tsx) — a stochastic geometry coincidence, the exact hazard
     v1 avoided with `--mode grid`. FIX: regenerated the converter .kicad_sch with
     `--mode grid` (label-glue, parity-safe by construction).
- result: MEASURED — 112/112 footprints resolved; BOOT_A={C7.1,D3.1,U2.18} and
  VCC_A={C8.1,D3.2,U2.16} now SEPARATE (D3 un-shorted); ERC 0 errors; count_parity
  112==112==112. Schematic gate GREEN and now electrically correct.
- next: This board REQUIRES `--mode grid` (gen_tscircuit.sh defaults to layout and
  re-introduces the merge). Author 03_src/floorplan.yaml (4 self-contained cells),
  generate_rules, route.yaml, grind to DRC 0/0/0.

## 2026-07-22 — placement finish
- did: Authored 03_src/floorplan.yaml (power-hub archetype, 4 self-contained cells
  on a 130x92 4-layer board: In1=GND, In2=VIN). Reused v1's proven LM5116 buck
  geometry TWICE (buck A north, buck C south, identical), v1's USB-A bank shape
  (east column, mouths east), fresh simple PD cell (TPS25740A + back-to-back path
  FETs, no switching). Wrote 03_src/audit_board.py (I-POL/I-PROX/I-EDGE/I-SILK).
  Relocated the two east mounting holes off the 18mm-tall connector column into
  clear board; nudged D1/D2/U12/RS3 out of bbox collisions.
- result: MEASURED — generate_board_generic: 112 placed (37 anchored), 26/26
  orientation asserts PASS, 38 legalized. audit_board: PASS (20 polarity, 21
  proximity, 4 edge, 116 silk). bbox overlaps >0.4mm^2: 0.
- next: generate_rules (netclasses/DRU, advanced tier) BEFORE route-prep; author
  route.yaml; KRT fanout-first; grind to DRC 0/0/0.
