# Journal — 03 schematic (usb-hub-3s-v2)

## 2026-07-22 — start
- did: Sourcing spike returned TPS25740A (C544309) — a pure PD-source PHY that
  REFUTES v1 ADR-0004's "no simple fixed-5V/5A source exists". D-ESC: VQFN-24
  0.5mm forces jlc_4layer_advanced (only advanced part on the board). Wrote
  ADRs 0001/0004-v2/0010/0011 + ARCHITECTURE.md. TPS25740A part.yaml built from
  a fresh datasheet read (SLVSDG8B) — key correction: EN9V active-LOW, must tie
  HIGH to DVDD for 5V-only.
- result: architecture fixed; parts staged.
- next: author the TSX (reuse input + 2 bucks + USB-A; new PD cell).

## 2026-07-22 — iterate 1 (build the TSX)
- did: Authored 03_tscircuit/src/usb_hub_3s_v2.tsx — parameterized <Buck> cell
  instanced twice (A→5VA, C→5VC), input protection + 3 USB-A ports carried from
  v1, new TPS25740A PD cell (back-to-back path FETs, straps, discharge, ESD, J5).
  Wrote manifest.yaml (112 components) + parity_padmap.txt.
- result: tsx_preflight (S-COUNT) PASS after adding padmap; tsci build = 112
  components, circuit.json produced.
- next: run the bridge + gates.

## 2026-07-22 — finish (SCHEMATIC GATE GREEN)
- did: Ran gen_tscircuit.sh bridge (circuit.json → converter kicad_sch → ERC →
  parity), count_parity, E-INV, E-ADR.
- result: **ALL GREEN, measured:**
  - E-TOPO: 2 rails BUCK, derived trunk 6.8 A @ 9 V (vs v1 ~16 A). PASS.
  - S-COUNT preflight: all multi-pin pads tsx-safe/mapped. PASS.
  - tsci build: 112 components (103 with FPID), 375 pins.
  - converter: 112 components, 479 wires, 0 segs dropped cross-net.
  - **ERC: 0 errors** / 869 warnings (all baselined classes: 548
    endpoint_off_grid, 215 lib_symbol_issues, 103 footprint_link_issues, 2
    unconnected_wire_endpoint, 1 multiple_net_names — cosmetic, converter render).
  - **count_parity: manifest 112 == circuit.json 112 == kicad_sch 112.** PASS.
  - **E-INV: 15/15 invariants hold** against the exported netlist (incl.
    INV-D1-PLACEMENT, INV-PD-EN9V-5V-ONLY the strap trap, INV-PD-BACKTOBACK).
  - **E-ADR: every protection/topology ADR cited.** PASS.
- next: PLANNED HANDOFF at the schematic gate (see handoff.md). Routing is the
  next session — v2 routes far easier than v1 (two clean buck cells + a
  separable PD cell; no buck-boost hot loop).
