# ADR-0015 — use characterized current limits and coordinate the PD clamp

Status: accepted  
Date: 2026-08-19  
Partially supersedes: ADR-0014 external-port and aggregate ILM values, direct
input bypass value, feedback trim, and SMF16A protection coordination.

## Context

The v0.1.2 adversarial review found four coupled problems:

1. The 5.90 kOhm port setting was analyzed with the greater-than-1 A ±10%
   accuracy statement even though TI provides separate low-current
   characterized rows. It did not guarantee 500 mA service.
2. Raising the local limit without reselecting the aggregate breaker could
   make the wrong protection stage trip during a single-port fault.
3. The 5.24667 V DC feedback high corner left only 3.33 mV below the 5.25 V
   output ceiling before ripple or settled line/load movement.
4. The SMF16A proof compared its 26 V clamp with the downstream regulator's
   32 V limit, overlooking the upstream TPS259470A input's 28 V limit.

## Decision

- Program `U_PWR1..4` with 3.32 kOhm, 0.1%, ±25 ppm/C
  `RT0603BRD073K32L` / `C861376`. TI characterizes the 3.32 kOhm row at
  0.850–1.150 A. Charging that row for 0.1% initial tolerance and a 100 C,
  25 ppm/C excursion gives 0.84704–1.15404 A. `ITIMER` and `DVDT` remain open
  intentionally: TI explicitly defines that as minimum fault delay and fastest
  turn-on. Capacitive startup and short behavior remain first-article gates.
- Program `U_AGG` with 750 Ohm, 1%, ±50 ppm/C
  `AR03FTDX7500` / `C412394`. TI characterizes that row at 3.96–4.84 A;
  the charged range is 3.90148–4.91371 A.
- Preserve the 2.58 A normal composite contract. One port at its worst-high
  limit plus three 0.5 A ports and 0.58 A internal demand is 3.23404 A, leaving
  0.66744 A below the aggregate worst-low threshold. Two concurrent faults
  may intentionally trip the aggregate latch. Cycling USB-C POWER is the only
  recovery path because latch-off removes the management plane.
- Keep all three feedback elements in Yageo's RT0402BRD 0.1%, 25 ppm/C
  family: change the 75 kOhm upper element to `RT0402BRD0775KL` / `C728563`,
  replace the second 1 kOhm segment with 374 Ohm
  `RT0402BRD07374RL` / `C852745`, and retain the 10 kOhm lower element
  `RT0402BRD0710KL` / `C190095`. The topology is unchanged. The 0.591–0.609 V
  reference plus initial tolerance and a 25 C resistor-temperature excursion
  yield 5.03115–5.21422 V. This balances the charged simultaneous-load
  delivery constraint with a 30 mV steady-state ripple/settling allocation and
  leaves 5.78 mV below 5.25 V. The product is qualified for 10–40 C bench
  ambient; wider-temperature performance is not claimed. First article
  separately bounds startup and load-release peaks.
- Replace SMF16A with `TVS1800DRVR` / `C2649846`. TI specifies an 18 V
  standoff and a 24.7 V maximum clamp at 35 A, 8/20 us and 125 C, leaving
  3.3 V of tabulated margin below the 28 V `U_PD_IN` absolute maximum.
- Increase the directly exposed input damping capacitor to 1 uF, 50 V, X7R
  `TCC0603X7R105K500CT` / `C5360793`. It remains below the Type-C 10 uF sink
  attach ceiling; the two 10 uF regulator capacitors remain switched behind
  `U_PD_IN`.

## Consequences and validation

- This is a material PCB revision because the TVS changes from SOD-123FL to
  WSON-6 and the input capacitor changes from 0402 to 0603. Regenerate and
  re-route from authoritative sources; do not patch a sealed release.
- Measure cable attach, source disconnect, downstream-short interruption and
  abnormal-source waveforms directly at the `U_PD_IN` pads. The measured peak
  must remain below 28 V and within the TVS1800 pulse envelope.
- Verify all four 0.5 A loads simultaneously, capacitive startup, one-port
  overload selectivity, two-fault aggregate latch-off, and power-cycle-only
  recovery over representative temperature and more than one eFuse lot.
- The release remains hardware-only. No firmware or host package is inferred.

## Authorities

- TI TPS25947 datasheet SLVSFC9C, characterized ILM table, pin descriptions,
  absolute maximum table and equations.
- TI TVS1800 datasheet SLVSEV7B, electrical characteristics and DRV package.
- TI, *ESD and Surge Protection for USB Interfaces*, 15 V USB-PD protection
  example using TVS1800.
- USB Type-C sink attach capacitance requirement cited by ADR-0014.
