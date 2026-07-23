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

**AMENDED 2026-07-23 (fix pass) — the hazard analysis above was INCOMPLETE.**
It considered only (a) PHY signal voltage onto AUDIO and (b) 5 V backfeed
INTO a switch port. The 4-lens red-team (P0-A/B) identified the dominant,
missing vector: **power INJECTION.** This board's custom power pins
4,5=5V_AUDIO / 7,8=GND alias EXACTLY onto IEEE 802.3af/at "Alternative-B"
PoE at the same fixed polarity, and 5V_AUDIO ties to U1 V+ (abs-max 40 V)
with zero series impedance — so a PoE switch drives 44–57 V into the op-amp
supply, and Mode-A PoE forces the D1 ESD array into ~13 W sustained
conduction. The RJ45-everywhere directive therefore creates a
destroy-on-mis-plug exposure that this ADR's labeling mitigates but does
NOT eliminate. The exposure is ACCEPTED as a documented deployment-
constraint waiver with USER sign-off — full hazard + mitigation + residual
risk in **ADR-0005** (BRIEF A1). This ADR's contribution to that mitigation
is the silk labeling, now required ADJACENT to J1 (see Decision).

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

## Footprint certification (P0-C resolved, 2026-07-23 fix pass)

The pin-review raised P0-C: the stock KiCad `RJ45_Amphenol_RJHSE538X`
footprint might be a full 1↔8 CONTACT MIRROR of the real part (which would
swap every custom net onto the wrong physical contact — a field hazard).
A definitive geometric re-analysis of the Amphenol dwg P-RJHSE-538X Rev K
"RECOMMENDED P.C.B. LAYOUT (COMPONENT SIDE OF BOARD)" + "LED SCHEMATIC"
figures against the footprint's extracted pad coordinates resolves it:
**CERTIFIED CORRECT — NOT a mirror.**

The decisive test the pin-review missed is ROW PARITY, not just contact side:
- Datasheet groups {contact 1, LED 9, LED 10} at ONE end and {contact 8, LED
  11, LED 12} at the other — the SAME grouping the KiCad footprint has (pads
  9,10 share the low-x end with the rect pad 1; pads 11,12 share the high-x
  end with pad 8).
- The KiCad→datasheet transform is a PURE 180° in-plane rotation (no
  reflection): it reproduces contact-1's side AND the odd-row-on-bottom
  parity AND the stagger direction AND the LED-pair ordering (12,11 / 10,9)
  ALL simultaneously. An x-reflection would flip contact-1 to the right end
  but would leave the odd row on TOP — contradicting the datasheet, which has
  the odd row on the bottom. Only the rotation matches every feature ⇒ same
  chirality ⇒ not mirrored.
- The hole PATTERN itself is fully mirror-symmetric (both Ø3.25 posts, all
  LED holes, both shield tabs), so no drilled feature alone fixes contact 1;
  certification rests on the manufacturer's printed COMPONENT-SIDE contact
  labels, which land on the same holes KiCad numbers. That is authoritative.

No pad remap, no vendored footprint. As defense-in-depth against a
hypothetical datasheet drawing error (the geometry being symmetric), a
one-time pad-1→physical-contact-1 continuity check on a real RJHSE-5384 is
retained as an ORDER_README backstop (same discipline as the first-power
ritual and the LED-polarity check) — a recommended verification, NOT an
order blocker.

## Consequences
- T1 is flagged to the user in the release report (a labeled connector is a
  mitigation, not a lockout — a keyed variant is the only true fix and the
  directive forbids it). The POWER-INJECTION half of the hazard is the
  ADR-0005 accepted waiver.
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
