---
id: 0001
date: 2026-07-23
status: accepted
---
# 0001 — Input protection (5V barrel-jack entry)

## Context
The board is powered by ONE external Mean Well GST25A05-P1J 5V/5A brick via a
barrel jack (D5). It carries no on-board energy store, so de-energization =
unplug (E-OFF N-A). Threats at the DC input: reverse-polarity plug, surge /
ESD on the jack, and a WRONG adapter (higher voltage) — the AP61102 bucks and
XC6227 LDO all have VIN abs-max 6.5V (OVP 6.3V, which does NOT protect the VIN
pin per ledger), so an over-voltage input is a real kill path (T2).

## Options
- **Schottky series diode RPP** — REJECTED: 0.3-0.5V drop at ~1.6A wastes
  ~0.6W and drops the 5V rail toward the pod delivery budget.
- **P-channel MOSFET high-side RPP + TVS + fuse-on-fault** — CHOSEN: near-zero
  drop (Rdson ~50mohm), reverse plug blocks via the FET, TVS clamps surge, and
  a series input fuse/PTC blows on a sustained over-voltage fault (crowbar with
  the TVS).
- **No protection, trust the regulated brick** — REJECTED: the mandatory
  input-protection ADR exists precisely because "trust the supply" ships
  reverse-polarity and OVP defects that pass every electrical gate.

## Decision
High-side **P-FET reverse-polarity** (Q1, AO3401A — the P-ch complement to the
AO3400A already on the BOM): drain to VIN_RAW (jack +), source to the 5V rail,
gate to GND through R (Vgs = -5V turns it on forward; reverse plug leaves it
off). A **unidirectional 5.0V TVS** (D1, SMAJ5.0A) on VIN_RAW clamps surge
ahead of the FET. A **series input fuse** (Littelfuse nano / 2A) on VIN_RAW: on
a wrong-adapter over-voltage the TVS conducts hard and the fuse opens.

T2 residual: a standard 5.0V TVS breaks down 6.4-7.1V and clamps ~9V under full
surge — above the 6.5V buck abs-max for the ns-us transient. Accepted: the
GST25A05 is a regulated 5.0V±2% supply (~5.1V max steady state, far below
6.3V OVP); the TVS+fuse is a FAULT crowbar (wrong adapter), not a steady clamp.
A tighter clamp (e.g. an active OVP load-switch) is a documented next-rev option
if field use exposes the board to arbitrary adapters.

Parts resolved (parts stage): Q1 = AO3401A (C15127), D1 = SMAJ5.0A (C87074,
Diodes Inc SMAJ5.0A-13-F, well stocked), F_IN = JFC1206-1200FS (C136345, a
2A/1206 fast fuse — the brief's JB12F2001R was not LCSC-findable; this is the
recorded substitute, alternate JB12F2001R if it becomes available), jack J1 =
DC-005-5A-2.0 (C381116, 5.5x2.1mm 5A barrel for the GST25A05-P1J P1J plug).

## Consequences
- Q1 AO3401A + D1 SMAJ5.0A + F_IN JFC1206-1200FS added to the BOM (all cheap, in stock).
- ~50mohm Rdson drop at 1.6A ~= 80mV on the 5V rail — negligible for pods.
- First-power ritual: multimeter the barrel jack polarity + continuity to 5V
  before applying the brick (jlcpcb-fab checklist).

## Invariants emitted (03_src/rules/electrical_invariants.yaml)
- `series_chain [VIN_RAW, Q1, 5V] through {Q1:[D,S]}` — the RPP FET sits in
  series between the raw jack and the 5V rail, drain-to-source.
- `net_has_part VIN_RAW diode >=1` — the TVS clamps the raw input.
- `net_has_part 5V capacitor >=1` — bulk decoupling on the protected rail.
