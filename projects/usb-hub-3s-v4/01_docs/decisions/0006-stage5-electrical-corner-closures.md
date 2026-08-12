---
id: 0006
date: 2026-08-11
status: accepted
---
# 0006 — Close exact current-limit, capacitance, gate-bias and fuse corners

## Context

The Stage 5 fresh-context topology review rejected four assumptions that had
survived the schematic and routed-board gates. TPS2557 with 39.2k could not
both guarantee the inherited 2.5A peak and remain within the USB1130 3.0A
rating. The reverse-FET proof ignored the specified +/-10uA gate leakage and
credited the -10V RDS(on) value without guaranteeing that drive. The selected
47uF MLCC source provided no DC-bias curve, so its nameplate total could not
prove either the TPSM63610 75uF effective minimum or TPS25810 120uF cold-socket
minimum. The fuse holder was exact, but the replaceable fuse element was not.
The same review found that the power-tree calculations omitted divider TCR and
FB bias current, and that the USB-A connector resistance counted only one
contact even though the load loop contains both VBUS and GND.

## Decision

Use one TPS2559DRCR per USB-A port with exact 43.2k +/-0.1%, +/-25ppm/C ILIM
programming. Scaling TI's characterized 44.2k row and charging a 100C resistor
excursion gives 2.554A worst-low and 2.849A worst-high. This preserves the
2.5A short peak and remains below the exact connector's 3.0A rating.

Use a 200k:100k Q1 source-to-gate-to-ground divider, implemented as R22=100k,
R23=100k and R1=100k, with D5 retained only as a secondary transient clamp.
With resistor tolerance and Q1's full +/-10uA gate leakage, the 9V corner still
guarantees 5.29V drive. At the rail-TVS coordination corner of 29.28V, worst
|VGS| is 20.31V versus the 25V absolute limit. Grade Q1 loss using the 17mohm
maximum guaranteed at -4.5V, not the 9.5mohm -10V value.

Replace the uncharacterized 47uF MLCCs with exact TDK
C3225X7R1C226KT000N 22uF/16V X7R parts. Six at U1 give 80.784uF effective and
three at U2 give 40.392uF after -10% tolerance, a conservative 20% DC-bias
loss and 15% X7R temperature loss. These close TI's 75uF and 30uF effective
ceramic minima. Fit TI's recommended 22pF CFF on both modules; U1 also uses the
required 4.99k series RFF. Retain C22 as extra U1 bulk. At its life corner C23
contributes 115.2uF; together with C9-C11 the TPS25810 cold-socket bank is
155.592uF against 120uF required.

Use R11=41.2k +/-0.1% in series with R24=430 ohm +/-0.1%. Grade U1 against
TI's electrical-table +/-1.5% reference limit and U2 against TPSM63604's
full-junction-temperature +/-1.0% feedback-system accuracy. Charge independent
25ppm/C TCR in both divider legs over 100C and 0..50nA FB bias. The resulting
windows are 5.015-5.228V for 5VA and 5.083-5.246V for 5VC_RAW.
With a nominated <=0.4m 16AWG cable qualified to <=14mohm round-trip, the full
89mohm delivery path retains about 12mV beyond its explicit 20% residual margin
and stays within the project's 5.25V Pi supply ceiling.

Count USB1130 contact resistance twice: one 30mohm maximum VBUS contact plus
one 30mohm maximum GND contact. The complete USB-A board-connector path is
therefore 101mohm. At 2A continuous it retains about 22mV after the 20%
residual margin. The 2.5A short peak retains about 12mV without claiming that
same residual; its duration remains a load-step and thermal qualification.

Name Littelfuse 0297010.WXNV as the exact user-installed 10A MINI blade in the
Keystone 3568 holder. Its 32V/1000A interrupt rating is accepted only when the
selected pack's prospective fault current is confirmed below 1000A. Limit the
fuse-holder local ambient to 60C for the admitted current envelope. No available
time-current/I2t proof coordinates the fuse to Q1 or the power modules, so the
claim is catastrophic pack-wiring/trunk protection only, not semiconductor
protection.

## Consequences

ADR-0007 later supersedes R24=430ohm with 300ohm, adds U9 aggregate fault
coordination and updates the delivery budgets. ADR-0008 supersedes the CFF
population after the next fresh review applied TPSM63610's explicit ESR-zero
prohibition to the added polymer output capacitor. The calculations below remain
the dated decision basis that the exact pre-route review challenged; they are
not the current release values.

This is an intentional Stage 5 backtrack: the schematic, placement and route
must be regenerated and every exact-artifact review repeated. The design gains
characterized ceramic banks, feed-forward parts, two gate resistors, a larger
port-switch footprint and a new Type-C feedback value. The normal
continuous/peak input bounds become 5.817A/6.785A; Q1's conservative peak loss
becomes about 0.78W and therefore
remains a mandatory hot first-article measurement. JLC stock remains volatile
and every exact catalog selection must be refreshed at release.

### Machine-readable bound amendment — effective U1 ceramic bank

This declaration makes the still-current ceramic-bank result independently
regenerable from the adopted rule inputs. It does not revive the superseded
feed-forward population discussed above.

<!-- bound: U1_EFFECTIVE_CERAMIC_MIN -->
```yaml
id: U1_EFFECTIVE_CERAMIC_MIN
claim: >-
  Worst-case effective capacitance of the exact six-part U1 ceramic
  control-loop bank after tolerance, DC-bias and temperature derating.
relation: ">="
value: 80.784
unit: uF
corner: worst_case
command: /usr/bin/python3 -c "import yaml;p=yaml.safe_load(open('projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml'));b=p['effective_capacitance_banks'][0];print(round(sum(len(x['refs'])*x['nominal_each_uF']*(1-x['tolerance_minus_pct']/100)*(1-x['dc_bias_derating_pct']/100)*(1-x['temperature_derating_pct']/100)*(1-x['lifecycle_derating_pct']/100) for x in b['contributors']),6))"
governs:
  evaluate: /usr/bin/python3 -c "print({value})"
  budget: ">= 75"
  unit: uF
tolerance: 0.0005
tolerance_why: >-
  Half one unit in the last published decimal place; it is more than ten
  thousand times smaller than the 5.784 uF margin to TI's adopted minimum.
grade: CITED
requires:
  - projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml
```
