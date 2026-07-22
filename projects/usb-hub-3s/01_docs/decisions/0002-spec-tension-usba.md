---
id: 0002
date: 2026-07-21
status: accepted
---
# 0002 — Spec tension T1: "USB-A 2.5 A max" vs USB standards and receptacle ratings

## Context
The prompt asks for "3 x USB A ports (2.5A max)". The user amended (D1/D3):
"USB A is meant to be 2A and burstable 2.5" — i.e. ≥2 A continuous, 2.5 A burst.
Governing standards: USB 2.0 allows 0.5 A; BC1.2 DCP allows 1.5 A; the de-facto
legacy ecosystem (Apple 2.4 A divider mode) reaches 2.4 A. There is NO USB
standard that grants 2.5 A on a Type-A port; receptacle datasheets in the JLC
catalog typically rate 1.0–1.8 A continuous per power contact.

## Options
- **Silently build 2.5 A ports** — REJECTED (D-SPEC: silent out-of-spec build).
- **Silently downgrade to 1.5 A BC1.2** — REJECTED (D-SPEC: silent downgrade;
  violates D1).
- **Protection-ceiling reading (CHOSEN)**: each port advertises BC1.2 DCP +
  Apple 2.4 A divider via a TPS2513 auto-detect chip (the strongest legacy
  advertisement that real devices honour), and the PORT HARDWARE is built for
  2.5 A burst: per-port current-limit switch set ≈ 3.0 A (above 2.5 A burst,
  below connector damage), 5 V rail budgeted 3 × 2 A continuous, VBUS copper
  sized ≥ 3 A/port. The 2 A/2.5 A figures are the SUPPLY capability the user
  asked for; what a sink draws is the sink's decision under DCP rules.
- Receptacle rating: choose the JLC-orderable USB-A receptacle with the best
  documented rating; record its number in its part.yaml. Known ceiling: most
  are rated 1.5 A. RESOLUTION: dual power-contact wiping receptacles carry
  2 A-class current in practice (powerbank industry does exactly this), but the
  DATASHEET number is the honest cap — recorded per part, flagged to the user
  in the final report.

## Decision
Ports deliver 2 A continuous / 2.5 A burst electrically (ILIM ≈ 3 A), with
BC1.2 DCP + 2.4 A-divider advertisement (TPS2513). Receptacle datasheet rating
recorded at part selection; any sub-2A receptacle rating is flagged as an
accepted deviation in the final report and ORDER_README.

## Consequences
- 5V_A rail must supply ≥ 6 A continuous, 7.5 A burst (+ margin).
- Per-port: TPS2557 limit switch (RILIM → ~3 A) + TPS2513 DCP + ESD array.
- The user sees the receptacle-rating caveat in the final report.
