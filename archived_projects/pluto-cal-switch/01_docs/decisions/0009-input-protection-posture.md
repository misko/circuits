---
id: 0009
date: 2026-07-27
status: accepted
tags: [protection, input-protection]
---
# 0009 — Input protection: what is fitted, and what is deliberately absent

## Context

This is the mandatory input-protection ADR (SKILL.md stage 1-3). The board has
**two** entries, not one, and the reflexive protection budget would be spent on
the wrong one.

1. **micro-USB VBUS** — keyed, single-source, 4.40–5.25 V from a host.
2. **the GPIO header** — **UNKEYED**, user-wired, and the realistic miswire
   path: somebody lands it on a Pluto GPIO at 1.8 V, or reverses it, or
   back-feeds 3V3 into it.

E-OFF is **N-A**: the board's only energy source is the USB host. Unplugging
the cable de-energizes it completely. There is no cell, no pack, and no stored
charge beyond ~6.8 µF of ceramic. `source_type: usb` in `power_tree.yaml`.

## Options

Considered per element, with the rejections stated as decisions rather than
omissions.

- **Reverse-polarity P-FET on VBUS.** REJECTED. Micro-B is mechanically keyed
  and is the SOLE power entry; there is no second source to reverse. Contrast
  `crow-recorder-central` ADR-0002, which DID fit an AO3401A — but only because
  a DNP screw terminal in parallel made miswiring physically possible. That
  condition does not exist here. Fitting one costs a part and a rail drop for a
  fault that cannot occur.
- **Dedicated power TVS / crowbar on VBUS.** REJECTED, KNOWINGLY. The ME6211's
  VIN absolute maximum is 6.5 V against a host's 4.40–5.25 V, and the USBLC6's
  VBUS diode (VBR ≥ 6 V @1 mA) clamps hot-plug transients. **HONEST CAVEAT:
  that is an ESD diode, not a power TVS. It will NOT survive somebody feeding
  12 V into the micro-B.** Surviving that needs an SMBJ5.0A-class TVS *and* the
  PPTC to crowbar — because a 5 V TVS clamps around 10.3 V, above a 5 V load's
  ceiling, so the clamp alone does not disconnect. For a bench adapter the
  exposure is taken deliberately.
- **UVLO.** REJECTED — no battery to over-discharge.
- **Common-mode choke on the USB pair.** NOT FITTED, but see the ground-loop
  consequence below.

## Decision

### Fitted on the USB entry

| element | value | why |
|---|---|---|
| `U_ESD` USBLC6-2SC6 (C7519) | — | D+/D−/VBUS ESD in one SOT-23-6, at the connector. Non-negotiable on a bench instrument whose cable a human handles daily |
| VBUS bulk | 4.7 µF + 100 nF | see the hard ceiling below |
| `F1` PPTC | ~500 mA hold | **protects the HOST, not this board.** A shorted rail here must not kill the laptop USB port. That is the failure that actually costs money |
| `FB1` ferrite | 600 Ω @100 MHz | the USB cable is a ~1 m antenna galvanically bonded to the RF ground system; keeps host-side common-mode junk off the 3V3 that biases the switches. 10 mV drop at 100 mA |

**VBUS BULK IS CAPPED AT 10 µF TOTAL, AND THIS IS A SPEC LIMIT, NOT A
PREFERENCE.** USB 2.0 §7.2.4.1 "Inrush Current Limiting", verbatim: *"The
maximum load (CRPB) that can be placed at the downstream end of a cable is
10 µF in parallel with 44 Ω… If more bypass capacitance is required in the
device, then the device must incorporate some form of VBUS surge current
limiting."* Budget: 4.7 µF + 100 nF at the connector + 1 µF at the LDO input +
1 µF at the LDO output = **6.8 µF**, compliant with **zero soft-start parts**.
This is the constraint people silently violate by adding "one more 10 µF".

**Shell grounding: tie the connector shell and its two THT legs DIRECTLY to
GND, with no R/C isolation network.** On an RF board the SMA grounds, the board
ground and the cable shield must be one system; a split here creates exactly
the common-mode path the design is trying to avoid.

### Fitted on the GPIO header — where the budget actually goes

| element | value | why |
|---|---|---|
| series R on `HDR_CTRL_IN` | 2.2 kΩ | also the top of the ÷2.5 divider (ADR-0008). Bounds a reverse fault to 0.45 mA |
| shunt R to GND | 3.3 kΩ | divider bottom, and the pull-down that makes an unconnected header read antenna mode |
| 2-channel bidirectional ESD clamp (TPD2E2U06DRLR class, SOT-553) | — | the ledger's part; shipped on three boards in this fleet |
| series R on `HDR_STATE_OUT` | 1 kΩ | emulated open-drain; cannot exceed the user's pull-up rail |
| **3V3 is NOT exported** on the header | — | a back-feed must not be able to fight the LDO. If the user later needs it, export it through a series Schottky |

**Spending the protection budget on the header rather than on a
reverse-polarity FET behind a keyed connector is the correct allocation**, and
it is the opposite of what a checklist would produce.

### The property this board keeps for free

BRIEF tension T2 works in our favour: with ON = loopback, an unpowered or
floating control line defaults to **antenna**, the safe state. The 10 kΩ
pull-downs at each switch CTRL pin (ADR-0001) preserve it even with the 3V3
rail dead.

## Consequences

- **Emits netlist invariants** (`03_src/rules/electrical_invariants.yaml`,
  canon E-INV): the PPTC is genuinely in series with VBUS; the ESD part is on
  the D+/D− nets; the CTRL pull-downs exist AND are bounded in value.
- **The 12 V-into-micro-B exposure is accepted and must be stated in the
  ORDER_README / first-power ritual**, not left implicit.
- **A SECOND USB CABLE MAKES THIS FIXTURE A GROUND BRIDGE — and nothing here
  fixes it.** The board's RF ground is already bonded to the Pluto through
  three coax shields and to the antenna system through two more. Plug this
  board's micro-USB into the same host that runs the Pluto and the loop closes:
  host GND → Pluto USB → Pluto RF GND → coax shields → this board's RF GND →
  this board's USB → host GND. At 70 MHz–6 GHz that loop carries common-mode
  current whose coupling is **cable-position-dependent — i.e. it differs
  between the calibration run and the measurement run.** That is precisely the
  error a calibration fixture exists to remove.
  **Mitigations, none of them free, all deferred to the user:** power the board
  from a separate supply or a USB isolator; or add a common-mode choke on the
  USB pair plus an explicit shield-grounding strategy. **Flagged to the user;
  not designed in, because the right answer depends on their bench.**
- **The LDO's thermal margin is the one number that is not comfortable at the
  envelope.** At the USB high limit 5.25 V and the 100 mA design envelope,
  ME6211 dissipation is 195 mW against a SOT-23 rating of 300 mW (65 %, with
  no ambient stated for that figure). At the realistic ~60 mA it is 117 mW
  (39 %). **If the load ever exceeds ~120 mA this part is WRONG** and must
  escalate to SOT-89 (XC6227C331PR-G, C6035451, 500 mW) or to a buck. Recorded
  in `power_tree.yaml` as a 0.10 A envelope so the number is visible.
- **ME6211 `CE` must be tied to VIN explicitly.** Its Figure 2 typical
  application (p.2) shows CE tied to the VIN node, and the datasheet **never
  states whether the C series has an internal pull-up or pull-down** — so a
  floating CE is undefined power-up behaviour. This is the same class as the
  ledger's XC6227 note, except there we at least get told which way it fails.
- **The micro-USB THT "PCB LEG" anchors are OVAL SLOTS (~1.00 × 1.70 mm), not
  round drills.** If the footprint emits them as round holes, as NPTH, or omits
  them, the entire mechanical-retention argument for choosing that connector
  evaporates and it becomes a pure-SMT part that tears off. Check the drill/slot
  report and the plated attribute before release, as a gate rather than by eye.
