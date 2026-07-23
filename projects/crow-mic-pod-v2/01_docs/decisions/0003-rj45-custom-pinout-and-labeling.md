---
id: 0003
date: 2026-07-23
status: accepted
---
# 0003 — RJ45 custom NON-ETHERNET pinout & mandatory labeling (T1)

## Context
The user directive amends the doc: "use ethernet cable AND ethernet
connectors EVERYWHERE" — so the pod end gets an RJ45 JACK (not a gland +
solder pads). But the cable is NOT Ethernet: it carries a custom 5V
power/audio pinout. This is spec-tension T1 — the connector is
electrically legal for the load but SEMANTICALLY hazardous: an RJ45 invites
a field tech to plug the pod into a real Ethernet switch, which would put
switch PHY voltages onto AUDIO_P/AUDIO_N and feed 5V_AUDIO backward into a
switch port.

## Options
- **Gland + solder pads (the doc's original)** — REJECTED by the user
  directive (RJ45 everywhere).
- **Keyed / shrouded non-RJ45 connector** — REJECTED: violates the "ethernet
  connectors everywhere" directive; the whole point is cable/connector
  commonality across the array.
- **Standard RJ45 jack + RIGOROUS labeling discipline** (ACCEPTED): use the
  ledger-proven RJHSE-5384 (shielded, board-locked), wire the exact custom
  pinout, and make the hazard IMPOSSIBLE TO MISS on the silk.

## Decision
ONE RJ45 jack (RJHSE-5384) on the WEST edge. Pinout (honoring the shared
cable contract, ARCHITECTURE.md): 1,2=AUDIO_P/AUDIO_N; 3,6=5V_BEEP/
BEEP_SWITCHED_RETURN; 4,5=5V_AUDIO (paralleled); 7,8=GND_AUDIO (paralleled);
shield→GND_AUDIO. Silk MUST carry, adjacent to J1 and legible:
- Header: **"NOT ETHERNET - CUSTOM 5V AUDIO PINOUT"**
- Full legend: `1,2 AUDIO+/-  3,6 5V_BEEP/RET  4,5 +5V  7,8 GND`
The two integrated jack LEDs are left NC (meaningless without a PHY) —
sanctioned floats, no_connect flags emitted (S4).

## Consequences
- T1 is flagged to the user in the release report (a labeled connector is a
  mitigation, not a lockout — a keyed variant is the only true fix and the
  directive forbids it).
- The identical labeling discipline binds the sibling CENTRAL board's 8
  jacks; this pod defines the pod-end half of that shared contract only.
- RJHSE-5384 is consign-only (LCSC C99*, stock 0, no EasyEDA CAD) →
  hand-solder line + a NO-CAD twin adjudication (evidence-backed).

## Invariants emitted (E-INV)
Into `03_src/rules/electrical_invariants.yaml`, citing adr 0003 — the exact
custom pinout is the contract, so it is machine-pinned:
- `pin_on_net` J1 pin1 = AUDIO_P, pin2 = AUDIO_N, pin3 = 5V_BEEP,
  pin6 = BEEP_SWITCHED_RETURN, pin4 = 5V_AUDIO, pin5 = 5V_AUDIO,
  pin7 = GND_AUDIO, pin8 = GND_AUDIO (pin numbers = the footprint's pad
  names, resolved from part.yaml).
