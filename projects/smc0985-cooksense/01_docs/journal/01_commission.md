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

## 2026-07-30 21:20 — CORRECTING ENTRY: the commission fact-lock named the SUPERSEDED relay code (B30-17 / topology P1-7)
- did: corrected the `BRIEF.md` "Commission fact-lock — cooksense (v1.7
  2026-07-28)" row **hard-cell sourcing class** from `DIP05-1A72-12L ×13` to
  **`DIP05-1A72-13L` ×12**. This journal is append-only, so the 2026-07-22
  entry above still reads "paid-for DIP05-1A72-12L (ADR-0006)" — that entry is
  HISTORICALLY CORRECT (it records what was commissioned on the day) and is
  NOT to be edited. This entry supersedes it as to the part actually specified.
- result: MEASURED against the artifacts, not the report. `fab/bom.csv` row 37
  = `DIP05-1A72-13L` over exactly **12** designators (K_D1–K_D4, K_PRESS,
  K_STOP, K_U1–K_U6), footprint `Relay_StandexDIP_1A_pinout13`; `02_parts/`
  contains **only** `DIP05-1A72-13L`. So the fact-lock was wrong in BOTH
  fields — code AND count.
- why it mattered more than a typo: that row is the row a BUYER reads, and the
  relays are self-supplied / hand-soldered / DO-NOT-SUBSTITUTE. `-12L` is a
  different PIN-OUT (code 12 = eight leads, 1↔14 tied as one contact node,
  7↔8 the other, coil on the inner pins) — it is the very land defect that
  makes all six sealed releases v1.0–v1.6 DO-NOT-ORDER. The paperwork of the
  release that FIXES the defect was still instructing a buyer to purchase the
  defect.
- also folded in (from `02_parts/DIP05-1A72-13L/part.yaml`): every distributor
  quote recorded in this tree (Mouser 876-DIP05-1A72-12L stock 132, DigiKey
  DIP05-1A72-12L-ND stock 56, read 2026-07-27) is keyed to `-12L` and **does
  not transfer**. No `-13L` distributor stock figure has ever been read.
  **DISTRIBUTOR SOURCING FOR THE CORRECT CODE IS STILL OWED** — that is now
  stated in the fact-lock itself instead of only in the part dossier.
- netlist impact: **NONE.** `BRIEF.md` is not a build input and is not present
  in the staging archive; board md5 `9f4fd5fae810f40a52b1035df727243c` is
  unchanged, DRC re-run 0/0/0 exit 0 after the edit's pass.
- next: B30-17 closes. B30-01 (C265111) remains OPEN and is a USER decision.
