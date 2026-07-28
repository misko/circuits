---
id: 0004
date: 2026-07-28
status: accepted
tags: [input-protection, protection, topology]
---
# 0004 — Input-protection posture, and what is deliberately ABSENT

## Context

The mandatory protection ADR (pcb-design SKILL, stages 1–3). It must settle
every port through which energy can enter, **including the ports where the
answer is "nothing, and here is why"** — a clean-room run once shipped a board
with zero UVLO because no stage forced the question, and usb-hub-3s-v3 self
drained its supply through always-on EN pins for the same reason.

Energy enters this board through exactly two kinds of port:

| port | what enters | who limits it |
|---|---|---|
| `J_USB` (USB-C, 5 V VBUS) | DC power, USB transients, cable ESD | the host, plus what this board adds |
| `J_ANT1…J_ANT8`, `J_RX1`, `J_RX2` (10 × SMA) | RF, and whatever a user plugs in | **nothing, unless this board adds it** |

Two device limits dominate every decision below, both read from
`02_parts/PE42482A-X/part.yaml` and its datasheet:

- **`V_RFDC` maximum = 0 V** (Table 8 fn 1, PDF p20). Any DC on any RF pin is
  outside absolute maximum. There is no positive headroom to spend.
- **ESD: HBM 1000 V, CDM 1000 V, all pins** (Table 1, PDF p2). That is
  JEDEC Class 1C — **low** for a die wired to ten user-handled coaxial
  connectors, and it is the number that makes the RF-port question real
  rather than theoretical.

## Options

### Power entry (USB-C VBUS)

- **Nothing at all.** REJECTED. The host limits current, but a board-side
  fault then burns on the host's budget, and nothing clamps cable transients.
- **Polyfuse + TVS + ferrite, in that order.** CHOSEN.
- **An eFuse / load switch with OV cutoff.** REJECTED as over-built for a
  ~100 mA bus-powered board: it adds a part class, a fault latch and a
  quiescent draw to protect a rail the host already current-limits.

### RF ports — ESD

- **A shunt inductor or shorted λ/4 stub to ground** (the textbook RF ESD
  drain). **REFUTED, and it fails for the SAME reason the directional
  coupler did (ADR-0002): the mechanism is an electrical length, and this
  band is 85.7 : 1.** A 100 nH shunt is 44 Ω at 70 MHz — a near short across
  a 50 Ω line, ~6 dB of return loss at the bottom of the band. A stub
  resonant at 6 GHz is a 12 mm short circuit at DC-to-low-band.
- **A low-capacitance shunt ESD diode at each launch.** REJECTED — and NOT
  on cost in dB, which is small: at 6 GHz, 0.05 pF is a 530 Ω shunt
  (RL 26.9 dB, IL 0.009 dB) and 0.1 pF is 265 Ω (RL 21.3 dB, IL 0.033 dB).
  It is rejected because it puts **nine ungraded parasitics and nine
  nonlinear elements on the nine paths whose CONSTANCY is this board's entire
  product** (ADR-0006). ADR-0002 measured what one ungraded parasitic costs:
  ±0.02 pF on a single 0402 is a **2.73 dB-wide band of unknown** tap tilt.
  Nine of them, each with its own part-to-part spread and its own mounting
  inductance, is nine unknowns added to the instrument that exists to measure
  unknowns.
- **DNP footprints "provisioned for later".** **REFUTED by arithmetic, not by
  taste**: a vacant shunt pad on a 50 Ω line is itself ~0.05–0.1 pF to
  ground. An unpopulated ESD footprint costs the full RF price and delivers
  none of the protection — strictly the worst of both. (The same refutation
  retired the Ku-ready footprints in ADR-0001.)
- **Nothing on the board, procedure off it.** **CHOSEN.**

### RF ports — DC blocking

- **A series DC block on every RF port.** REJECTED. The block that works at
  70 MHz (10–100 nF) is far past self-resonance at 6 GHz, where an 0402's
  ESL (~0.4 nH, **not a guaranteed datasheet number for the parts JLC
  stocks**) is ≈15 Ω of series reactance: RL 15.5 dB and 0.12 dB of loss per
  port, nine times over, with an ungraded spread on each. Choosing
  PE42482A-X *was* the decision that removed the 85.7 : 1 DC-block problem
  from the signal path (its RF pins need no blocks at 0 VDC); re-introducing
  them discards that.
- **No blocks; the 0 VDC requirement becomes a PORT CONTRACT.** **CHOSEN.**

## Decision

### 1. Power entry — the chain, in order

```
J_USB.VBUS ──[ F_IN 500 mA hold / 1 A trip PPTC ]── VBUS_F ──┬── D_TVS (cathode)
                                                             ├── C_BULK 4.7 µF
                                                             └──[ FB_IN ferrite ]── U_LDO.VIN → 3V3
J_USB.CC1 ──[ R_CC1 5.1 kΩ ]── GND        J_USB.CC2 ──[ R_CC2 5.1 kΩ ]── GND
J_USB.D+/D− ──[ U_ESD 2-ch array ]── GND
```

**The fuse is UPSTREAM of the clamp**, deliberately: a TVS that fails short
must open the fuse rather than burn. **`D_TVS`'s cathode is on `VBUS_F`, not
on VBUS** — this is the exact geometry of the usb-hub-3s v1.0 D1 defect
(cathode on the wrong side of the protection), which passed ERC, DRC, parity,
twin AND pin review because every artifact was consistently wrong together.
It is therefore emitted as a `pin_on_net` invariant, not left as prose.

**`R_CC1`/`R_CC2` = 5.1 kΩ each is a PROTECTION part, not a plumbing part.**
Two 5.1 kΩ pull-downs advertise this board as a plain 5 V sink, which is what
makes the sustained-overvoltage case (a PD source at 9/15/20 V) unreachable
rather than survivable. Its value is machine-asserted for the same reason the
pickoff resistors are: nothing electrical on the board can detect a wrong one.

**THE CLAMP-VS-RATING PAIR, stated as a stage-2 selection CONSTRAINT.** A
5.0 V-standoff TVS of the SMAJ5.0A class clamps at **≈9.2 V at 43.5 A**.
Many popular 3.3 V LDOs are rated **6 V absolute maximum on VIN** — pairing
one with this clamp means *the regulator dies before the protection
conducts*, which is the defect the red-team topology lens hunts by name.
Therefore:

> **`U_LDO` MUST have V_IN(abs max) ≥ 10 V.** Any candidate at 6 V is
> disqualified at selection, not waived at review.

`FB_IN` (a ferrite between the clamped node and the regulator) attenuates the
fast residual; it does nothing for a sustained overvoltage, which is why the
CC pull-downs above and the LDO rating do that job instead.

### 2. RF ports — the posture is a CONTRACT, and the board carries no components

**No ESD devices, no DC blocks, no DNP pads, on any of the ten RF ports.**

What is taken for free, because the part choice already bought it: the switch
is **ABSORPTIVE**, so every deselected port sits at ~50 Ω to ground *inside
the die* in all eight states. Slow triboelectric accumulation bleeds off
rather than building. It does nothing for a fast HBM event, and that is
stated rather than implied.

**The port contract** — printed on silk, repeated in `ORDER_README.md`, and
listed in `CHECKLIST.md`:

> **RX ONLY · PASSIVE ANTENNAS · 0 VDC · NO BIAS TEE · NO TRANSMIT**

with the numbers behind each clause: 0 VDC because `V_RFDC max = 0 V`;
no transmit because CW power is bounded by Figure 2 and **hot-switching by
20 dBm above 100 MHz** — and this board hot-switches 480 times a second by
design.

**One port is partially self-limiting and it is worth knowing which.** The
RX1 pickoff arm (ADR-0002) puts 440 Ω between `J_ANT8` and RF8, so an
accidental 5 V on that jack drives 10 mA into the pin, against 100 mA
straight into a direct port's internal termination. A 10× mitigation, not a
licence.

**Residual risk, named and bounded:** a 1 kV HBM part behind ten unprotected
coaxial ports will eventually meet a charged connector. The exposure is one
$6.09 switch plus rework — not a respin, because nothing else on the RF side
is exposed. Mitigation is procedural (ESD-safe bench, bond shields before
mating, store with shorting caps on the jacks) and is a bring-up checklist
item. **The trigger that reverses this decision**: any field ESD failure ⇒
fit ≤0.05 pF RF ESD diodes at the launches and re-measure and re-publish the
path table, which ADR-0006's mechanism already accommodates.

### 3. What is deliberately ABSENT everywhere else

| absent | why |
|---|---|
| reverse-polarity FET/diode | USB-C is keyed and rotationally symmetric; VBUS and GND cannot be exchanged, and there is no second source. Series resistance and a new failure mode for a fault that cannot occur |
| UVLO / over-discharge | **there is no self-contained energy source.** Nothing to over-discharge |
| master power switch | same. De-energization is unplugging the cable (see E-OFF below) |
| inrush limiter | VBUS bypass is held to **≤10 µF** (USB 2.0 §7.2.4.1); the design budget is 4.7 + 1 + 4×0.1 ≈ **6.1 µF**, so inrush is inside spec by construction |
| OV crowbar / latch | the CC pull-downs make sustained OV unreachable; a crowbar adds a latching failure mode to protect against it |
| RF-port fuses | nothing to fuse — the RF paths carry receive-level power |
| RF-port DC blocks / ESD | above |

### 4. E-OFF — de-energization and stored draw

Emitted to `03_src/rules/power_tree.yaml`:

```yaml
source_type:  usb_bus_powered_5v
off_control:  "unplug the USB-C cable — no self-contained energy source
               is present on the board (ADR-0004)"
quiescent_ua: 0
```

Unplugged, the board holds ≤6.1 µF of ceramic bypass, which the regulator's
own path bleeds in milliseconds. There is no storage self-drain question to
answer, and E-OFF grades this as N-A **for a reason the file states** rather
than by the file's absence.

## Consequences

- **Four invariants are emitted** into
  `03_src/rules/electrical_invariants.yaml` citing this ADR: the fuse
  `series_chain`, the TVS cathode `pin_on_net`, and the two CC-resistor
  `part_value`s. Without them this ADR is prose, and prose is what the D1
  reverse-polarity defect was.
- **A stage-2 part-selection constraint is now binding**: `U_LDO` V_IN abs
  max ≥ 10 V. It goes into the LDO dossier's selection record, not into a
  reviewer's memory.
- **The port contract is a SILKSCREEN obligation**, so it is a placement and
  a silk-generation requirement (P-SILK-FN), not documentation. A board whose
  jacks are unlabelled has no contract.
- **The absent ESD protection is the single largest named risk on this
  board**, and it is a DECISION with a reversal trigger, not an omission.
  Any reviewer who finds it must find this ADR first.
- **If the board is ever re-scoped to transmit** — even at +10 dBm — this ADR
  is void: hot-switching above 20 dBm, the 0 VDC rule under bias, and the
  absent DC blocks all change together.
