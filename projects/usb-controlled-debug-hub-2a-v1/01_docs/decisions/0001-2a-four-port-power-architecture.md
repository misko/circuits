# ADR 0001 — four simultaneous 2 A ports use two retained 6 A buck cells

status: accepted architecture; exact component programming and sourcing pending
date: 2026-08-20

## Context

The predecessor supplies four 500 mA ports from one TPS56637 and a 15 V/3 A
PD contract. The new requirement is four simultaneous 2 A outputs. That is
40 W at the connectors before conversion, protection and management losses.
The predecessor's USB-A connector also has no published contact-current rating.

## Decision

Request a 20 V/3 A PD fixed PDO and use two identical TPS56637 6 A converter
cells, each feeding two external ports through its own aggregate protection.
Keep the v2 hub, management and data-switching core. Reprogram each retained
TPS259470A port eFuse for a full-corner threshold above 2 A and below the
selected connector's 3 A rating. Replace KH-AF90DIP-112 with the already-
qualified GCT USB1130-15-A. Re-open the input clamp/gate because the v2 18 V
clamp and OVLO intentionally reject 20 V. Use TPS16630PWPR with TVS2200 at
that boundary; the initially considered TPS259827O is rejected because its
24 V recommended limit is below the TVS2200's 28.35 V worst published clamp.
TPS26630 was electrically acceptable but rejected at commission because exact
TI public stock was zero; the TPS16630 HTSSOP had ample public stock.

## Why

Two copies of the proven 6 A cell preserve a purchased high-cost IC and its
manufacturer layout precedent while keeping each continuous service bank near
4 A. A single 6 A cell cannot meet the 8 A requirement. A new monolithic 10 A
converter would discard qualified parts and concentrate thermal/current-path
risk. A 15 V/3 A source has no loss margin; 20 V/3 A provides 60 W.

## Consequences and gates

- The input protection stage changes and must receive a new transient/UVLO/
  inrush proof; no v2 protection evidence carries forward.
- The board gains a second buck/inductor/output-capacitor cell and a second
  aggregate breaker, increasing area but reducing bank current density.
- Output connector geometry changes and requires fresh footprint/model/
  orientation evidence.
- Exact port and aggregate current-limit corners, voltage-drop/thermal math,
  preliminary JLC allocation and MOQ economics block part freeze.
- TPS16630 UVLO/OVP, ILIM and inrush programming require machine-checked
  component/device/leakage corners before schematic generation.
- No firmware work is authorized.
