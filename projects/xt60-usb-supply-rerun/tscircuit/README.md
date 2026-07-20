# tscircuit render — xt60-usb-supply-rerun

An **alternate, non-authoritative** tscircuit design of this board (51 parts).
KiCad (`../04_kicad/xt60-usb-supply.kicad_pcb`) remains the fab-of-record; this folder is a
second-opinion render + verification stack. Format + rationale (canon S-DSL):
`skills/kicad-pcb/references/tscircuit-folder.md`.

Status: **RENDERED** — node-for-node schematic parity achieved.

## Parity headline (Phase-1, ADR-0001 schematic bridge)

**51/51 components · 28/28 nets · 151/151 logical nodes · NODE-FOR-NODE PARITY: YES**
(after one normalization: KiCad `5V_A`/`5V_C` → tscircuit `N5V_A`/`N5V_C`, leading-digit rule.)

- ERC on the tscircuit `kicad_sch`: 635 (72 error / 563 warning) — all parametric
  schematic-render artifacts (off-grid wires, generated-symbol issues), zero connectivity faults.
- PCB DRC-on-export: 217 + 118 unconnected — parametric/placement study; autorouter skipped.
- **Connector footprinter gap:** the specialty connectors (XT60 J1, USB-A J2/J3/J4, USB-C J5),
  the SY8368 QFN (U1/U2), FXL0630 inductors (L1/L2), TO-252 (Q1), polymer cap (CB1/CB2), NANO2
  fuse (F1) and M3 holes (H1–H4) are **absent from footprinter** and were hand-authored as
  `<footprint>` children — all expressible, pad- and name-for-name. See `verification/notes.md`.

Regenerate: see `GENERATE.md` (`bash <kicad-pcb skill>/scripts/gen_tscircuit.sh <project_dir>`).
