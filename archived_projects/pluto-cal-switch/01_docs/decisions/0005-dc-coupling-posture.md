---
id: 0005
date: 2026-07-27
status: accepted
tags: [protection, topology]
---
# 0005 — No DC blocks on the calibration path; blocks on the antenna ports only

## Context

Both candidate switches state, verbatim and identically:

> `Maximum DC-voltage on RF ports and RF-Ground, V_RFDC, Min 0 / Max 0 V —
> "No DC voltages allowed on RF-Ports"`
> footnote 1: *"There is also a DC connection between switched paths. The DC
> voltage at RF ports V_RFDC has to be 0 V."*

(BGS12WN6 Table 1, PDF p4; BGS12P2L6 Table 2, PDF p4.)

Combined with the resistive delta splitter — which is DC-continuous between
all three of its ports — this means **every RF port on both switches and all
three splitter ports are ONE galvanic node**. A single DC fault anywhere
violates the rating on both switches at once. The sourcing spike recorded this
per-part and never noted that the topology makes it board-wide.

The counter-pressure is that a DC block spanning **85.7:1** is genuinely hard.
No single capacitor value is good at both ends: 1 nF is 2.27 Ω at 70 MHz but
inductive at 6 GHz; 100 pF is 22.7 Ω at 70 MHz. Avoiding that problem was one
of the three reasons the switch was chosen.

## Options

- **Blocks on all three RF ports of both switches (6 caps).** The reflexive
  answer, and the one an external datasheet reader proposed. REJECTED: it puts
  a capacitor in the CALIBRATION path — the one path whose flatness is the
  product — costing ~0.05 dB and a ~16.5 dB local return loss at 6 GHz per
  block, twice per loopback run. It also solves a problem that does not exist
  on the Pluto-facing ports.
- **No blocks anywhere**, relying on the datasheet's own "No blocking
  capacitors required if no DC applied on RF lines". REJECTED: the proviso is
  CONDITIONAL, and the two `RX_ANT` ports are user-facing SMA jacks into which
  anybody can plug an active antenna or a bias-tee'd LNA.
- **Blocks on the two ANTENNA ports only.** CHOSEN.

## Decision

**Fit a 1 nF 0402 C0G/NP0 50 V DC block in series with `RX_ANT1` and
`RX_ANT2`. Fit nothing on the loopback path or the three Pluto-facing ports.**

The proviso is satisfied by DERIVATION, not by hope. **The YAT attenuator pads
DC-reference the whole internal RF node to ground.** A DC–18 GHz absorptive
thin-film pad is a resistive pi with through-wafer vias to ground; for a 10 dB
pi, R_shunt ≈ 96.2 Ω and R_series ≈ 71.2 Ω, so **each RF port of each pad
presents ≈70 Ω of DC resistance to ground**. With PAD_A1 and both PAD_A2
chains in the network, **the entire internal RF node sits at 0 V DC by
construction**, and `V_RFDC = 0` is satisfied without a single capacitor on
the calibration path.

Realised block performance:

```
70 MHz: Xc = 2.27 Ω  → |Γ| = 0.0227 → RL 32.9 dB, IL 0.002 dB
6 GHz:  0402 ESL ≈ 0.4 nH → net +j15.0 Ω → |Γ| = 0.150 → RL 16.5 dB, IL 0.05 dB
```

1 nF is the best compromise across 85.7:1 (100 pF gives RL 12.9 dB / IL
0.22 dB at 70 MHz — worse at the bottom). 0402 is specified over 0201 for
assembly robustness on a low-volume bench board; **0201 is the documented
upgrade** (ESL ≈ 0.25 nH ⇒ +j9.4 Ω ⇒ RL 20.6 dB, 4 dB better) if measured
antenna-port return loss disappoints.

## Consequences

- **The calibration path carries no capacitor.** The switch's DC-through
  property is fully banked, which was one of the three reasons it was chosen
  (ADR-0002).
- **The antenna path pays 0.05 dB and 16.5 dB of local return loss at 6 GHz.**
  Both are COMMON to the two channels, so they cancel in the arm-to-arm
  comparison the board exists to make.
- **No floating island.** Because the pads DC-reference the node, the delta
  does not become a DC-floating island and needs no bleed resistor — a real
  hazard on a board with five user-accessible ports had blocks been fitted on
  all sides instead.
- **STILL OPEN (O6): nobody has ASSERTED that the PlutoPlus RX/TX SMA ports
  are DC-free.** They are almost certainly balun-coupled, but the PlutoPlus
  schematic names no connector part and no one has measured it. **If they are
  not DC-free, blocks become mandatory on the three SMP ports too**, and the
  calibration path inherits ~0.05 dB and a 16.5 dB local return loss at 6 GHz
  per block. This is a five-minute meter check on the physical hardware and it
  should be done before the board is fabricated.
- Reverses the sourcing spike's own mitigation, which proposed 1 nF **0201**
  on the switch ports. Its arithmetic was right and its placement was wrong:
  the parts that need protecting from DC are the ones facing the USER, not the
  ones facing a known instrument.
