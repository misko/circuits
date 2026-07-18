# ADR-0007 — Q9 reverse-polarity P-FET orientation (corrects ADR-0002 text)

Status: accepted 2026-07-18 (electrical correction of an internal
inconsistency in ADR-0002; flagged for the dedicated pin reviewer)

## Context

ADR-0002 specifies the reverse-polarity guard as "Q9 AO3401A P-FET
(drain toward load, gate to GND via 100k; **body diode conducts first,
FET then shorts it**)". Those two clauses are electrically inconsistent:

- The AO3401A is a P-channel MOSFET. Its intrinsic body diode has its
  anode at the DRAIN and cathode at the SOURCE (conducts drain->source).
- "Body diode conducts first, FET then shorts it" describes the correct-
  polarity power-up path: current must flow input -> load THROUGH the body
  diode before Vgs establishes and the channel enhances. For that current
  to flow input->load through a P-FET body diode (drain->source), the
  DRAIN must be on the INPUT side and the SOURCE on the LOAD side — the
  opposite of the literal "drain toward load".

The reversed-Schottky incident in the fleet audit (a self-consistent
polarity flip that no ERC/DRC/parity/LVS check can see) is exactly this
failure class. So the assignment is decided by the datasheet body-diode
figure, not by prose.

## Decision (D-CAC-9 in BRIEF.md)

High-side P-FET reverse guard, oriented by the AO3401A body diode:

- **SOURCE (pad 2) = 5V (load rail)** — the output.
- **DRAIN (pad 3) = 5V_P (input, from PTC F1 + TVS D9)**.
- **GATE (pad 1) = GATE9 -> R90 100k -> GND**.

Correct polarity: at power-up the body diode (drain=input -> source=load)
conducts and powers the load through ~0.7V; once the rail is up,
Vgs = Vgate(0) - Vsource(~5V) = -5V << Vth(P), the channel enhances and
shorts the diode (~10mV at 1.2A). Reverse polarity: source goes negative,
Vgs >= 0, channel off, body diode reverse-biased -> blocks. Vgs abs-max
+-12V is not exceeded at a 5V input (no gate divider needed, per ADR-0002).

This **supersedes ADR-0002's literal "drain toward load"** while keeping
its intent (a P-FET reverse guard with a 100k gate-to-GND resistor and no
UVLO). generate_schematic.py wires Q9 as {2:5V, 3:5V_P, 1:GATE9};
audit_board.py I9 asserts it; the dedicated pin review MUST re-derive it
from the AO3401A datasheet body-diode figure before any order.

## Consequence

The board's only reverse-polarity element is Q9. The DNP KF128 terminal
(J11) is the miswire-prone entry; the barrel (J9) is keyed. Both sit
behind F1 (PTC) + D9 (TVS) + Q9, so a reversed terminal input is blocked
by Q9 and clamped by D9.
