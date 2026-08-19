# ADR-0016 — close the regulator transient budget with a low-loss aggregate eFuse

Status: accepted  
Date: 2026-08-19  
Partially supersedes: ADR-0015 aggregate eFuse, aggregate ILM, feedback trim,
aggregate timing and protected-rail drop assumptions only.

## Context

ADR-0015 corrected the DC setpoint but allocated only 30 mV for ripple and
settled movement, leaving 5.78 mV below the 5.25 V external-output ceiling.
TI's TPS56637 5 V / 6 A reference design specifies a +/-5% load-step target
and its published load-step plots use a 200 mV/div output scale. The board's
smaller load step and larger output bank help, but neither proves that a 30 mV
envelope is safe. The retained TPS259474L also has 45 mOhm maximum RON, which
consumes delivery-floor budget and partly isolates the downstream bulk bank.

## Decision

- Keep the purchased TPS56637 regulator, 3.3 uH inductor and output capacitors.
- Replace only aggregate `U_AGG` with `TPS259804ONRGER` / JLC `C2878936`.
  Its guaranteed 5 mOhm maximum RON over temperature recovers 40 mOhm of
  common-path budget and lets the downstream bulk participate at a much
  shorter time constant.
- Program `U_AGG` with `R_AGG_ILIM=300 ohm`, 1%, 100 ppm/C
  `0603WAF3000T5E` / `C23025`. TI's characterized 300-ohm row is
  4.36..5.66 A; charging resistor tolerance and a 100 C excursion gives
  4.2745..5.7755 A.
- Tie EN/UVLO directly to `P5V_REG`. The selected 4O variant has fixed
  16.9 V typical OVLO, far above this 5 V-only stage. Remove the obsolete
  three-resistor UV/OV string. Tie RETRY_DLY, NRETRY and LDSTRT to GND to
  preserve intentional latch-off and disable handshake. Leave IMON and PG
  open.
- Use `C_AGG_TIMER=6.8nF` C0G and retain `C_AGG_DVDT=3.3nF`. The new device
  bounds blanking to approximately 1.61..6.65 ms and gives about 1.394 V/ms nominal
  output slew, or about 0.351 A into the declared 251.86 uF maximum bank.
- Change `R_PD_FB_A` to 73.2 kOhm, 0.1%, 25 ppm/C
  `RT0402BRD0773K2L` / `C852909`; retain 374 ohm and 10 kOhm. The charged DC
  output window is 4.92511..5.10424 V. Reserve a 100 mV high-side transient
  envelope, leaving 45.76 mV below 5.25 V.
- With 5 mOhm aggregate RON, 18 mOhm common-copper budget, 2.58 A load and
  5% path margin, the common-path drop is 62.307 mV and the protected floor
  is 4.86281 V, above the rounded 4.860 V contract.

## Coordination and recovery

Normal composite demand remains 2.58 A. One port at 1.15404 A plus three at
0.5 A and 0.58 A internal demand is 3.23404 A, leaving 1.04046 A below the
aggregate worst-low threshold. Two concurrent port faults produce 3.88808 A,
still 0.38642 A below that threshold; a persistent broader overload can trip
the aggregate. The worst declared four-port demand is 5.80216 A, above the
aggregate worst-high threshold and below the TPS56637 6.3 A minimum valley
limit by 0.5245 A. Aggregate latch-off still requires cycling USB-C POWER.

## Layout and fabrication consequences

The RGE0024M package is larger than RPW0010A and requires a material PCB
revision. Use TI drawing 4223975/B: split IN pad 25 and GND pad 26, all power
lands connected, and nine 0.20 mm via-in-pad holes at TI's example sites.
Those holes belong to the board's complete IPC-4761 Type VII filled and
copper-capped family. The exact C2878936 native STEP is source-owned and must
pass model-registration review after placement.

## Validation

- Re-run source topology, margin, surge, fault, identity and sourcing gates.
- Capture startup, simultaneous 2 A application/removal and one-port
  disconnect waveforms at `P5V_REG` and the USB-A VBUS lands. The measured
  high peak must remain below 5.25 V and the loaded floor above 4.75 V.
- Verify one-port and two-port overload coordination, aggregate latch-off,
  power-cycle recovery and hot four-wire common-path drop.
- Confirm all nine U_AGG via-in-pad sites as filled/capped in the JLC order
  preview before fabrication.

## Authorities

- TI TPS56637 datasheet SLVSEG1A, 5 V / 6 A reference and load-step plots.
- TI TPS25980 datasheet SLVSFR1A, device table, characterized ILIM row,
  timing/slew equations, RGE0024M package and example land pattern.
- Exact JLC/LCSC `C2878936` EasyEDA CAD and native STEP fetched 2026-08-19.
