# journal: 03_schematic

## 2026-07-23 — start
- did: authored the board in tscircuit (03_tscircuit/src/crow_mic_pod_v2.tsx):
  35 components — U1 OPA1678 active-balanced driver, MK1 electret, LS1
  transducer + D2/D3 flyback/TVS, D1 ESD, J1 RJ45 custom pinout, 11 R, 10 C,
  7 TP. Vendored 2 footprints (CMT-8504 4-pad, AOM-5024 2-pad) in 03_src/lib.
- result: preflight FAILED first (RJHSE-5384 part.yaml documented SH/NPTH_*
  alphanumeric pins). Fixed by moving shield/post docs out of `pins:` into a
  `mechanical_pads:` block (they float at the pod, ADR-0001) — preflight 0.
- next: run gen_tscircuit bridge → ERC + parity.

## 2026-07-23 — finish (SCHEMATIC GATE GREEN)
- did: ran tsx_preflight → gen_tscircuit.sh → count_parity → netlist export →
  electrical_invariants (E-INV/E-ADR) → power_topology (E-TOPO/E-MARGIN/E-OFF).
- result: ALL GREEN.
  - ERC (converter kicad_sch, severity-all): **0 errors**, 213 warnings all in
    the baselined parametric classes (127 endpoint_off_grid, 51 lib_symbol_issues,
    35 footprint_link_issues) — the exact set the 03_tscircuit contract baselines.
  - FPID resolution: **35/35** components (MK1 no-LCSC resolves via its MPN as
    the supplier handle; J1 via the C99 consign code).
  - count_parity: **0** (circuit.json == kicad_sch == manifest, 35 each).
  - netlist wiring hand-verified node-for-node: canonical rails (N-strip:
    N5V_AUDIO→5V_AUDIO, N5V_BEEP→5V_BEEP), diode flyback polarity (D2.1/D3.1
    cathode→5V_BEEP), ESD channels (D1.3→AUDIO_P, D1.5→AUDIO_N, D1.1/2/4→GND),
    RJ45 custom pinout exact, and BEEP ISOLATION confirmed (5V_BEEP &
    BEEP_SWITCHED_RETURN carry ONLY beep parts — no GND/5V_AUDIO bridge, G8).
  - E-INV: **14 invariants hold**; E-ADR: every protection/topology ADR cited.
  - power-tree: E-TOPO / E-MARGIN / E-OFF all **N-A** (cable-powered, no rails,
    no battery) — correct for a passive remote node.
- next: CHECKPOINT for the main loop to commit. Then placement (floorplan.yaml
  adapted from the analog-audio-pod archetype) → generate_board → routing.
