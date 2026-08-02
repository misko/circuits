# ADR-0004 — Retain the reviewed power cells at a guaranteed 2 A per port

status: accepted and implemented
date: 2026-08-01
tags: [topology, module-first, power, voltage-margin, gate-drive]

## Context

The first routed LM5116 design was not releasable at 3 A per socket. Its
BSC016N06NS pair had no maximum gate-charge value and consumed 26.75 mA at
250 kHz using the published typical charge, above the controller's guaranteed
15 mA internal-VCC startup limit. The complete 150 mOhm port path also failed
the required voltage margin. The user subsequently authorized lowering the
guaranteed output to 2 A and clarified that module selection should follow
total integration complexity, with a formal comparison for roughly ten or
more external support components rather than an absolute module mandate.

## Module-versus-chip decisions

The LM5116 cells each have many support components, so TPSM64406RCHR was
reconsidered. It can supply a 4 A rail, but adopting it at this backtrack would
replace two already reviewed high-current cells, change package and thermal
geometry, and restart compensation, placement, routing and transient
qualification. The retained cells instead need one drop-in MOSFET substitution,
one RT value change and one series feedback-trim resistor. On total remaining
project complexity, the bare controller is the lower-risk choice.

The USB2517I likewise exceeds the support threshold. Microchip's EVB-USB2517
is a development board with finished USB receptacles, not an embeddable module
that exposes the internal PHY segments and individual PRTPWR/OCS signals used
by this board's data switches and eFuses. The exact IC reference circuit is the
verified integration. The STM32G0B1 needs seven direct support/interface parts,
so the LQFP is a simple bare-IC decision below the threshold.

## Gate-drive correction

Replace Q3-Q6 with exact AON6266E, retaining the AOS DFN5x6_8L_EP1_P land and
pin order. Its Rev 1.1 table guarantees 20 nC maximum total gate charge at
10 V. Change R101/R201 to 34.0 kOhm, which gives 98.95 kHz nominal from the
LM5116 timing equation. The declared 110 kHz frequency includes the datasheet
+10% oscillator corner.

For two switches per controller:

`I = 2 * 20 nC * 110 kHz + 7 mA = 11.4 mA`.

The policy allows 80% of the 15 mA minimum internal-VCC limit, or 12.0 mA, so
the maximum-Qg calculation passes with 0.6 mA remaining. At 24 V input,
5.16 V output, 6.8 uH and the approximately 89 kHz low-frequency corner, the
inductor ripple is approximately 6.6 A peak-to-peak; a 4 A rail therefore peaks
near 7.3 A, below the selected inductor's 15.2 A saturation rating and below
the approximately 10 A current-sense threshold. First-article switch-node,
temperature and transient measurements remain acceptance tests.

## Guaranteed static voltage margin

R102/R202 remain exact 3.92 kOhm 0.1% parts and R103/R203 remain exact
1.21 kOhm 0.1% parts. New 11 Ohm 1% R111/R211 parts are series-connected with
the top legs. The effective 3.931 kOhm top resistance has a conservative
0.1026% tolerance. With the LM5116 1.215 V +/-1.5% reference, the calculated
output is 5.0769 V worst-low and 5.2478 V worst-high.

The complete per-port path is:

| element | maximum |
|---|---:|
| TPS259470 pass FET | 45 mOhm |
| PCB copper, vias and solder joints | 10 mOhm |
| USB1130 VBUS and GND mated contacts | 80 mOhm |
| total | 135 mOhm |

At 2 A with the policy's 20% loss margin, the bounded drop is
`2 A * 135 mOhm * 1.20 = 324 mV`. The mated-test-plug lower bound is therefore
4.7529 V, while the unloaded high corner remains below 5.25 V. R414/R424/
R434/R444 become 1.47 kOhm 1%, giving a nominal TPS259470 limit of 2.268 A,
approximately 2.02 A minimum and 2.52 A maximum with device and resistor
tolerances. The hardware therefore guarantees 2 A without preserving the old
3 A trip setting.

The 10 mOhm board/via/joint allocation is an acceptance limit, not an assumed
fact: pre-release copper extraction must meet it and first articles must pass a
hot four-wire measurement at each socket. The release test plan also covers a
simultaneous 0-to-4 A step on each shared rail.

## Surge coordination

U4 remains AP63203QWU-7. Its exact datasheet permits 40 V for less than 400 ms;
the specified SMBJ24A maximum clamp is 38.9 V at the declared 1 ms waveform.
That cited device limit closes the static coordination gate. Capturing U4 VIN
during first-article surge testing remains required because layout inductance
can add overshoot not represented by the TVS table.

## Consequences

- The board keeps its two independent rails and existing power-cell floorplan.
- Q3-Q6, RT, feedback trim and eFuse limit values change; routing must be
  regenerated and all exact-artifact reviews repeated.
- The release may be called design-complete only after every mechanical gate,
  exact-board adversarial review and fabrication-package gate passes.
