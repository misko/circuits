---
id: 0009
date: 2026-08-12
status: accepted
---
# 0009 — Rebalance Type-C feedback and qualify the complete delivery path

## Context

The independent r8 topology review found two false closures. TPSM63604 gives
10nA typical FB input current but no maximum; ADR-0007's 50nA allowance was only
five times typical and left 1.974mV below the adopted 5.25V steady-state ceiling
after the 15mV variation reserve. The delivery path also allocated 15mOhm to
the Type-C connection even though GCT specifies 40mOhm maximum initially and
50mOhm maximum after test per mated contact. The cable was described by length
and gauge but had no exact orderable identity.

## Decision

Reduce the TPSM63604 divider impedance by ten and rebalance its ratio:
R11=4.12k, R24=24.3ohm and R12=1k, all +/-0.1% and +/-25ppm/C. The total top leg
is 4.1443k. With the full +/-1% feedback-system accuracy, independent initial
tolerance and 100C TCR corners, and an analytical 0..500nA FB-current screen,
the calculated output window is 5.064237-5.227226V. Adding the 15mV steady-state
variation reserve leaves 7.774mV below 5.25V. The 500nA value is 50 times TI's
typical value; it is deliberately a qualification screen, not a recast
manufacturer maximum. Exact-board voltage over line, load and temperature is
still mandatory.

Do not turn one connector's contact limit into a complete interconnect limit.
USB Type-C Release 2.0 section 3.7.8.1 defines LLCR across one plug/receptacle
mated contact and explicitly excludes internal plug/receptacle paddle cards or
substrates. A C-to-C cable into a Pi has two mated pairs plus both plug
assemblies, cable conductors/terminations and the Pi receptacle/entry path.
GCT's 50mOhm post-test contact limit is useful plausibility evidence, but it is
not counted as a guaranteed bound for that complete path.

Retain 55mOhm for TPS25810's hot maximum and 4mOhm for exact-board
copper/vias/joints. Allocate the remaining 39mOhm to one explicitly bounded
interconnect measurement from the J5 PCB-side VBUS/GND lands to Raspberry Pi 4
load-plane sense points. This hot four-wire measurement includes both mated
pairs, the Amphenol 10165794-Z0030YBLF 0.3m/3A cable's plug paddle cards,
terminations and conductors, and the Pi-side receptacle/entry path. Neither GCT,
Amphenol nor Raspberry Pi guarantees this combined resistance, so <=39mOhm is
a first-article acceptance target for the exact combination, not a recast
manufacturer maximum. Sources are the [USB-IF Type-C Release 2.0 specification](https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf),
the [GCT USB4105 Revision B drawing](https://gct.co/files/drawings/usb4105.pdf)
and the [Amphenol USB Type-C connector/cable presentation](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/customerpresentation/usb_type_c_connector_cable_productpresentation.pdf).
The identities and ratings come from the [GCT USB4105 Revision B drawing](https://gct.co/files/drawings/usb4105.pdf)
and [Amphenol USB Type-C connector/cable presentation](https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/customerpresentation/usb_type_c_connector_cable_productpresentation.pdf).

The complete analytical path is 98mOhm. Applying 5% residual margin after all
hot/max/qualified values requires 5.058700V at the regulator plane for 4.75V at
the Pi load at 3A. The 5.064237V worst-low divider corner leaves 5.537mV. The
5% residual is smaller than the USB-A path's 20% because each Type-C term is
already a hot maximum, post-environment maximum, or measured acceptance limit;
it is not used to conceal a typical component value.

### Machine-readable bound — qualified complete interconnect resistance

<!-- bound: TYPEC_COMPLETE_INTERCONNECT_MAX -->
```yaml
id: TYPEC_COMPLETE_INTERCONNECT_MAX
claim: >-
  Largest admitted hot four-wire resistance from J5's PCB-side power lands to
  the Pi load plane after subtracting the switch and exact-board terms from the
  adopted 98 mOhm budget.
relation: "<="
value: 39
unit: mOhm
corner: worst_case
command: /usr/bin/python3 -c "import yaml;p=yaml.safe_load(open('projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml'));r=next(x for x in p['rails'] if x['name']=='VBUSC');c=r['ir_budget_components_mohm'];print(round(r['ir_budget_mohm']-sum(v['value'] for k,v in c.items() if k!='complete_type_c_interconnect'),6))"
governs:
  evaluate: /usr/bin/python3 -c "import yaml;p=yaml.safe_load(open('projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml'));r=next(x for x in p['rails'] if x['name']=='VBUSC');c=r['ir_budget_components_mohm'];print(r['ir_budget_mohm']-sum(v['value'] for k,v in c.items() if k!='complete_type_c_interconnect')-{value})"
  budget: ">= 0"
  unit: mOhm
chosen: 39
tolerance: 0.0005
tolerance_why: >-
  Half one unit beyond the last published decimal place; it is four orders
  below the 5.537 mV residual load-plane voltage margin at the adopted path.
grade: CITED
requires:
  - projects/usb-hub-3s-v4/03_src/rules/power_tree.yaml
```

## Consequences

The resistor footprints and placement do not change, but the TSX, generated
schematic, BOM and exact routed board must be rebuilt and all hash-bound reviews
repeated. The lower divider consumes about 1mA rather than 0.1mA while U2 is on,
which is negligible relative to the 3A rail and does not affect OFF current
because U2 is disabled.

This decision closes the paper-design defects sufficiently for a controlled
first article only after fresh independent reviews. It does not close the open
cable/contact/copper/steady-state/load-step/loop-response measurements and
does not authorize production. ADR-0007 remains authoritative for U9 and rail
variation, but its former Type-C divider population is superseded here.
