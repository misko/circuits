# usb-power-3s — architecture

A 3S-LiPo → USB power board: 3× USB-A at 2.5 A each and 1× USB-C at 6 A.
No data, no MCU, no firmware — pure hardware power conversion with hardware
protection. Machine-enforced net facts live in `../03_src/rules/nets.yaml`.

## Power tree

```
J1 XT60PW-M (3S LiPo, 9.0–12.6 V, ≤9 A)
  └─ F1 15 A ATO blade fuse ─ VBATT_F
       └─ U1 LM74800-Q1 + Q1/Q2 CSD18543Q3A back-to-back  (reverse-polarity
          protection + hardware UVLO 9.3 V-on / OV 15.2 V-off)  ─ VSW
            ├─ Buck A: U2 LM5145 + QA1/QA2 + LA1 3.3 µH ─ SW_A ─ 5V_C
            │     5.08 V / 6 A ─────────────────────────► J5 USB-C (direct)
            └─ Buck B: U3 LM5145 + QB1/QB2 + LB1 3.3 µH ─ SW_B ─ 5V_A
                  5.08 V / 7.5 A
                    ├─ U4 TPS2557 (ILIM 2.5 A) ─ VBUS1 ► J2 USB-A
                    ├─ U5 TPS2557 (ILIM 2.5 A) ─ VBUS2 ► J3 USB-A
                    └─ U6 TPS2557 (ILIM 2.5 A) ─ VBUS3 ► J4 USB-A
```

Worst case: 67.5 W out → ~8.1 A in at 9 V (η≈0.93). Fuse 15 A.
Rails: 5.078 V setpoint (0.8 V ref, 20k/3.74k); ports see ≥4.9 V at full
load after trace drop.

## Net domains

Index only — the source is `03_src/rules/nets.yaml`.

| Class | Nets | Why special |
|---|---|---|
| `SWITCH_NODE` | SW_A, SW_B | 6–7.5 A + highest dV/dt; poured, minimal area |
| `PWR_RAIL` | VBATT_F, VBATT_S, FE_MID, VSW, 5V_A, 5V_C | trunk on planes/pours; also carries mA sense taps |
| `VBUS` | VBUS1–3 | 2.5 A port power, switch-limited |
| Default | CC pulls, FB, EN ladder, ILIM, gates, PGOOD | signals |

Any net >1 A not in a class is a bug.

## Stackup (4-layer, JLC 4L)

| Layer | Purpose |
|---|---|
| F.Cu | components, power pours (SW nodes, rail necks), signal |
| In1.Cu | solid unbroken GND — the return for everything |
| In2.Cu | power planes: VSW, 5V_A, 5V_C |
| B.Cu | GND pour + escape routing |

Vias: 0.6/0.3 standard, 0.25/0.15 in the VQFN fanout — so the
JLC ADVANCED (small-via) option IS REQUIRED. Verify at order.

## Ground strategy

Solid, unbroken In1 GND plane — no splits. F.Cu and B.Cu GND pours stitched.
Each LM5145's PGND/AGND join at the controller per datasheet; no analog
island at this scale.

## Critical geometries

- **Hot loops**: input caps (3× 10 µF/50 V X7R) tight to each half-bridge;
  FET pair + inductor loop minimal. SW pours sized for current, no larger.
- **Tap corridors**: LM5145 SW-sense/BST/ILIM taps are thin by design —
  named rule areas `SW_TAP_A`/`SW_TAP_B` carry the scoped 0.15 mm floor.
- **Keep-outs**: mounting holes clear of ALL connector bodies (screw-head
  radius 3.2 mm) — enforced by the audit, not by eye.
- **USB-C 6 A path**: 5V_C from buck A output bank to J5 VBUS pads
  (A4/A9/B4/B9) is a pour; all four VBUS and four GND pads carry current.

## Interfaces

| Conn | Part | Role | Polarity/pinning fact |
|---|---|---|---|
| J1 | XT60PW-M | 3S in | **pad 1 = "−" blade, pad 2 = "+"** — `02_parts/XT60PW-M/part.yaml` |
| J2–J4 | USB-A CNCTech 1001-011-01101 | 5 V / 2.5 A out | D+ shorted to D− (BC1.2 DCP) — ADR-0003 |
| J5 | USB4105-GF-A | 5 V / 6 A out | Rp 10 k×2 → advertises 3 A; copper sized for 6 A — ADR-0002; D pairs DCP-shorted |

## Firmware boundary

None. No MCU; all protection is hardware (fuse, reverse polarity, UVLO/OV,
per-port limits, buck OCP). There is no unprogrammed-state hazard.
