# ADR-0001 — input protection for a 5V-over-Cat5e outdoor pod (MANDATORY ADR)

Status: accepted 2026-07-18

## Context

The pod hangs on 30-35 ft of outdoor Cat5e carrying 5V power, a balanced
audio pair, and a switched beeper pair (commission §4). Outdoor cable =
ESD/surge exposure; custom pinout = mis-plug hazard; inductive transducer =
switching kick. The pipeline mandates an explicit protection ADR.

## Decisions

1. **ESD at the cable entry, on the pod (D1 TPD2E2U06DRLR, POPULATED).**
   The source doc lists it "optional"; we populate it (board-local D5):
   ~$0.35 buys IEC 61000-4-2 ±25 kV contact protection for the only
   high-impedance lines leaving the enclosure. The 68R isolation resistors
   sit between the op-amp outputs and the clamp, limiting strike current
   into the OPA1678 (abs max (V+)+0.5V) — strike energy dumps at the entry.
   Rationale for populating: pods are field-installed on stakes, handled
   while charged (walking on grass), and the doc itself mandates "ESD
   suppressors at cable entry" in §4 Termination and safety.

2. **Overcurrent (PTC) lives at the CENTRAL end, not the pod.** The system
   design (§5) puts a MINISMDC050F-2 PTC per port on the central board;
   duplicating it at the pod would double the series resistance in a 5 V
   feed that only drops 4.5 mV today and protects nothing extra: the fault
   that matters (shorted cable or pod) is cleared at the SOURCE end. The
   pod carries NO local fuse. This split is recorded here because a future
   pod-only reuse (different host) must re-add source-end protection.

3. **Reverse/mis-wiring: tolerated by design margins, blocked by labeling.**
   A screw-terminal pod can be miswired. Mitigations: terminal numbering
   matches T568B pin numbers 1:1 (wire straight through), every terminal
   has a plain-word silk label, and the NOT ETHERNET banner is printed
   large. Electrically: swapping 5V/GND reverse-biases only the electro
   C1 through 100R (survivable briefly) — full reverse protection (a
   series diode) was REJECTED because it would drop 0.3-0.6 V from a 5 V
   rail that feeds a 3.9k bias string (noise penalty exceeds risk; the
   central end current-limits the fault).

4. **Beeper clamp (flyback vs TVS): BOTH footprints, flyback shipped**
   (commission A3; see ADR-0002).

5. **Lightning: out of scope** per §4 ("They do not replace lightning
   protection or a storm-disconnection policy") — documented in
   ORDER_README as an operational rule, not a board feature.

## UVLO/OV note

The pod is unpowered-logic (no MCU, no battery): no UVLO/OV circuitry is
applicable. Undervoltage merely lowers VMID; the GST25A05 source and the
central board own rail quality.
