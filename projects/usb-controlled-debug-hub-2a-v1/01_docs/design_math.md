# Pre-schematic electrical closure

status: preliminary machine-checked architecture evidence
date: 2026-08-20

## Input power

- Required external output: `4 × 5 V × 2 A = 40 W` nominal.
- Conservative planning load uses the 5.25 V service ceiling:
  `4 × 5.25 V × 2 A = 42 W`.
- At 85% planning efficiency for both 5 V banks, that is 49.412 W input.
- The 3.3 V rail budget is `3.3 V × 0.6 A / 0.85 = 2.329 W`.
- Total planning input is 51.741 W, or 2.723 A at the minimum accepted 19 V.
- A 20 V/3 A fixed PDO therefore has 8.259 W planning margin. A 15 V/3 A
  contract does not.

TPS16630 `R_ILIM=5.90 kOhm` gives 3.051 A nominal from TI's characterized
`18/R_ILIM(kOhm)` relation. Applying a conservative ±8% device spread and
±1% resistor tolerance gives 2.780–3.328 A. This is secondary fault protection;
the standards-compliant PD source owns the exact 3 A source ceiling. The 2.780 A
minimum remains above the 2.723 A planning demand.

## TPS16630 input window

Candidate shared divider: R1=931 kOhm, R2=19.6 kOhm, R3=51.1 kOhm, all 1%.
The corner enumerator varies all three resistors independently, both device
thresholds from 1.176–1.224 V, and both UVLO/OVP leakage currents from
-150 to +150 nA:

| threshold | minimum | maximum | consequence |
|---|---:|---:|---|
| UVLO rising | 16.1171 V | 17.9106 V | 15 V +5% is rejected; 20 V -5% is accepted |
| OVP rising | 22.3402 V | 24.7388 V | below retained TPS56637 28 V recommended maximum |

The directly exposed TPS16630 is rated for 60 V operation and 67 V absolute;
the TVS2200 worst published clamp is 28.35 V.

## Five-volt service window

Each TPS56637 bank uses a candidate 75.0 kOhm / 10.0 kOhm, 0.1% feedback
divider. With TI's 0.591–0.609 V full-temperature reference range, exhaustive
resistor corners give 5.01464–5.18564 V. Reserving 50 mV for line/load/ripple
gives a 4.965–5.236 V regulator service window.

The per-port path budget is 90 mOhm maximum:

| element | maximum/budget | 2 A drop |
|---|---:|---:|
| TPS259804 bank eFuse + TPS259470A port eFuse | 50 mOhm | 100 mV |
| PCB copper, vias and joints | 10 mOhm | 20 mV |
| qualified USB1130 mated contact | 30 mOhm | 60 mV |
| total | 90 mOhm | 180 mV |

The resulting worst planning floor is `4.965 - 0.180 = 4.785 V` at the mated
test plug, 35 mV above the 4.75 V requirement. This is deliberately tight:
post-route resistance extraction and a hot four-wire first-article measurement
are mandatory, and failure backtracks to copper geometry or the service claim.
