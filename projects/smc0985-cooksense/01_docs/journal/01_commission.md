# journal: 01 commission

## 2026-07-22 — commissioned (interactive session)
- did: archived Rev 1.0 brief verbatim + D1-D6 decision register into
  BRIEF.md with the S9 spec-tension table (T1-T6); ADRs 0001-0006;
  ARCHITECTURE.md. Skeleton seeded from the drift-corrected contract
  templates (12 contracts).
- key findings folded in: CN1 is LATCHED (photos; TRIO-MATE is
  friction-only per TE TDS) -> tail-geometry-replication strategy
  (ADR-0005); Pi GPIO budget overflow -> MCP23017 (ADR-0003); cameras
  to Pi-native I2C + phantom-power pullup rule (ADR-0004); NO MCU —
  all enforcement in hardware (ADR-0002); relay cell = cook-hub's
  paid-for DIP05-1A72-12L (ADR-0006).
- E-TOPO: N-A by design (all-linear power, no converters) — do NOT
  fabricate a power_tree.yaml.
- next: (bench, user-side) Gate-1 CN1/tail measurements incl. the two
  lock-slots; (pipeline) parts stage — fan-out part.yaml research w/
  layout: blocks (P-LAYOUT day-one), jlc_twin stock check on DIP05 +
  AQY212GS + TRIO-MATE; then schematic w/ the ADR-0002/0006 invariants
  (E-ADR currently holds those loops open — intended).

## 2026-07-24 — interposer commissioned (Board C, Task #12, DESIGN-ONLY to routing gate)
- did: activated the INTERPOSER board per ADR-0007 (per-board sub-tree). Path A
  decided by user -> ADR-0009 + BRIEF D9; Commission fact-lock (interposer)
  filled in BRIEF.md — passive signal board, all power/protection/off-control
  rows N-A by design (documented why per row).
- result: scope locked: 2x 10FDZ-BT (self-supplied THT, footprint authored from
  JST eFDZ datasheet — NEEDS REAL-PART PHYSICAL CONFIRM before any seal) +
  J_KEY_MATRIX (SM10B-GHS-TB, reused verified part, pin map == main board) +
  20 labeled TPs; 10 floating nets KP_U1..U6/KP_D1..D4; NO GND anywhere.
  HARD STOP declared: routing gate (DRC 0/0/0 + M-REPRO) then HOLD — no seal,
  no order (G2 coupon + footprint confirm block).
- next: 02_parts 10FDZ-BT (datasheet fetch + part.yaml + hand-authored
  .kicad_mod in 03_src/lib/cooksense.pretty + escape block).
