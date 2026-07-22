---
id: 0001
date: 2026-07-21
status: accepted
---
# 0001 — Battery/input protection: fuse + reverse-polarity P-FET + board UVLO + TVS

## Context
Input is a 3S LiPo (9.0–12.6 V envelope, A1) on XT60. The skill mandates this
ADR: reverse polarity, overcurrent, over-discharge (UVLO), overvoltage/transient.
Worst-case input current: USB-C 100 W (0004) + USB-A 30 W at Vin=9.0 V,
eff ~0.93 → ~15.5 A; at 12.6 V → ~11.1 A.

## Options
- **Overcurrent: 20 A MINI blade fuse in THT holder** — hand-solder line, user
  replaceable. CHOSEN over SMD chip fuse (hard to source >15 A, not
  replaceable) and no fuse (REJECTED: hard fault on a LiPo is a fire).
- **Reverse polarity: P-FET high-side ideal-diode-style** (source to load,
  drain to battery, gate to GND via R, zener clamp on Vgs) — ~mΩ loss.
  CHOSEN over series Schottky (REJECTED: ~0.4 V × 15 A = 6 W) and over
  ideal-diode controller + NFET (more parts, controller stock risk).
  FET must be ≥30 V, Rds(on) ≤ 5 mΩ at Vgs = −8 V (worst at UVLO floor ~8.7V),
  continuous ≥ 20 A.
- **Over-discharge/UVLO: LM5116's precision UVLO pin as the SINGLE board
  authority** (divider 49.9k/6.98k → 9.65 V rising / 8.84 V falling, derived
  in DETAIL_DESIGN §2), with the IP6559 EN (GPIO18) gated by 5VA presence
  (10k/10k divider from the 5VA rail): when the buck is UVLO'd, 5VA collapses
  and the PD stage disables too. CHOSEN over a separate TLV431 comparator
  (rejected: its hysteresis needs feedback from a rail with full swing; every
  candidate node here has a weak or ambiguous pull-up — more parts, less
  certainty) and over a hard P-FET load cutoff (rejected for v1: residual
  draw after UVLO ≈ 0.5 mA — IP6559 standby 200 µA + UVLO divider 221 µA +
  LM5116 standby — acceptable; ORDER_README says "do not store the pack
  plugged in").
  Thresholds: cutoff 8.84 V falling (2.95 V/cell), re-enable 9.65 V rising
  (0.8 V hysteresis prevents chatter on load-shed recovery).
  KNOWN RISK (documented): IP6559 GPIO18/EN semantics differ between the _AC
  variant (power-share input, "ground when unused") and the base EN function;
  for the _C variant the EN PIN Function section governs (enabled high,
  internal pull-up). The 10 kΩ pull-down + 10 kΩ feed from 5VA asserts a
  clean logic level either way; first-power ritual verifies UVLO behavior
  with a bench supply BEFORE a pack is connected.
- **OV/transient: SMBJ15A TVS across input after the fuse** — standoff 15 V >
  12.6 V max battery; clamp ≤ 24.4 V < IP6559 abs max 34 V and LM5116 100 V
  rating. CHOSEN. (3S packs cannot legitimately exceed 12.6 V; the TVS guards
  hot-plug inductive spikes, which XT60 hot-plug + wire inductance produces.)
- **Inrush**: bulk input capacitance is large (≥ 300 µF); XT60 hot-plug inrush
  is accepted (LiPo + XT60 standard practice; both converters soft-start).

## Decision
20 A blade fuse (holder, hand-solder) → P-FET reverse-polarity switch →
TVS SMBJ15A + bulk caps → VIN rail. Board-level UVLO ~8.8 V falling /
~9.4 V rising gates both converters (LM5116 UVLO pin; IP6559 EN pin via
detector). Exact values derived in DETAIL_DESIGN.md.

## Consequences
- Fuse + holder are hand-solder BOM lines (JLC THT catalog gap accepted).
- ~0.3 mA post-UVLO standby documented; no hard cutoff in v1.
- P-FET dissipates ≤ 1.2 W at 15.5 A worst case (5 mΩ) — needs copper pour +
  thermal vias at placement; verified at R-THERM.
