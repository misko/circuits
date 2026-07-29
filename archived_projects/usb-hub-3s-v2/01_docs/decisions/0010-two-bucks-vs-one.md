---
id: 0010
date: 2026-07-22
status: accepted
---
# 0010 — Two separate 5 V bucks (per rail) vs one shared 11 A buck

## Context
Both output rails are fixed 5 V step-down bucks (E-TOPO). Total load is
USB-A 6 A + USB-C 5 A = 11 A at 5 V. The architecture choice: ONE shared 5 V
buck sized for ~11 A feeding both rails, or TWO separate 5 V bucks (one per
rail). The task flags this as the key architecture ADR.

## Options
- **Two separate LM5116 bucks (CHOSEN).**
  - Buck A: LM5116 + AON6354 pair + 6.8 µH → 5VA (≤ 6 A) → 3× TPS2557.
  - Buck C: LM5116 + AON6354 pair + 6.8 µH → 5VC (≤ 5 A) → TPS25740A path FET.
  - Each buck operates INSIDE the proven LM5116 5 V/7 A design point (v1's
    USB-A buck, DRC-clean and shipped). 6 A and 5 A are both < 7 A, so **zero
    re-derivation** — the FB divider, RT, slope, CS shunt (10 mΩ), inductor,
    and UVLO/EN values are the v1 buck verbatim, twice.
  - **Fault isolation** (matches v1 ADR-0001's isolation intent): a USB-C fault
    (shorted path FET, PD misbehaviour) cannot starve the three USB-A ports,
    and vice-versa. The two converters share only VIN and GND.
  - The **PD cell is cleanly separable**: buck C + TPS25740A + path FET form a
    self-contained block, easy to place and route without interacting with the
    A-side — the opposite of v1's congested shared PD hot loop.
- **One shared 11 A buck (REJECTED).**
  - Would exceed the proven 7 A design point → new inductor (≥ 15 A sat),
    bigger shunt/FETs, re-derived compensation and thermals — NEW engineering
    and NEW risk for the sake of parts count.
  - Single point of failure: one buck fault kills ALL four ports.
  - No fault isolation between the A-side and C-side.
  - Marginal BOM saving (one controller + one inductor + one FET pair) does not
    justify losing the proven design point + isolation.

## Trade acknowledged
Two bucks cost ~1 extra controller (LM5116 HTSSOP, cheap, standard-tier), one
extra FET pair (AON6354 DFN), one extra inductor, one extra shunt, and the
duplicated control passives (~15 small 0603). All are standard-tier, low-cost,
and NON-congesting. The per-port current limits (TPS2557 ILIM on each A-port,
TPS25740A/path-FET on the C-port) already provide DOWNSTREAM isolation; the
two-buck split adds UPSTREAM (converter-level) isolation on top. The input
trunk (~6.8 A) is unchanged either way — it carries the sum.

## Decision
TWO separate LM5116 5 V bucks, each the v1-proven 5 V/7 A design reused
verbatim: Buck A → 5VA (USB-A, 6 A), Buck C → 5VC (USB-C, 5 A).

## Consequences
- Refdes: U2 = buck-A controller, U11 = buck-C controller; Q2/Q3 and Q13/Q14
  the FET pairs; L2/L3 inductors; RS1/RS2 shunts. Control passives duplicated
  with _A / _C net suffixes.
- Both UVLO dividers gate their own converter off below ~8.8 V — no separate
  board-authority comparator needed (ADR-0001).
- Placement (next session): two independent buck cells + a separable PD cell —
  routes far easier than v1's single buck-boost hot loop.
