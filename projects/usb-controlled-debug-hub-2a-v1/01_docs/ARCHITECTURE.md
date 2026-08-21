# USB-controlled debug hub 2A v1 — architecture

status: candidate; commission facts are locked, exact protection parts and
corners are not yet frozen.

## Power tree

```text
J_POWER USB-C (power/PD only; require 20 V fixed PDO, 3 A)
  -> input fuse
  -> 20 V transient + UV/OV/inrush protection
  -> VBUS_PD_SW
       |-> Buck A: TPS56637, 20 V -> ~5.1 V, 6 A rated
       |    -> aggregate eFuse A
       |         |-> port eFuse 1 -> J_PORT1 VBUS, 2 A continuous
       |         |-> port eFuse 2 -> J_PORT2 VBUS, 2 A continuous
       |         `-> internal management VBUS, <=0.1 A
       |-> Buck B: TPS56637, 20 V -> ~5.1 V, 6 A rated
       |    -> aggregate eFuse B
       |         |-> port eFuse 3 -> J_PORT3 VBUS, 2 A continuous
       |         `-> port eFuse 4 -> J_PORT4 VBUS, 2 A continuous
       `-> AP63203Q, 20 V -> 3.3 V, <=0.6 A

J_DATA USB-C (USB 2.0 data upstream)
  -> VBUS high-impedance detector only
  -> USB2517I upstream D+/D-
```

The two 5 V banks isolate converter and fault load. Each 6 A converter carries
4.0 A of external service load; bank A additionally carries no more than
0.1 A of management VBUS. The 3.3 V converter is moved to negotiated 20 V so
its prior ~0.48 A equivalent load does not consume a 5 V bank's current margin.

## Power budget

At the locked continuous service point:

- external USB output: `4 × 5 V × 2 A = 40 W`;
- two 5 V banks, including 0.1 A management and assuming 90% minimum
  conversion efficiency: approximately `45 W` input;
- 3.3 V / 0.6 A management rail at an 85% bound: approximately `2.33 W` input;
- PD/control loss allowance remains to be charged during exact component math.

A 15 V/3 A contract supplies only 45 W and therefore has no credible
continuous margin. A 20 V/3 A contract supplies 60 W and is the minimum
accepted source class. Exact low-PDO lockout and source-tolerance corners remain
an architecture gate.

## Functional data/control architecture

The v2 functional core remains the intended baseline, but no generated v2
source is copied into this project. USB2517I provides four downstream USB 2.0
data channels. FSUSB42 devices independently connect or isolate each downstream
D+/D- pair. MCP2221A plus MCP23017 and hardware interlocks command power/data
states. Hardware safe state remains all external power and data off until valid
control enables them. No firmware artifact belongs to this project.

## Current and protection boundaries

- External port switches remain true reverse-current-blocking TPS259470A
  devices. Their ILIM resistor will be selected from the datasheet equation and
  full process/resistor corners so the guaranteed low threshold exceeds 2.0 A
  and the guaranteed high threshold remains below the USB1130 3 A rating.
- One TPS259827O latch-off breaker protects each 5 V bank. Each threshold
  must clear normal two-port load with margin yet coordinate below the
  TPS56637 minimum current limit. This is not inherited from v2.
- Input protection must operate continuously at the full 20 V PD tolerance,
  survive the selected clamp waveform below every exposed absolute maximum,
  and keep initial Type-C attach capacitance within the applicable sink limit.
- Every output claim is measured at a mated USB-A plug. Connector contact
  resistance is therefore in the voltage-drop budget.

## High-speed boundary

The data path is USB 2.0 High Speed and therefore uses the high-speed-digital
adapter. The v2 topology and exact USB hub/data-switch parts are reuse
candidates, but the new power floorplan can change reference-plane corridors.
Differential routing, plane continuity, ESD adjacency and branch/stub limits
must be re-proved on this board; v2 route evidence is not inherited.

## Stackup and ground

Candidate stackup is JLC four-layer advanced:

| Layer | Purpose |
|---|---|
| F.Cu | components, USB pairs and local high-current/hot-loop copper |
| In1.Cu | continuous GND reference plane; no signal cuts under USB pairs |
| In2.Cu | separated 20 V and 5 V bank power regions, with no return-path slots under USB |
| B.Cu | secondary power spreading and low-speed escape over continuous reference |

Converter hot loops and switch nodes are kept compact and spatially separated
from USB pairs, crystal and feedback/ILIM networks. The two power cells must be
placed as independent manufacturer-reference-layout islands.

## Interfaces

- `J_POWER`: USB-C PD sink, power only; no D+/D-/SBU route.
- `J_DATA`: USB-C USB 2.0 upstream data; its VBUS is detector-only.
- `J_PORT1..4`: GCT USB1130-15-A right-angle receptacles, 3 A/contact
  manufacturer rating; 2 A continuous board claim.

All connector footprints and bodies require exact-model registration and
hash-bound directional human approval before routing spend.

## Firmware boundary

Firmware is forbidden. Hardware may expose the same management interface as
v2, but this project does not create, modify, build or release firmware,
descriptors or host software.
