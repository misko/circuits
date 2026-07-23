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
