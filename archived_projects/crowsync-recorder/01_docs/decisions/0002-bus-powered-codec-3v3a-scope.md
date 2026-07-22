---
id: 0002
date: 2026-07-16
status: accepted
---
# 0002 — Codec runs bus-powered; TPS7A2033 powers only the analog front-end

## Context

The brief pins TPS7A2033PDBVR as "low-noise 3.3 V analog rail". The
PCM2900C datasheet (SBFS039) shows two configurations: simple bus-powered
(fig 38 — VCCCI/VCCP1I/VCCP2I/VCCXI/VDDI are internal-regulator outputs,
decoupling caps only) and "high-performance" (fig 36 — those pins driven
externally at **3.6–3.85 V**).

## Options

- **Drive the codec supply pins from the TPS7A2033** — REJECTED: 3.3 V is
  BELOW the 3.6–3.85 V external-supply window; out-of-spec operation of a
  user-pinned part to satisfy a topology the brief never asked for.
- **Add a second 3.75 V LDO for fig-36 high-performance mode** — REJECTED:
  adds a part the brief didn't pin; the fig-38 penalty ("analog performance
  of the ADC may be degraded") is small against an outdoor electret noise
  floor at 16-bit/48 kHz, and the mic signal is pre-amplified before the ADC.
- **Bus-powered codec per fig 38; TPS7A2033 dedicated to the front-end**
  (chosen) — codec self-contained from VBUS; the low-noise rail feeds
  exactly the noise-critical nodes: TLV9062 supply and mic bias.

## Decision

PCM2900C in fig-38 bus-powered configuration; TPS7A2033 3V3A rail powers
TLV9062 + mic bias network only.

## Consequences

- Codec supply pins get individually-named nets (VCCCI, VDDI, ...) with only
  the datasheet decouplers — the pin-review agents must NOT expect them tied
  to a rail.
- Mic-channel SNR is set by the preamp (on the clean rail), not the ADC's
  internal regulator.
- If a future article needs the last few dB of ADC dynamic range, a fig-36
  3.75 V LDO retrofit is a new ADR + board rev.
