# ARCHITECTURE — esp32-laser-timing

Bench controller that timestamps laser-beam interruptions: 3 laser channels
(low-side switched), 3 photodiode channels (LM339 comparators -> ESP32-S3
edge timestamping), 3 off-board buttons, OLED status header. USB-C 5V is
the sole power input and the native-USB programming/console port.

## Power tree

```
USB-C VBUS (J1, 5V, <1A budget)
 └─ 5V ──────────────────────────────── net: 5V
     ├─ laser terminals J4/J5/J6 pin1 (3 x 40mA = 120mA)
     ├─ photodiode cathode bias J7/J8/J9 pin1 (3 x <3mA)
     ├─ LM339 VCC (U3, ~1mA) — 5V rail is USER-PINNED (P6: input
     │   common-mode must cover the 0-3V signal swing; CM tops ~1.5V
     │   below VCC)
     ├─ C_bulk 100uF electrolytic + 100nF near laser terminals (P4)
     └─ U2 AMS1117-3.3 (22uF in / 22uF out)
         └─ 3V3 ─────────────────────── net: 3V3
             ├─ ESP32-S3-WROOM-1 (U1; WiFi peaks ~350mA)
             ├─ comparator output pullups (3 x 10k), threshold dividers
             │   (3 x 10k/2.7k, ~0.78mA total), hysteresis refs
             ├─ button pullups (3 x 10k), EN pullup 10k + 1uF
             ├─ OLED header VCC (budget 30mA) + 4.7k I2C pullups
             └─ power LED (1k + green 0805, ~2mA)
```

Worst case draw: 120mA lasers + ~10mA PD/comparator + ~370mA ESP32(3V3,
via LDO) + 30mA OLED ≈ 0.55A from VBUS — inside the 1A budget (P4) and
inside AMS1117's 1A rating. LDO dissipation worst-case ~0.65W peak
(SOT-223 on pour, see DETAIL_DESIGN).

## Net domains

Machine-readable classes live in `03_src/rules/nets.yaml`; summary:

- **PWR** (`5V`, `3V3`): supply distribution, floored width, routed wide
  on F.Cu with B.Cu reinforcement where needed.
- **COMP** (`COMP1..3`): the timing-critical comparator outputs — similar
  length, routed away from the FET switch nodes (`LSW1..3`), over
  continuous B.Cu ground.
- **LSW** (`LSW1..3`): laser switched-ground drains (40mA, slow edges but
  they are the aggressors relative to COMP).
- Default: everything else (gate drives, button/I2C/USB signals).

## Stackup

2 layers (P10, JLC default 2-layer rules: 0.127mm track/space floor is
comfortable; we use 0.25mm signal / 0.20mm clearance, 0.6/0.3 vias):

- **F.Cu** — components (all SMD one side, P2) + primary routing + local
  GND pour.
- **B.Cu** — THE ground pour (kept continuous under the LM339 signal
  region) + minority escape routing. Routing on B.Cu is kept short so the
  pour stays connected; stitch vias reconnect any severed regions.

## Ground strategy

Single GND net. B.Cu full-board GND pour is the return plane; F.Cu GND
pour secondary; stitch-via grid + a via next to every GND pad. The LM339
input region (PD load resistors, thresholds, feedback) sits over
unbroken B.Cu copper — audit checks no B.Cu track crosses under it.
Laser return current (terminal pin2 -> FET drain -> source -> GND pour)
is localized in the south-west corner, away from the comparator region.

## Critical geometries

- **Antenna keepout**: the WROOM-1 antenna end overhangs the north board
  edge; no copper of any kind under/near the antenna zone per the module
  datasheet keepout figure. `audit_board.py` enforces (placement invariant).
- **Comparator outputs** (`COMP1..3`): similar length, no routing through
  the FET corner; no capacitance added anywhere in the signal path (P6:
  microsecond edges).
- **Photodiode signal nodes** (`PD1..3`): terminal -> 1k load -> LM339
  +IN, kept short, over B.Cu GND.
- **USB differential pair** (`USB_DP/USB_DM`): connector -> ESD -> module
  IO19/IO20, tight pair, < 30mm, full-speed (12Mbps) so geometry is
  forgiving but keep it over unbroken ground.
- **LDO thermal**: SOT-223 tab (VOUT=3V3) on an enlarged 3V3 pour.

## Placement plan (matches 03_src/generate_board.py floorplan)

Board 92 x 62mm, origin (50,50)-(142,112). M3 holes 5.5mm corner insets.

```
NW/N: USB-C (west edge) | ESP32-S3-WROOM-1 (antenna overhangs north edge) | OLED header (NE)
mid:  ESD/CC/LDO | BOOT+RESET tactiles, power LED | button terminals (east edge)
S:    laser FETs + 3 laser terminals (SW, south edge) | bulk cap | LM339 + networks | 3 photodiode terminals (SE, south edge)
```

Every terminal is silkscreened in plain words (P10); the OLED header pin
order GND/VCC/SCL/SDA gets prominent silk incl. a "CHECK MODULE PINOUT"
warning (P8). Test points: COMP1-3, 5V, 3V3, GND (P10).

## Connector map

| Ref | What | Where |
|---|---|---|
| J1 | USB-C 5V + native USB | west edge |
| J2 | OLED 4-pos female header GND/VCC/SCL/SDA | north-east |
| J4/J5/J6 | LASER 1/2/3 (pin1 5V, pin2 switched GND) | south edge, west |
| J7/J8/J9 | PHOTODIODE 1/2/3 (pin1 5V cathode, pin2 anode/signal) | south edge, east |
| J10/J11/J12 | BUTTON 1/2/3 (pin1 signal, pin2 GND) | east edge |

## MCU pin map

Authoritative table in the project README (P11 deliverable) and ADR-0004;
also silkscreened. Summary: COMP1..3 -> IO4/IO5/IO6; LASER1..3 ->
IO7/IO15/IO16; BTN1..3 -> IO17/IO18/IO21; I2C SDA=IO1 SCL=IO2; USB
D-=IO19 D+=IO20; BOOT=IO0 tactile; EN=RESET tactile + 10k/1uF.
