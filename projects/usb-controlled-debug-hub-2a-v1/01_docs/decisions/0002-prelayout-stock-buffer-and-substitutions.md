# ADR 0002 — require +200 public-stock surplus before footprint freeze

status: accepted
date: 2026-08-20
partially_superseded_by: ADR 0003 for the pre-layout JLC response only

## Context

The first quantity-five candidate BOM passed the legacy public-catalog gate,
but six exact codes had fewer than 200 units beyond the build requirement.
Proceeding would make ordinary catalogue movement capable of forcing package,
footprint, placement and routing backtracks.

## Decision

Before footprint promotion, every machine-assembled LCSC line must satisfy
`public stock >= aggregate quantity required for five boards + 200`. This is a
negative candidate filter, not allocation evidence. ADR 0003 subsequently
accepts this exact filter for pre-layout only; order-time ALLOCATED/economics/
BOM-echo checks remain mandatory.

Adopt these exact replacements:

| Function | Rejected code | Selected code / MPN | Public stock at decision |
|---|---|---|---:|
| 24 MHz crystal | C1985204 | C70590 / X322524MOB4SI | 101,010 |
| USB shunt ESD | C3708426 | C3709087 / PESD2USB5UX-TR | 2,523 |
| 910 kOhm divider | C352384 | C25800 / 0402WGF9103TCE | 42,065 |
| factory USB-I2C bridge | C640876 | C130462 / MCP2221A-I/ST | 380 |
| bank circuit breaker | C2878936 | C2155765 / TPS259827ONRGET | 603 |

Keep exact GCT USB1130-15-A receptacles because their manufacturer documents a
3 A rating. Exclude them from turnkey population and buy/fit or consign them;
DigiKey publicly listed 18,788 exact units. High-stock JLC alternatives found
during the search were rated only 1–1.8 A or lacked adequate manufacturer
authority and therefore cannot support the 2 A service claim.

## Consequences

- MCP2221A changes from SOIC-14 to TSSOP-14; functionality and pin numbering
  stay unchanged but exact footprint/model review is reopened.
- TPS259827ONRGET is pin-compatible with the former TPS259804 cell and keeps
  the same 300 ohm full-temperature current-limit window. It has no OVLO,
  which is appropriate on the protected 5 V bank; latch-off remains selected.
- PESD2USB5UX-TR retains the same SOT-23 shunt topology and lowers maximum
  channel capacitance from 0.7 pF to 0.6 pF.
- The exact crystal keeps 24 MHz, 12 pF load and the 3225 four-pad geometry;
  its tolerance/stability remain comfortably within the hub clock budget.
- The four USB-A connectors become an explicit manual/consigned population
  set and must appear in assembly and procurement previews as such.
