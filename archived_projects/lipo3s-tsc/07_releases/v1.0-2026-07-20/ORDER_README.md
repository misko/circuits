# lipo3s-tsc v1.0 — JLCPCB order guide

**This board is the tscircuit-authored TWIN of usb-power-3s v1.3** (ADR-0001
capstone). It is the SAME board: 3S LiPo (9.0–12.6 V) XT60 input → 3× USB-A @2.5 A
(5 V_A rail) + 1× USB-C @6 A (5 V_C rail), 100 parts, 4-layer. It was authored in
tscircuit/TSX (`../../tscircuit/src/lipo3s_tsc.tsx`), converted to a native KiCad
schematic, and built by the usb-power-3s KiCad backend — **node-for-node identical
to the sealed usb-power-3s board** (board-netlist parity 0, 303/303 nodes; source
git_sha d8992b8). Fab-of-record stays KiCad (canon S-DSL).

## Upload
- **PCB order:** `usb_power_3s_gerbers.zip` (13 files: 4 copper + F/B mask + F/B
  silk + F/B paste + Edge_Cuts + PTH/NPTH drills). 4-layer.
- **Assembly BOM:** `bom.csv` (Comment, Designator, Footprint, MPN, LCSC).
- **Assembly CPL:** `cpl.csv`.

## Order settings (must match)
- **4 layers.**
- **ADVANCED small-via option REQUIRED** — the board uses 0.25/0.15 mm fanout
  vias; without the advanced option JLC rejects or drifts the holes.
- Confirm rotations in the JLC 3D preview (the exporter auto-corrects via
  `jlc_rotations_db.csv`; SON/QFN/VQFN families were rot-corrected +270°).

## Not assembled (hand-solder / user-supplied)
- **J2, J3, J4** — USB-A jacks (CNCTech 1001-011-01101, Digi-Key 3064739). Not in
  the JLC catalog: mark **Do Not Place**, hand-solder. Uncoded in `bom.csv` by design.
- **F1** — 15 A ATO fuse cartridge is user-supplied (the holder `178.6165.0002` /
  C207061 IS assembled).

## Verification (this release, verification/)
- **GATE 1** `gate1_parity.txt` — converter kicad_sch ERC 0 + netlist parity 0
  node-for-node vs the sealed usb-power-3s schematic.
- **GATE 2** `gate2_board_parity.txt` + `drc.json` — backend DRC 0/0/0 + board
  parity 0 (303/303 nodes) vs the sealed usb-power-3s board.
- `policy_audit.md` — FULL, zero FAIL. `audit.txt` — placement/polarity invariants PASS.
- `twin_report.csv` + `twin_*.png` — JLC digital twin exit 0. The 14 PAD-GEOM /
  7 PAD-MISMATCH adjudications are KiCad-standard-land vs JLC-CAD deltas that are
  **identical on the sealed usb-power-3s v1.3 board** (proven: the current twin on
  that board flags the same 14 refs) — footprint-inherited, not authoring defects.
  Still eyeball LA1/LB1 (no EasyEDA CAD) and CE1/D1-D3/F1 polarity at order time.
- `stock_check.csv` — every coded line ≥5× qty at order-prep time; re-check on order day.

## First-power ritual (when boards arrive)
Before any real source: multimeter the XT60 blades vs board nets — pad 1 = "−"
(GND), pad 2 = "+" (VBATT_RAW) — and continuity to the fuse / LM74800 front-end.
Polarity bugs are electrically self-consistent and invisible to every upstream check.
