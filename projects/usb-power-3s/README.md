# usb-power-3s

3S-LiPo (XT60) → USB power board: **3× USB-A at 2.5 A** each and **1× USB-C at
6 A** (5 V, no PD — fixed Rp advertises 3 A; copper sized for 6 A). No MCU, no
firmware; all protection is hardware.

- Input: 9.0–12.6 V via XT60PW-M + 15 A ATO blade fuse
- Front end: LM74800-Q1 ideal-diode controller + back-to-back CSD18543Q3A
  (reverse polarity, UVLO 9.33 V on / OV 15.25 V off)
- Two synchronous bucks (LM5145, 606 kHz): 5.08 V rails — one direct to
  USB-C, one feeding 3× TPS2557 (2.51 A per-port limit) to the USB-A jacks
- 100×60 mm, 4-layer (sig / GND / power planes / GND+escape)

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); design math in
[docs/DETAIL_DESIGN.md](docs/DETAIL_DESIGN.md); decisions in
[docs/decisions/](docs/decisions/).

Everything in `kicad/` is GENERATED — edit `src/` and run
`bash src/rebuild_all.sh` (regenerates schematic, netlist, board, imports the
KRT routing, stitches/fills, and runs the full DRC gate; it must end
`violations: 0 / unconnected: 0`).

**Ordering**: JLCPCB 4-layer with the ADVANCED (small-via) option — the VQFN
fanout uses 0.25/0.15 vias. USB-A jacks (CNCTech 1001-011-01101) are not in
the JLC catalog: order from Digi-Key (3064739) and hand-solder. See the
`releases/` directory for the exact ordered packages.
