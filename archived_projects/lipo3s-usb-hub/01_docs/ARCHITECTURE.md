# lipo3s-usb-hub — architecture

A 3S-LiPo → USB power board: **3× USB-A at 2.5 A each + 1× USB-C at 6 A**, from an
XT60 pack input. No data, no MCU, no firmware — pure hardware power conversion with
hardware-only protection. Authored in tscircuit/TSX and built through the
tscircuit-native one-command pipeline (`tsx_to_board.sh`) to a DRC-0/0/0,
node-for-node-parity board. Machine-enforced net facts live in
`../03_src/rules/nets.yaml`; every value is derived in `DETAIL_DESIGN.md`; each real
decision has an ADR in `decisions/`.

## Requirements → topology

| Req | Spec | How it is met |
|---|---|---|
| P1 | 3S LiPo via XT60 (9.0–12.6 V, ~12.9 V abs-max) | J1 XT60PW-M input; whole input chain rated ≥30 V |
| P2 | 3× USB-A, 2.5 A max each | 5V_A rail → per-port TPS2557 current-limit switch, ILIM = 2.51 A |
| P3 | 1× USB-C, 6 A max | 5V_C rail direct to J5 VBUS pads, copper sized for 6 A |
| P4 | internal research, all decisions autonomous | D1–D11 in BRIEF.md; ADRs in decisions/ |
| P5 | placed + routed board + JLC fab files | sealed release 07_releases/v1.0-2026-07-20/ |

## Power tree

```
J1 XT60PW-M (3S LiPo, 9.0–12.6 V, pack ≤ tens of A)
  └─ F1 15 A ATO blade fuse ─ VBATT_F
       └─ U1 LM74800-Q1 + Q1/Q2 CSD18543Q3A back-to-back  (reverse-polarity
          block + hardware UVLO 9.33 V-on / OV 15.25 V-off)  ─ VSW
            ├─ Buck A: U2 LM5145 + QA1/QA2 + LA1 3.3 µH ─ SW_A ─ 5V_C
            │     5.08 V / 6 A ─────────────────────────► J5 USB-C (direct copper)
            └─ Buck B: U3 LM5145 + QB1/QB2 + LB1 3.3 µH ─ SW_B ─ 5V_A
                  5.08 V / 7.5 A aggregate
                    ├─ U4 TPS2557 (ILIM 2.5 A) ─ VBUS1 ► J2 USB-A
                    ├─ U5 TPS2557 (ILIM 2.5 A) ─ VBUS2 ► J3 USB-A
                    └─ U6 TPS2557 (ILIM 2.5 A) ─ VBUS3 ► J4 USB-A
```

### Sizing — the REAL aggregate, not the connector rating

The XT60 is a 60 A-class connector and the 3S pack can source tens of amps, but the
BOARD's own maximum aggregate draw is bounded by its outputs:

- USB-C: 6 A × 5.08 V = 30.5 W
- 3× USB-A: 3 × 2.5 A × 5.08 V = 38.1 W
- **Board max out = 68.6 W.** At the worst-case low input (9 V) and η ≈ 0.93,
  input current I_in = 68.6 / (9 × 0.93) ≈ **8.2 A**.

So the copper/fuse/front-end are sized for **~8.2 A aggregate at the input**, not for
the XT60's 60 A rating. F1 = 15 A ATO (headroom over 8.2 A, below pack-fault levels).
The two buck rails split the load: Buck A carries 6 A (USB-C), Buck B carries 7.5 A
(the USB-A bank, with ILIM headroom). See ADR-0001 for why two bucks, not one.

## Net domains (index only — source is `03_src/rules/nets.yaml`)

| Class | Nets | Why special |
|---|---|---|
| `SWITCH_NODE` | SW_A, SW_B | 6–7.5 A + highest dV/dt; poured, minimal area |
| `PWR_RAIL` | VBATT_RAW, VBATT_F, FE_MID, VSW, 5V_A, 5V_C | trunk on planes/pours; also carry mA sense taps |
| `VBUS` | VBUS1–3 | 2.5 A port power, switch-limited |
| Default | CC pulls, FB, EN ladder, ILIM, gates, PGOOD | signals |

Any net > 1 A not in a class is a bug (enforced by the DRU floors).

## Stackup (4-layer, JLC 4L "advanced" small-via)

| Layer | Purpose |
|---|---|
| F.Cu | components, power pours (SW nodes, rail necks), signal |
| In1.Cu | solid unbroken GND — the return for everything |
| In2.Cu | power planes: VSW, VBATT_F, 5V_A, 5V_C |
| B.Cu | GND pour + escape routing + rail bond patches |

Vias: 0.6/0.3 standard, 0.25/0.15 in the VQFN fanout → the JLC **ADVANCED (small-via)
option is REQUIRED**. Verify at order (ORDER_README checklist).

## Ground strategy

Solid, unbroken In1 GND plane — no splits. F.Cu and B.Cu GND pours stitched to it.
Each LM5145's PGND/AGND join at the controller per datasheet; no separate analog
island at this scale.

## Critical geometries

- **Hot loops**: input caps (3× 10 µF/50 V X7R) tight to each half-bridge; the
  FET-pair + inductor loop kept minimal. SW pours sized for current, no larger.
- **Tap corridors**: each LM5145's SW-sense/BST/ILIM taps are thin by design —
  named rule areas `SW_TAP_A`/`SW_TAP_B`/`FE_TAP` carry the scoped 0.15 mm floor.
- **Keep-outs**: mounting holes clear of ALL connector bodies (M3 screw-head radius
  3.2 mm) — enforced by the placement audit, not by eye.
- **USB-C 6 A path**: 5V_C from buck-A output bank to J5 VBUS pads (A4/A9/B4/B9) is a
  pour; all four VBUS and four GND pads carry current.

## Interfaces

| Conn | Part | Role | Polarity/pinning fact |
|---|---|---|---|
| J1 | XT60PW-M | 3S in | **pad 1 = "−" blade, pad 2 = "+"** — see `02_parts/XT60PW-M/part.yaml` |
| J2–J4 | USB-A CNCTech 1001-011-01101 | 5 V / 2.5 A out | D+ shorted to D− (BC1.2 DCP) — ADR-0005 |
| J5 | USB4105-GF-A (16P) | 5 V / 6 A out | dual 10 k Rp → advertise 3 A; copper sized 6 A — ADR-0003; D pairs DCP-shorted |

## Firmware boundary

None. No MCU; all protection is hardware (fuse, reverse-polarity block, UVLO/OV,
per-port current limits, buck valley-current OCP, rail TVS). There is no
unprogrammed-state hazard — the board is safe from first power-up.

## Build provenance (the flagship claim)

This board was authored `03_tscircuit/src/lipo3s_usb_hub.tsx` and built to fab-ready
copper by the **one-command tscircuit-native pipeline** —
`bash ~/.claude/skills/kicad-pcb/scripts/tsx_to_board.sh lipo3s-usb-hub` — NOT by
schwriter2 or hand-KiCad. The gate chain (tsci build → converter kicad_sch → ERC 0 →
generate_board placement → audit PASS → generate_rules → promoted KRT route → stitch
→ DRC `--severity-all --refill-zones --schematic-parity`) reports **0/0/0** and
board-netlist parity **0** (303 nodes / 56 nets) vs the sealed usb-power-3s prior art.
See ADR-0006 for the honest A/B relationship to that prior board.
