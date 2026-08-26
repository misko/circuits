---
id: 0001
date: 2026-07-23
status: accepted
---
# 0001 — Protection & grounding (mandatory input/protection ADR)

## Context
The pod sits at the far end of a 25 ft OUTDOOR Cat5e run and has no local
energy source: it is powered (5V_AUDIO / GND_AUDIO), referenced, and — for
calibration — driven (5V_BEEP / BEEP_SWITCHED_RETURN) entirely from the
central board. The exposures that need a protection decision:
(1) ESD/surge on the exposed audio outputs and rails; (2) the inductive
kick of the CMT-8504 magnetic transducer when central opens its low-side
switch; (3) whether the switched beep return may share the analog ground;
(4) cable-shield bonding; (5) reverse polarity on the power rails.

## Options & decisions
1. **ESD** — A: no ESD (REJECTED — outdoor cable is the surge aperture).
   B: TPD2E2U06 on the two exposed audio pins to GND_AUDIO (ACCEPTED — the
   brief's named part; 2 channels exactly cover AUDIO_P/AUDIO_N; working
   voltage 6.5–8.5V VBR clamps ESD while passing the ±<2V audio swing).
   Placed hard against J1's audio tails, connector-side of the coupling
   caps (protect the physical pins, D-ADJ). Rails 5V_AUDIO/5V_BEEP rely on
   the central's protection + bulk caps here.
2. **Inductive flyback** — A: none (REJECTED — the transducer is inductive;
   opening the low-side switch flies BEEP_SWITCHED_RETURN high and can punch
   the central FET / radiate). B: freewheel Schottky at the driven end
   (ACCEPTED — SS14 D2, cathode→5V_BEEP, anode→BEEP_SWITCHED_RETURN;
   40V/1A ≫ 5V/150 mA; clamp AT the pod per the ledger gotcha). A SMAJ6.0A
   (D3) over-clamp is provided for field surge margin, same net orientation
   (cathode→5V_BEEP). **AMENDED 2026-07-23 (fix pass, D5): D3 is now
   POPULATED, not DNP.** It was DNP in the release-candidate; the 4-lens
   red-team (P0-D) found the resulting BOM-with-code-but-no-CPL state is an
   assembly-file defect (JLC's validator bounces a BOM line with no matching
   placement, and a parity-clean end-to-end DNP is not a proven JLC path
   because the tscircuit converter hardcodes symbol in_bom=yes/dnp=no).
   Populating D3 is parity-clean, costs ~$0.05 (extended tier), and is
   electrically fine: D3 is a redundant TVS over-clamp in parallel with the
   SS14 flyback (both cathode→5V_BEEP), no conflict — during flyback D3
   forward-conducts alongside D2, and it additionally clamps a >6 V positive
   surge on 5V_BEEP. The DNP-alternate rationale is retired.
3. **Beep-return isolation** — the 5V_BEEP / BEEP_SWITCHED_RETURN pair is
   NOT bonded to GND_AUDIO anywhere on the pod (they meet only at central).
   ACCEPTED — keeps the 150 mA switched burst current off the analog
   ground (G8). The flyback loop is entirely within the beep pair.
4. **Shield** — RJ45 shield/tabs FLOAT at the pod; the cable shield is
   single-point-ground bonded at the CENTRAL star ground. ACCEPTED (revised
   from an earlier pod-end bond): six ~25 ft outdoor home-runs bonded at
   BOTH ends would form six ground loops; single-point at central is the
   correct topology and drains every shield to one reference. Consequence
   for THIS board: the RJ45 "SH" shield pads and the unused jack-LED pads
   (9-12) carry NO net at the pod — they are intentionally unconnected.
   (Secondary benefit: "SH" is exactly the alphanumeric pad tscircuit drops
   silently — not authoring it sidesteps that trap with no vendored
   footprint.)
5. **Reverse polarity AND power injection on pod power** — A: series P-FET /
   Schottky (REJECTED — ~5 mA load makes a 0.3V Schottky drop or a FET
   pointless cost/area; nothing to protect a ~$0.10 op-amp against in a
   keyed, labeled, fixed install). B: rely on the keyed RJ45 + mandatory
   "NOT ETHERNET" labeling + controlled install (ACCEPTED, BRIEF D3/A1 —
   signed off by the user). The ESD arrays clamp reverse TRANSIENTS; a
   sustained reverse-plug or power injection is prevented administratively,
   not electrically.
   **AMENDED 2026-07-23 (fix pass): this decision originally analysed only a
   reversed-polarity plug and CONFLATED it with "wrong device plugged in."**
   The 4-lens red-team (P0-A/B, P1-E) showed the real dominant hazard is
   POWER INJECTION: the pod's 5V_AUDIO/GND on contacts 4,5/7,8 alias exactly
   onto 802.3af/at Alternative-B PoE, so a PoE switch drives 44–57 V straight
   into U1 V+ (abs-max 40 V) with ZERO series impedance, and Mode-A PoE forces
   D1 into sustained ~13 W conduction. A hand-crimp swap of 4/5↔7/8 puts V+
   below V−. NONE of these are covered by "keyed connector" (keying stops a
   *different connector*, not a switch on the same RJ45 or a mis-crimped
   cable). This exposure is ACCEPTED as a documented deployment-constraint
   waiver — the hazard, the controlled-deployment mitigation, and the residual
   risk are in **ADR-0005** (USER sign-off A1). No protection network, no
   re-pin, this rev.

## Consequences
- No on-board energy source ⇒ E-OFF is N-A (power_tree source_type =
  external). De-energized by unplugging the cable / powering down central.
- D2 AND D3 are both populated at build (D5, 2026-07-23) — both in the BOM
  and the CPL, both cathode→5V_BEEP. (D3 was DNP in the release-candidate;
  populated in the fix pass to resolve the P0-D assembly-file defect.)
- The beep-pair isolation is a PLACEMENT + ROUTING invariant, not just a
  net fact: keep the beep loop in the SW corner, return straight to J1.

## Invariants emitted (E-INV / E-ADR)
Into `03_src/rules/electrical_invariants.yaml`, each citing adr 0001:
- `pin_on_net` D2.1 = 5V_BEEP (SS14 cathode/band on the supply rail — the
  polarized-2-pad class; a reversed flyback shorts the rail).
- `series_chain` [5V_BEEP, LS1, BEEP_SWITCHED_RETURN] (the transducer
  bridges the two beep nets — the drive loop exists as designed).
- `net_has_part` AUDIO_P carries a diode (the ESD array D1 clamps the hot
  output pin).
- `net_has_part` 5V_AUDIO carries a capacitor (rail decoupling present).
