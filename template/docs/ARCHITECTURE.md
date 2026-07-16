# <board> — architecture

The high-level concepts a reader (or agent) must hold before touching
anything. This file says **what is**; `decisions/` says **why**; and machine-
enforced facts live in `../src/rules/nets.yaml`, which generates the
netclasses and DRC floors.

Rule of thumb: if a tool must check it, it belongs in `nets.yaml`. If a human
must understand it, it belongs here. Never restate widths/floors here — they
drift. Link instead.

---

## Power tree

Every rail, source → conversion → load, with worst-case current. Net names
must match `nets.yaml` exactly.

```
J1 XT60 (3S, 9–13V, 13A)
  └─ F1 15A ATO ─ VBATT_RAW
       └─ U4 LM74800 ideal diode + Q2/Q3 back-to-back ─ VBATT_F → VSW
            ├─ Buck A (U1 LM5145) ─ SW_A ─ LA1 3.3µH ─ 5V_A  5.18V / 6A → Pi
            └─ Buck B (U2 LM5145) ─ SW_B ─ LB1 3.3µH ─ 5VB_PRE
                 └─ L4 π-filter ─ 5V_B  5.08V / 6A → 3× USB-A + aux
```

State, per rail: nominal, tolerance, max load, and what browns out first.

## Net domains

One row per class in `nets.yaml`. This table is a reader's index, not the
source — the source is the YAML.

| Class | Nets | Why it is special |
|---|---|---|
| `SWITCH_NODE` | SW_A, SW_B | 6A + highest dV/dt; the EMI aggressor. Poured, minimal area, tight loop. |
| `PWR_RAIL` | VBATT_*, VSW, 5V_* | trunk on planes/pours; also carries mA sense taps |
| `VBUS` | VBUS1-3, AUX_5V | current-limited port power |
| `USB_DATA` | D?_N, D?_P | passed through, ESD in series |

**Any net carrying >1A that is not in a class is a bug** — nothing checks
ampacity for you.

## Stackup

What each layer is FOR, not just what it is.

| Layer | Purpose |
|---|---|
| F.Cu | components + signal + power pours |
| In1.Cu | **solid GND** — the return path for everything above |
| In2.Cu | power planes (VSW, 5V_A, 5V_B, VBATT_S) |
| B.Cu | GND pour + escape routing |

Fab tier and the option it forces (e.g. advanced/small-via if any via is
below 0.45/0.2) — state it here AND in every release's ORDER_README.

## Ground strategy

Planes, splits, stitching, and the return-path intent. If there are no
splits, say so explicitly — "solid, unbroken In1 GND" is a decision a future
router can otherwise destroy silently.

## Critical geometries

The things a router will wreck if it does not know. Each one needs a
`nets.yaml` `verify:` line or a rule area — prose alone does not survive.

- **Hot loops** — the FET/inductor/input-cap loop on each buck. Minimal area.
- **Kelvin sense** — the shunt's sense taps: they must meet AT the shunt, not
  share trunk copper.
- **Tap corridors** — gate-drive returns are deliberately thin (0.15mm) and
  exempted by NAMED rule areas so the strict floor still governs the trunk.
- **Keep-outs** — mounting-hole screw heads; connector bodies (a shell over a
  hole means no screw access — check in 3D, not just DRC).

## Interfaces

Connector-by-connector: what plugs in, pinout reference, and polarity. For
any keyed/polarized connector, the authoritative pad↔polarity fact lives in
`parts/<MPN>/part.yaml` — cite it, do not restate it. (A reversed battery
connector is invisible to every electrical check; the netlist is
self-consistent either way.)

## Firmware boundary

What the board does with the MCU **unprogrammed**. If the power path is
hardware-default-on, say so loudly: the board will appear to work and quietly
lack every protection.
