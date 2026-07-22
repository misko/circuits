# ADR-0015 — T3: 1V8 LDO = TLV70018DDCR on the BOM; TCR2LF18 exact-MPN fallback via Digi-Key

Status: accepted 2026-07-21 (resolves BRIEF spec tension T3; formalizes the
adopted archive's D27 sourcing substitution + the alternates search T3 asked
for)

## Context — live stock + alternates search, re-measured this session

jlc_stock_check.py, 2026-07-21 (06_build/cache/tension_stock_2026-07-21.csv):

| Code | Part | JLC stock | Price |
|---|---|---|---|
| C150173 | Toshiba TCR2LF18,LM(CT) (doc-named part) | **0** (was stocked 2026-07-17) | $0.13 |
| C79924 | **TI TLV70018DDCR** (the BOM part, D27) | **5,258** | $0.22 |
| C92498 | TI LP5907MFX-1.8 | 6,858 | $0.19 |
| C236671 | MicrOne ME6211C18M5G-N | 49,067 | $0.06 |
| C59969 | Richtek RT9013-18GB | 33,901 | $0.17 |

The SOT-23-5 fixed-1.8V 200mA class is dense, as T3 predicted: four
in-catalog pin-compatible candidates all in stock.

## Decision

- **The assembled BOM line (U12) is TLV70018DDCR, C79924** — the archive's
  D27 substitution, carried by `03_src/bom_seed.py` ("TCR2LF18" value ->
  TLV70018DDCR). Pin-compatible (IN/GND/EN/NC/OUT SOT-23-5), 1.8V/200mA,
  cap-stable with the existing 1uF ceramics; evidence in
  `02_parts/TLV70018DDCR/part.yaml` (footprint gotcha: DDC = SOT-23-5;
  the DCK/SC70-5 code C133796 is the WRONG package — do not "upgrade" the
  code at order time).
- **Ranked alternates if C79924 dries up** (same pinout class, from
  02_parts/TCR2LF18,LM(CT)/part.yaml alternates + live check above):
  LP5907MFX-1.8 (C92498, lowest-noise option — closest to the Toshiba's
  quiet-rail role), ME6211C18M5G-N (C236671, deepest stock), RT9013-18GB
  (C59969). Any swap needs its own datasheet pinout re-verification before
  the BOM edit.
- **Exact-MPN fallback**: TCR2LF18,LM(CT) via Digi-Key hand-solder line if
  a build must match the XMOS manual's named part; re-check Toshiba stock
  at order day — C150173 was stocked as recently as 2026-07-17, so a
  restock revert is plausible (part.yaml note says revert if restocked).

## Consequence

- No board change (same land, same loading). ORDER_README states the
  value->BOM mapping like ADR-0014's.
- 1V8 rail load is QSPI flash + XU316 VDDIOB18 (<100mA envelope, BRIEF
  G3); TLV70018's 200mA rating and dropout at 3V3 input hold the archive's
  design math unchanged (re-verified in its DETAIL_DESIGN adoption).
