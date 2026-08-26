    date: 2026-07-24
    subject: smc0985-cooksense interposer v1.0 (pre-seal staging, board 04_kicad/interposer.kicad_pcb)
    reviewer: pin-review (fable-medium fresh-context agent, dossier protocol)
    context-given: dossiers + part.yaml/datasheets only
    verdict: PASS

# Fresh-context PIN REVIEW — interposer v1.0 (verbatim)

## J_MEMBRANE (10FDZ-BT) — PASS
- Land pattern vs eFDZ p.3 (top-entry) + p.2 table: board shows 10 PTH pads drill phi0.90, size 1.6x1.6, one row at y=20.000, pitch 2.54 (x=25.000 to 47.860, span = 22.86 = table value A for 10 circuits, eFDZ p.2). Matches phi0.9±0.05 holes at 2.54±0.05, A=22.86±0.05.
- Polarization boss: NPTH (pad type 3), drill 1.80, at (22.460, 20.000) — colinear with the row, exactly 2.54 outside pin 1. Matches eFDZ p.3 phi1.8 boss one pitch outside circuit 1.
- Nets: pins 1..10 = KP_U1..KP_U6, KP_D1..KP_D4 positionally, as intended. Passive contacts, 50 mA/250 V rating irrelevant to a floating matrix — sane.

## J_CN1_JUMPER (10FDZ-BT) — PASS
- Identical footprint, identical orientation (rot 0, boss at x=22.460 west of pin 1 at 25.000, y=46.000), pin columns X-aligned with J_MEMBRANE (same x per pin) — the straight-through parallel-track intent holds. Same land-pattern match as above. Nets 1..10 positional, identical to J_MEMBRANE. Sane.

## J_KEY_MATRIX (SM10B-GHS-TB) — PASS
- Pattern vs eGH p.3: side-entry header, 10 circuits, A=11.25. Board: pin 1 at (16.850, 27.375) to pin 10 at (16.850, 38.625) -> span 11.25 at 1.25 pitch. Pad 0.6x1.7 SMD, standard KiCad Connector_JST library footprint. No.1 circuit at row end per eGH p.3 figure — single-row, dossier winding CCW is a rotation, not a mirror.
- Nets: pins 1..10 = KP_U1..KP_U6, KP_D1..KP_D4 positionally — matches the two FDZ connectors pin-for-pin. Sane.
- MP tabs: both MP pads (13.650, 25.525/40.475) have net='' — UNCONNECTED, confirmed floating. Per eGH the tabs are tin-plated reinforcement only (no circuit); floating is correct for the isolated keypad domain. Not a defect.

## Findings
1. QUESTION (residual, already tracked) — 10FDZ-BT: which housing end carries circuit 1 vs the boss was read from the eFDZ p.3 reference drawing only (drawing is viewed from the mounting surface, note 1; hole dims are "reference only", note 4). Both FDZ connectors are identically oriented so the board is internally consistent, but the physical-part confirm flagged in 02_parts/10FDZ-BT/part.yaml (NEEDS-PHYSICAL-CONFIRM, blocks ORDER not seal) remains the closing evidence. Nothing new to fix.
2. LOW (doc inconsistency, no board impact) — 02_parts/SM10B-GHS-TB/part.yaml layout.notes (2026-07-22) still said "Tie both MP mechanical tabs to the ISOLATED-side ground", contradicting the corrected pins.MP note (2026-07-23, MP must FLOAT). The board follows the corrected intent; the stale sentence should be cleaned.
