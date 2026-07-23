# journal: 02_parts

## 2026-07-23 — start
- did: commissioned the project (BRIEF, ARCHITECTURE, ADR-0001..0006, power_tree,
  nets, electrical_invariants). Ran the D-SPEC sourcing spike against the ledger:
  8 of 15 core parts are ledger hits (XU316, PCM1865, NC7NZ34, AP61102, XC6227,
  TCR2LF18/TLV70018, TPD2E2U06, RJHSE-5384) — escape/gotchas/layout_refs/lcsc
  copied from proven-parts.yaml (sanctioned reference). 7 parts + protection
  passives need fresh datasheet research: FA-238, W25Q16, USB4105, TPD4EUSB30,
  SHT40, MINISMDC050, AO3400A/AO3401A, plus SMAJ5.0A TVS, barrel jack, fuse.
- result: fab_tier fixed to jlc_6layer_smallvia (ADR-0002); tension table T1/T2/T3
  recorded; XU316 consignment flagged (ADR-0003).
- next: fan out parts research (5 concurrent agents), each emits part.yaml with a
  datasheet-FIGURE pin map + verified note; then merge, spot-verify S-VER, run
  escape_check over the merged set.

## 2026-07-23 — finish
- did: merged 18 part.yaml from the 5-agent fan-out; spot-verified S-VER figure
  citations (PCM1865 pin15=SCKI/pin10=XI EXPLICITLY confirmed p10/p11 SLAS831D;
  XU316 128/128 pins from Table 4 + Fig.2 XM-014532-PC-2.0.0). Ran escape_check
  over the full set (18/18 ok), fixed the XU316 tier to the exact escape_check
  verdict (jlc_4layer_advanced; board fabs 6L-smallvia per ADR-0002). Added
  layout: blocks to DC-005/TPD2E2U06/RJHSE-5384 (P-LAYOUT). Removed the pod-5V
  pass-through "rail" from power_tree (not a converter) — E-TOPO now OK.
- result: policy_audit parts gates GREEN — S-VER/P-ESC/P-TIER/P-LAYOUT PASS,
  E-TOPO PASS (2 bucks BUCK-correct). Only FAIL = E-INV (needs the schematic
  netlist — resolves at the schematic gate). Renamed crystal dir (space->_).
- flags carried: barrel jack DC-005-5A-2.0 (C381116, 5A for the GST25A05); fuse
  JFC1206-1200FS (C136345 — brief's JB12F2001R not LCSC-findable, recorded as
  alt); MINISMDC050F-2 is LITTELFUSE (C2649901); FA-238 CL=9pF -> 12pF load caps,
  C7190380 was OOS at fetch (sourcing risk); XU316 EP needs a project-local
  TQFP-128_EP footprint variant + 4x4 via-in-pad thermal grid.
- next: author the tscircuit board (schematic gate: ERC 0 + refdes parity).
