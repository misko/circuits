# architecture: xt60-usb-supply

3S LiPo (9.0-12.6 V) in via XT60; out: three USB-A charge ports (2.5 A
each) and one USB-C port (6 A). Two independent 5 V buck rails
(decisions/0001), no digital logic, no firmware.

## Power tree

```
XT60 (J1)          VBAT_RAW   8.5 A worst case (73 W out / 9 V / 0.92 eff)
  └─ F1 15A fuse → VBAT_F
       └─ Q1 P-FET (reverse polarity, drain=VBAT_F, source=VBAT_P)
            └─ VBAT_P  ── TVS D1, bulk C
                 ├─ Buck A (U1) ── SW_A ── L1 ── 5V_A  8 A → J2,J3,J4 USB-A VBUS
                 └─ Buck C (U2) ── SW_C ── L2 ── 5V_C  6 A → J5 USB-C VBUS
GND: single solid plane (In1), all returns.
```

Net names here are exactly those in `03_src/rules/nets.yaml`.

## Net domains

- **SWITCH_NODE** (SW_A, SW_C): buck half-bridge to inductor; highest
  dV/dt, full inductor current. Minimal-area F.Cu pours. → nets.yaml.
- **PWR_RAIL** (VBAT_RAW, VBAT_F, VBAT_P, 5V_A, 5V_C): trunk current on
  F.Cu pours; also carries FB sense taps (low floor + pours). → nets.yaml.
- **FB/CC/DCP signals** (FB_A, FB_C, CC1, CC2, DCP1..3, LED nets):
  ordinary signal geometry. DCPn is the per-port shorted D+/D- pair
  (BC1.2 DCP, decisions/0002 & BRIEF A3).
- **GND**: plane-served.

## Stackup

4-layer JLC standard (decisions/0005):
- F.Cu — power pours (VBAT trunk, SW pours, 5 V trunks) + component routing
- In1.Cu — solid GND, never routed
- In2.Cu — GND fill + 5 V reinforcement patches if needed
- B.Cu — signal routing + pour patches

## Ground strategy

One GND net, one unbroken In1 plane. Buck input caps sit tight to each
converter's VIN/GND pins so the hot loop closes locally on F.Cu + via
stitch to In1. Port grounds (USB shells + GND pins) stitch straight to the
plane. No splits, no star points.

## Critical geometries

- **Hot loop A/C**: CIN ceramic -> U1/U2 VIN -> SW -> L -> COUT -> GND back
  to CIN. Input ceramics within ~3 mm of converter VIN.
- **SW pours**: minimal area, must cover converter SW pad(s) and inductor
  pad; no signal trace may slice them into islands.
- **FB dividers**: at the converter FB pin (<= 10 mm), sensed at the last
  output cap, routed away from SW.
- **6 A USB-C VBUS**: all four VBUS contacts and all four GND contacts of
  J5 carry current; pour from 5V_C to the pad group.
- **XT60 polarity**: KiCad AMASS footprint pad 1 = "-" blade. Audit gate.
- **Port edge**: J2-J4 USB-A + J5 USB-C overhang the east board edge;
  XT60 overhangs west. Mounting holes: 4x M3 with screw-head keepouts.
