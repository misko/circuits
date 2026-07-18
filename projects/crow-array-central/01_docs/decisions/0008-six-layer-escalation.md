# ADR-0008 — escalate to 6 layers (ADR-0004 revisit trigger fired)

Status: accepted 2026-07-18. Supersedes ADR-0001's 4-layer choice (D3);
invokes ADR-0004's explicit revisit trigger ("If the part had been ... this
would have been a package-change ADR ... recorded so the reasoning
survives" — and the routing-order note: escape saturation -> revisit).

## Context — 4-layer escape saturation (measured)

The board (XU316-1024 TQ128 129-pin + 8 RJ45 ports + dual PCM1865 + power)
would not close routing on 4 layers (F / In1 GND / In2 / B = 3 signal
layers over one GND plane), across many placement and net-ordering attempts:

- **Power-first** (In2 power, then signals): 16 XU316 3V3/0V9 IO pins boxed
  when signals then claimed the escape annulus; 2 could never route (via
  sites blocked on ALL layers at the 0.4mm pitch).
- **Signal-first** (USB/clock/beeper early, power second): the distributed
  XU316 power pins boxed instead.
- **Board grown 104 -> 122mm** (D18, ADC↔XU316 gap 10 -> 23mm, decoupling
  annulus widened): improved the deficit from ~6 to ~2-5 nets but did NOT
  close it.
- Final 4L deficit reproduced every reconcile pass (3..9): **BEEP_G3/G5/G7
  + I2C_SCL/I2C_SDA** — the router oscillates (BEEP_G1<->BEEP_G3 rip-up
  swap) around a corridor that fits ~5 of the 8 beeper-gate wires.

Two structural facts make this a topology limit, not router tuning:

1. **The XU316 escape competes with power globally.** ~90 used pins fan
   out of a single TQ128 into an annulus that must ALSO carry the
   distributed-power taps (3V3 47 pins / 0V9 35 pins, interleaved on every
   edge at 0.4mm — D15 showed no clean In2 plane partition is possible).
   Whichever of {signal, power} routes first boxes the other.
2. **The 8 beeper-gate control lines must cross the analog band.** The
   beeper FETs sit at the north edge (with the jacks, for a short current
   return — ARCHITECTURE), their gates are driven from the XU316 at the
   south, so 8 wires fan from the XU316 east edge to gate resistors spread
   across the full board width at the port row — straight through the ADC /
   coupling / audio corridor. That both saturates the corridor AND pushes
   beeper copper into the analog band the layout is meant to keep clear.

This is precisely golden-rule R4/R5 territory: the fix is layers/topology,
not iterations. Per ADR-0004 the sanctioned response to escape saturation
is escalation, recorded with an ADR rather than shipping unrouted copper.

## Decision — 6-layer stackup (JLC 6L standard tier)

```
F.Cu   signal
In1.Cu GND plane  (reference)
In2.Cu signal
In3.Cu signal
In4.Cu GND plane  (reference)
B.Cu   signal
```

**4 signal layers** (F / In2 / In3 / B), each with an adjacent GND plane
(In1 or In4) for a clean reference — better SI than the 4L board had. GND
is not routed (In1+In4 planes + F/In2/In3/B pours + stitch vias). Power
stays floored TRACKS distributed across the 4 signal layers (D15 unchanged —
the rails are still spatially intermixed; the extra signal layer is what
buys the escape headroom). The added In3 signal layer + the second GND
plane give the beeper-gate bus and the I2C bus their own lanes without
starving the XU316 power escape.

The brief permits 4-6 layers (D3 chose 4 as the cost-minimal option that
"passed the gate" — it does not, so 4 is withdrawn). JLC 6L standard tier
(0.45/0.3 vias, no advanced small-via option) still applies — the escape
geometry (ADR-0004) is unchanged; only the layer budget grows.

## Consequence

- Cost rises vs 4L (6L bare-board multiplier at JLC ~1.6-2x the 4L price
  for this size) — reported in the release cost headline; the board is
  now ROUTABLE at standard tier, which 4L was not.
- generate_board emits 6 copper layers + GND zones on all six (In1/In4
  full-connect planes); route_waves routes on F/In2/In3/B; stitch bonds
  all six GND layers and checks via sites on all six; export ships In1-In4
  in the layer PDF. Netlist parity unchanged (placement/nets identical).
- If 6L still could not close (it does), the next lever would be a package
  change (XU316 is fixed by the commission) or board growth — not needed.
