---
id: 0002
date: 2026-07-17
status: accepted
---
# 0002 — LM339 variant selection (no Basic option exists) + rail plan

## Context

P6 pins "one LM339 (quad, basic part) … power the LM339 from the 5V
rail". Live JLC search 2026-07-17: **no LM339 of any brand is in the
Basic library** — every listing (TI, ST, onsemi, UTC…) is Extended. The
"basic part" clause is unsatisfiable as written; the part class itself
is pinned, so we pick the best Extended cross.

## Options

- **TI LM339DR** (C7948) — $0.177, 45.5k stock.
- **onsemi LM339DR2G** (C63821) — $0.168, 68.9k stock.
- **ST LM339DT** (C71036, CHOSEN) — $0.140, 45.8k stock, SOIC-14,
  specs identical for this use (2–36V supply, CM to VCC−1.5V, inputs
  rated +36V independent of VCC, 1.3us response, open collector).
  Highest-stock-lowest-cost rule among equivalent crosses (P2) → the
  ST part wins on cost with ample stock; onsemi kept as alternate.
- **UTC LM339G-S14-R** ($0.12, 1.3k stock) — REJECTED: stock below the
  5x margin comfort for a clone brand.

## Rail plan (restating the user-pinned facts as build constraints)

- LM339 VCC = **5V** (pinned; CM range must cover the 0–3V PD swing).
- Outputs pull up to **3.3V** via 10k (pinned) — open collector makes
  the mixed-rail interface inherently safe for the S3 GPIOs.
- Thresholds derive from **3.3V** (pinned, A1 fixed): the LDO output is
  tighter than USB VBUS (±1% + load reg vs 4.4–5.25V USB), so a 0.70V
  threshold from 3.3V is supply-stable even when VBUS sags.
- 4th comparator: +IN4→GND, −IN4→VTH3 (the 0.7V channel-3 threshold —
  a defined DC level already present on the same SOIC pad column, so the
  tie routes at signal width; 3V3 at the 0.5mm PWR floor could not reach
  the mid-column pad), output floating per P6. Loading on VTH3: <=250nA
  bias -> <=0.5mV threshold shift, negligible.

## Decision

ST LM339DT (C71036), one unavoidable Extended reel, powered from 5V,
outputs pulled to 3.3V, thresholds and hysteresis per DETAIL_DESIGN.
