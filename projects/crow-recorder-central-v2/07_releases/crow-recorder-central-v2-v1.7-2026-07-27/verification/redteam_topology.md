subject: crow-recorder-central-v2 v1.2-staging (07_releases/crow-recorder-central-v2-v1.2-2026-07-24)
date: 2026-07-24
reviewer: redteam-agent (fable-medium, topology/protection/ratings lens)
context-given: release-archive-only
verdict: ORDER

# Red-team review — v1.2 staging, topology/protection/ratings lens

All checks below were computed by this reviewer from the staged archive's own
bytes (and the sealed v1.1 archive, opened read-only). Nothing was taken from
the maker's prose without re-measuring it.

## 1. Netlist diff vs sealed v1.1 — CLAIM VERIFIED

`diff` of the two `source/crow_recorder_central_v2.net` files, then an
independent net-membership parse:

- Component sections: exactly 5 comps added — C_c9, C_c10, C_c11, C_c12,
  C_c13, each `value 100nF`, footprint `Capacitor_SMD:C_0402_1005Metric`.
  Comp count 196 (v1.1) -> 201 (v1.2), delta +5, nothing removed.
- Net membership (parsed, not diff-context-guessed): each new cap has pin 1 on
  `0V9` and pin 2 on `GND`. No other net gained or lost a node; net-name set
  identical. Only other diff line is the export timestamp.
- 100nF caps on 0V9 in v1.2: 13 (C_c1..C_c13) vs 8 in v1.1; vendor minimum is
  12. Quote verified at source in this project's own vendored datasheet
  (02_parts/XU316-1024-TQ128-I24/XM-014532-PC-2.0.0...pdf, §14 p.29,
  pdftotext hit: "Place many (at least 12) 100 nF low inductance multi-layer
  ceramic capacitors close to the chip between the supplies and GND").

The decoupling_fix.md diff claim is exact. Total 0V9 net membership (35 pads,
21 refs) is v1.1's set plus the 5 caps: C_b0v9 bulk, Cout_U8/Couth_U8, L2,
L_pll, R_fb2a, TP3, U1 — no topology change on the rail beyond the caps.

## 2. BOM / CPL — VERIFIED

- fab/bom.csv diff vs v1.1: ONE changed line — the 100nF / C_0402_1005Metric /
  LCSC **C1525** row gains exactly C_c9..C_c13 (39 -> 44 designators). No
  other BOM line changed; C1525 is the same already-vetted basic part, so no
  new sourcing/stock exposure.
- fab/cpl.csv diff vs v1.1: exactly 6 rows differ — the 5 new caps (all top,
  0402) and C_b0v9 moved (91.8,-112.3) -> (91.85,-116.05) = 3.75 mm south,
  matching the documented bulk-slot swap. Bulk caps have no pin-adjacency
  requirement (ds §14), so the move is a legal trade.

## 3. Topology / protection / ratings regressions vs v1.1 — NONE FOUND

Independently re-measured on the archived .kicad_pcb with pcbnew:

- Per-pin nearest-0V9-cap distances reproduce decoupling_fix.md's table:
  pin 5 = 3.22 mm (unchanged worst case, honestly disclosed), pins 11/14 =
  1.63 mm (was 3.50/2.99), pin 50 = C_c11 2.01 mm (was 3.51), pin 54 = C_c13
  2.02 mm (was 3.90), pin 95 = C_c12 2.54 mm (doc says 2.55 — rounding).
- v1.1 blocker closures intact on THIS archive: U1 pins 40/43/52 (LV straps)
  read `unconnected-(U1-PadNN)` — still floated (PR2-P0-1 closure); 16 GND
  vias within 2.5 mm of U1 center (EP thermal grid, F1 closure).
- Reviewer-run DRC on the archive's own source (kicad-cli, --severity-all
  --refill-zones --schematic-parity): **0 violations / 0 unconnected / 0
  parity** — independently reproduces the shipped drc.json (also 0/0/0).
  Shipped erc.json re-counted: 0 errors / 1211 warnings, matching the README.
- Ratings: the change adds ceramic capacitance only (+0.5 uF distributed) on
  a 0.9 V buck output already carrying 10 uF bulk + 8x100nF — no voltage/
  current rating concern, no new protection path touched. Input protection
  chain (Q1/D1/F_IN), RJ45 posture, and USB path are byte-identical in the
  netlist diff. ADR-0007 RJ45/OVP waiver: out of scope per tasking, not
  re-litigated; the §0 banner is carried verbatim.

## 4. ORDER_README v1.2 header + §4a gate text — CONSISTENT

- Header arithmetic checks: "8 local caps vs minimum 12" (v1.1 truth),
  "13x 100nF C_c1-C_c13" (matches netlist), pin 50/54 numbers match the
  measured table, count_parity 199 x4 = v1.1's 194 + 5, ERC 1211 = shipped
  erc.json, DRC 0/0/0 reproduced above.
- §4a strengthened rail-sequencing gate: pass condition (1V8 valid before
  0V9 valid at EVERY corner; RST_N held until 3V3+1V8 stable) is explicit,
  the corner list is enumerable, and the failure action ("real interlock...
  NOT an empirical delay tweak") does not contradict §6, which records the
  same interlock as the v-next item and makes it mandatory on any corner
  failure. Honest about the limits: ordering is "plausible-by-topology...
  NOT interlocked". No internal contradiction found.

## Findings

- **P2** — verification/audit.txt ships 3 lines of pcbnew PROPERTY_ENUM
  assert noise ahead of the one-line audit_board OK; cosmetic, but stderr
  should be filtered from evidence files so the signal line is not buried.

No P0/P1 findings. Every tasked check passed under independent re-measurement.

Verdict: **ORDER**.
