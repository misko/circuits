---
id: 0003
date: 2026-07-21
status: accepted
---
# 0003 — Spec tension T2: "USB-C 6A max" vs Type-C/PD caps; 5 A compliant reading

## Context
The prompt asks for "1 x USB C port (6A max)". USB Type-C caps a plain Rp
current advertisement at 3.0 A; USB Power Delivery caps ANY contract at 5.0 A,
and >3 A additionally REQUIRES the source to verify a 5 A e-marked cable
(Discover Identity on SOP', Vconn-powered) with 3 A fallback. 6 A does not
exist in any USB standard. The user amended (D2/D3): "USBC still needs to be
5A compliant" / "min requirements are 2A USBA and 5A USBC".

## Options
- **Bare Rp 3 A port** — REJECTED: fails D2 (no 5 A path).
- **Rp overclaim / non-compliant 5-6 A at 5 V** — REJECTED: exactly the
  out-of-spec build D-SPEC forbids; sinks would draw 5 A on non-rated cables.
- **PD source with e-marker verification (CHOSEN)**: a PD3.0 source SoC whose
  contract set includes 5 A objects (fixed 20 V/5 A and PPS up to 5 A), offered
  ONLY after reading a 5 A e-marked cable, falling back to 3 A otherwise.
  This is the only standards-compliant way to put 5 A on a Type-C port.

## Decision
The USB-C port is a USB PD 3.0 source (IP6559-C per ADR 0004): 100 W class,
20 V/5 A + PPS 5 A with integrated e-marker check and 3 A fallback. "5 A
compliant" is satisfied at PD contract voltages (20 V fixed / PPS range), not
at 5 V — fixed 5 V is capped at 3 A by the chip's PDO set, which is itself
spec-conformant (5 V/5 A fixed PDOs are not offered by any mass-market
source silicon). Recorded for the user: the port delivers 5 A under a PD
contract with an e-marked cable; a legacy 5 V-only sink gets up to 3 A.

## Consequences
- Buck-boost topology required (20 V > Vin): IP6559-C 4-switch power stage.
- Vconn sourcing circuit (datasheet Fig. 9) required for e-marker reads.
- Input power budget rises to ~100 W + USB-A 30 W (drives ADR 0001 sizing).
