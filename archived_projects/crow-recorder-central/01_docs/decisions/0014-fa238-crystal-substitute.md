# ADR-0014 — T2: 24MHz crystal = X322524MOB4SI on the BOM; FA-238 is the Digi-Key fallback

Status: accepted 2026-07-21 (resolves BRIEF spec tension T2; formalizes the
adopted archive's D27 sourcing substitution as this project's decision)

## Context — live stock, re-measured this session

jlc_stock_check.py, 2026-07-21 (06_build/cache/tension_stock_2026-07-21.csv):

| Code | Part | JLC stock | Price |
|---|---|---|---|
| C2650433 | Epson FA-238 24.0000MD30X-W5 (doc-named part) | **0** | $0.20 |
| C70590 | YXC X322524MOB4SI | **104,480** | $0.09 |

FA-238 stock 0 matches the archive's 2026-07-17 finding and the commission
spike — this is persistent, not a blip.

## Decision

- **The assembled BOM line (Y1) is X322524MOB4SI, C70590** — the archive's
  D27 substitution, carried by `03_src/bom_seed.py` ("FA-238" value ->
  X322524MOB4SI). Electrical equivalence is evidenced in
  `02_parts/X322524MOB4SI/part.yaml`: same 3225-4P land as the FA-238,
  SAME CL 12pF (so the on-board 18pF loading network is unchanged),
  +-20ppm vs the Epson +-50ppm (tighter), AEC-Q200 YXC part; geometry
  verified against the C70590 datasheet drawing.
- **FA-238 24.0000MD30X-W5 remains the named-part fallback as a Digi-Key
  hand-solder line**: Digi-Key SER4069CT-ND, 28,284 stock @ $0.44 on
  2026-07-17 (02_parts/FA-238-24.0000MD30X-W5/part.yaml sourcing note).
  If a build must match the XMOS hardware manual's exact crystal, order
  from Digi-Key and hand-place Y1 (4-pad 3225, hot-air).
- Do NOT mix codes: C2650453 ("FA-238 24.0000MB-C3") is the 10pF/50ppm
  variant — wrong CL for this loading network.

## Consequence

- No board or schematic change (same land, same CL). The schematic value
  string keeps the design-intent name ("FA-238 24MHz"); the BOM carries
  the substitute — the ORDER_README states this mapping so the assembler
  is not surprised.
- Order-day stock re-check includes C70590 (deep stock today).
