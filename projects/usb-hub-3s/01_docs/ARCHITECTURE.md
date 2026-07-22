# usb-hub-3s — architecture

3S LiPo (XT60) → protected VIN → two independent converters: a 5 V / 7 A
synchronous buck (LM5116 + external FETs) feeding three current-limited
USB-A ports, and a 100 W 4-switch buck-boost PD3.0 source (IP6559-C) feeding
one USB-C port with compliant 5 A contracts. No MCU, no firmware — all
behavior is silicon + straps. Why: decisions/0001..0005.

---

## Power tree

```
J1 XT60 (3S LiPo, 9.0–12.6 V, ≤15.5 A worst case)
  └─ F1 20 A MINI blade ─ VBAT_F
       └─ Q1 P-FET reverse-polarity switch ─ VIN   (D1 SMBJ15A TVS + bulk)
            ├─ U2 LM5116 buck (Q2 HS / Q3 LS, L2 6.8 µH, Rs 10 mΩ) ─ 5VA  5 V / 7 A cont
            │    ├─ U3 TPS2557 (ILIM ≈3 A) ─ VBUSA1 → J2 USB-A   ─ 2 A cont / 2.5 A burst
            │    ├─ U5 TPS2557 ─ VBUSA2 → J3 USB-A
            │    ├─ U7 TPS2557 ─ VBUSA3 → J4 USB-A
            │    └─ D2 ─ VCONN5V (e-marker Vconn feed, tens of mA)
            └─ U9 IP6559-C buck-boost (Q4 HG2/Q5 LG2/Q6 HG1/Q7 LG1, L1 10 µH)
                 ─ VOUT_PD (3.3–21 V) ─ Q8 path NFET ─ VBUSC → J5 USB-C
                    5 V/9 V/12 V @3 A, 20 V @5 A (e-marked), PPS 3.3–21 V ≤5 A
UVLO: U10 TLV431 + Q13 sense VIN, gate U9 EN (GPIO18); U2 has its own UVLO
divider at the same 8.8 V falling / ≥9.4 V rising thresholds (ADR 0001).
```

Brown-out order: 5VA holds to VIN ≈ 5.5 V (buck dropout) but UVLO cuts both
converters at 8.8 V falling first — the pack is protected before any rail sags.

## Net domains

Reader's index — the source is `../03_src/rules/nets.yaml`.

| Class | Nets | Why it is special |
|---|---|---|
| `SWITCH_NODE` | SW_A (buck), LX1/LX2 (buck-boost) | high dV/dt EMI aggressors; poured, minimal area, tight loops |
| `PWR_IN` | VBAT, VBAT_F, VIN | up to ~15.5 A trunk; pours + In2 plane |
| `PWR_RAIL` | 5VA, VOUT_PD | 7 A / 5 A trunks; pours |
| `VBUS` | VBUSA1-3, VBUSC | port power, 3 A / 5 A |
| `SENSE` | CSP/CSN pairs, FB, ILIM | Kelvin/analog — short, off the trunks |
| `USB_DATA` | port D+/D-, CC1/CC2 | data/CC; ESD-protected at connector |

Any net carrying >1 A that is not in a class is a bug.

## Stackup (4-layer, fab_tier jlc_4layer_advanced — ADR 0005)

| Layer | Purpose |
|---|---|
| F.Cu | components, hot loops, power pours (VIN/5VA/VOUT_PD trunks) |
| In1.Cu | **solid GND** — unbroken return under both converters |
| In2.Cu | VIN plane (+ 5VA island east if needed) |
| B.Cu | GND pour + escape routing (QFN-48 fanout) |

ADVANCED option REQUIRED at order: min via 0.25/0.15 (QFN-48 0.5 mm fanout).
State in every release ORDER_README.

## Ground strategy

Single GND net. In1 solid and unbroken (a future router must not slice it).
AGND pins of U9 (11/28/30) tie at the chip; sense-line pairs route
differentially to the 5 mΩ shunts. Stitch vias bond F/B pours to In1.

## Critical geometries

- **Hot loops**: buck (C_in ↔ Q2/Q3), buck-boost input (C_in ↔ Q4/Q5) and
  output (C_out ↔ Q6/Q7) — minimal area, caps hard against FETs (D-ADJ).
- **Kelvin sense**: R_s5m input/output shunts — CSP/CSN taps leave from the
  pad ends, parallel pair, never sharing trunk copper (IP6559 DS §13.5).
- **LX web**: L1 between Q4/Q6 LX nodes — wide, short; RC snubbers at each LX.
- **Escape corridor**: U9 QFN-48 — advanced-tier fanout vias; B.Cu escape.
- **Keep-outs**: mounting-hole screw heads; connector overhangs at board edge.

## Interfaces

| Conn | What plugs in | Polarity/pinout authority |
|---|---|---|
| J1 XT60PW-M | 3S pack XT60 male | `02_parts/XT60PW-M/part.yaml` — **pad 1 = '−'** (asserted in floorplan) |
| J2–J4 USB-A | legacy 5 V sinks | `02_parts/<usb-a>/part.yaml` |
| J5 USB-C | PD sinks (5 A needs e-marked cable) | `02_parts/TYPE-C-31-M-12A/part.yaml` |

## Firmware boundary

None — no MCU. Power path is hardware-default-on above UVLO: plugging a
charged pack makes all four ports live. Protections (UVLO, ILIM, PD rules)
are silicon straps, active unprogrammed, by construction.
