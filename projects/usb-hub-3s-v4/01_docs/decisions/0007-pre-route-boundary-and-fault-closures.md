---
id: 0007
date: 2026-08-11
status: accepted
---
# 0007 — Close source floor, rail variation and aggregate USB-A faults

## Context

The first exact pre-route review found three assumptions that the arithmetic
gates had not owned. The 9.0V lower input bound existed only as a converter
calculation; neither the board nor a named external device stopped a bare 3S
pack below it. Divider/reference corners were presented as complete 5.25V
maxima without reserving nonzero switching ripple and steady line/load
movement. Finally, the three independent TPS2559 worst-high limits could sum
to 8.547A indefinitely, above U1's 8A continuous rating, even though the
declared 7.5A service peak itself was acceptable as a transient.

## Decision

Make a protected 3S pack with an independent disconnect at or above 9.0V an
explicit input-interface requirement. The board still has no active
overvoltage cutoff; a bare unprotected pack is outside its commissioned source
boundary.

Insert U9 TPS259827ONRGET between U1's `5VA_RAW` output and the shared `5VA`
USB-A rail. This exact `7O` device is the no-OVLO, circuit-breaker variant, not
an active overvoltage protector. R26=210ohm programs a machine-derived
6.160253-8.066419A full-temperature threshold. The derivation applies TI
Equation 4's `+0.11A` offset before scaling the adverse characterized row and
then charges resistor tolerance/TCR. It retains 0.160A above 6A continuous
service and 0.481A below the 8.547A three-port worst-high fault. Its upper
corner can exceed U1's 8A continuous rating by 0.066A, so that interval is
explicitly transient: it remains below U1's 10A peak rating, C29 bounds it to
45.962ms, and board acceptance requires a hot <=50ms overload qualification.
C29=47nF +/-5% C0G, C0G's +/-30ppm/C class bound over
the 100C design excursion, TI's 0.7-1.3V comparator delta and 1.4-2.8uA
discharge-current limits give a charged 11.129-45.962ms blanking window, so
the declared <=10ms coincident peak passes at every listed corner. C30=3.3nF
+/-2% C0G on dVdt also closes TI's maximum-ITIMER-capacitance startup
relation: even omitting turn-on delay, its shortest charged contribution is
4.388ms, permitting 82.795nF versus C29's 49.498nF maximum. RETRY_DLY is
grounded for latch-off, LDSTRT is grounded because handshake is unused, and
cycling SW1 resets the fault.

Lower U2's feedback top leg from 41.630k to 41.500k (R24=300ohm). Its exact
static window becomes 5.069841-5.233026V. Both regulated rails reserve 15mV
below the 5.25V steady-state ceiling for switching ripple and steady line/load
movement. Startup and load-step excursions are a separate first-article
qualification with a 5.5V ceiling; no claim turns a typical transient plot
into a production maximum.

## Consequences

U9 adds one advanced-tier split-thermal-pad QFN and three passives, but closes a
real protection-coordination gap without replacing the power module. Its
4.5mohm maximum resistance is charged to the USB-A delivery path. JLC catalog
identity C2155765 had 15 units on 2026-08-11; that observation is volatile and
must be repeated at release. The exact footprint requires electrically
separate IN and GND filled/capped via-in-pad fields and independent twin review.

The input contract now depends on an external protection device and must be
prominent in the schematic, assembly/use instructions and release checklist.
The 15mV rail-variation allocations and <=10ms peak window remain mandatory
exact-board qualifications before order approval.

### Machine-readable bound amendment — startup-compatible ITIMER ceiling

<!-- bound: ITIMER_STARTUP_CAP_MAX -->
```yaml
id: ITIMER_STARTUP_CAP_MAX
claim: >-
  Largest ITIMER capacitance permitted by TPS25982's startup relation at the
  exact C30 worst-low ramp and adopted voltage/current corners.
relation: "<="
value: 82.795
unit: nF
corner: worst_case
command: /usr/bin/python3 -c "import yaml;p=yaml.safe_load(open('projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml'));s=p['fault_envelopes'][0]['aggregate_breaker']['timer']['startup'];c=s['capacitance_nominal_nF']*(1-s['tolerance_pct']/100)*(1-s['temperature_minus_pct']/100)*(1-s['dc_bias_minus_pct']/100)*(1-s['aging_minus_pct']/100);print(round(c*(s['vin_min_V']+s['gate_overdrive_V'])/s['dvdt_current_max_uA']*1000000/s['itimer_divisor'],6))"
governs:
  evaluate: /usr/bin/python3 -c "print(82.79525185792721-{value})"
  budget: ">= 0"
  unit: nF
tolerance: 0.001
tolerance_why: >-
  One unit in the last published decimal place; it is over thirty thousand
  times smaller than the 33.297 nF margin to C29's charged 49.498 nF maximum.
grade: CITED
requires:
  - projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml
```
