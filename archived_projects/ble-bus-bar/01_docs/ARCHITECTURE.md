# ARCHITECTURE — ble-bus-bar

12–24 V DC distribution bus bar: one bolted input feed (60 A aggregate),
six individually ATO-fused, individually shunt-monitored bolted output
ports (each up to 30 A peak), telemetry via BLE (ESP32-C3), statistics
logged to onboard SPI NOR flash. Monitor-only: no port switching —
protection per port is the user-replaceable blade fuse (Q2/A2, Q3/A3).

The board distributes the POSITIVE rail only (automotive practice): load
returns go back to the battery/chassis, not through this board. The board
GND is a low-current reference/electronics ground brought in on its own
M4 stud. Consequence: only +paths need 30–60 A copper; GND stays a quiet
electronics plane. (D1 in BRIEF.md)

## Power tree

```
+12-24V feed (M5 stud J7, 60A) ──► VBUS trunk pour (F+B.Cu, 2oz)
    ├─► F1 (ATO ≤30A) ─ VF1 ─ RS1 0.5mΩ ─ VP1 ─► port stud J1 (M4, ≤30A)
    ├─► F2..F6 / VF2..6 / RS2..6 / VP2..6 ─► J2..J6          (identical ×6)
    └─► F7 (2A SMD fuse) ─ VTAP ─ D7 SS310 ─ VIN_E           electronics tap
             VIN_E ─► U8 LMR16006XDDCR buck (60V, 0.7MHz) ─ SW ─ L1 22µH ─► 3V3 (≈0.4A pk)
USB-C 5V (VUSB) ─► U9 AMS1117-3.3 ─ VLDO ─ D8 B5819W ─► 3V3   (bench/flash power, ≈3.0V)
GND reference (M4 stud J8) ─► GND plane (electronics only — NOT a load return)
```

3V3 loads: ESP32-C3-WROOM-02 (≤350 mA radio peak), W25Q64JV flash
(≤25 mA), 6× INA238 (≈4 mA total), LEDs/pull-ups (≈10 mA). Budget ≈0.4 A
peak vs 0.6 A buck rating.

## Net domains

Machine-readable facts live in `03_src/rules/nets.yaml`; summary:

- **TRUNK** — `VBUS`: 60 A continuous. Carried by paired priority-1
  pours (F.Cu + B.Cu) in the south trunk band; never by tracks.
- **PORT** — `VF1..VF6` (fuse→shunt), `VP1..VP6` (shunt→port stud):
  30 A peak each. Single-layer F.Cu pours ≥10.5 mm wide; the only
  sub-floor copper is the Kelvin sense taps inside the named KELVIN
  rule areas (see Critical geometries).
- **EPWR** — `VTAP, VIN_E, SW, 3V3, VLDO, VUSB`: ≤0.6 A electronics
  power, 0.5 mm floor.
- **Default** — I2C (`SDA, SCL`), `ALERT`, per-port sense taps after the
  filter Rs (`KP1..6, KN1..6, VB1..6`), USB data, SPI flash, straps,
  buttons: 0.3 mm (JLC 2 oz floor is 0.254 mm).
- **GND** — electronics reference only (no load current): B.Cu plane
  (west + under slices) + F.Cu pour in the electronics zone; stitch vias.

## Stackup

2-layer, **2 oz outer copper** (JLC 2-layer 2 oz service). See
ADR-0002: two layers of 2 oz with THT-stitched paired pours meet the
60 A/30 A ampacity with ≥1.4× margin; a 4-layer board would add cost
without adding usable inner copper (JLC 4L inner layers are thin unless
exotic). F.Cu = all power paths + components; B.Cu = GND plane, trunk
reinforcement pour, and the E–W signal corridor that crosses under the
port slices.

## Ground strategy

- One GND domain (electronics). B.Cu plane covers the electronics zone
  and continues (priority 0) under the port slices; the trunk
  reinforcement pour (priority 1) displaces it only in the south band.
- F.Cu GND pour in the electronics zone only (keeps SMD GND pads
  connected without via-per-pad); power pours own the east F.Cu.
- Stitch vias tie F/B GND; every GND SMD pad outside the F.Cu GND pour
  gets a rescue via (stitch_and_fill pass).
- Loads do NOT return through this board (D1); the GND stud is labeled
  as reference only.

## Critical geometries

- **Kelvin sense taps** (machine-checked, audit I-KELVIN): each shunt's
  sense traces leave the pads at the pad INNER edges (the element side),
  through the pad gap, on F.Cu — never from the pour side where port
  current enters. The taps are on 30 A-class nets (VF*/VP*) at signal
  width, legal only inside the named `KELVIN` rule areas
  (`.kicad_dru` scoped exception, canon R1).
- **Pour discipline**: port current enters the shunt pad from the pour
  side (VF from the south/fuse side, VP from the north/stud side); the
  pad gap itself carries no pour copper.
- **Trunk band**: F.Cu + B.Cu paired pours, y≈93.5–110, joined by the
  input stud barrel and every fuse holder's THT pins (each fuse is fed
  from both layers). Solid pad connections (thermal relief NONE) on all
  power zones.
- **Antenna keepout**: ESP32-C3-WROOM-02 PCB antenna zone overhangs the
  west board edge region with an all-layer copper keepout per the module
  datasheet (§3.1 keepout zone).
- **I2C corridor**: SDA/SCL/3V3/ALERT run E–W on B.Cu under the slices
  (the F.Cu there is port-power), with a via pair up to each INA238.
- **Reverse-polarity story** (ADR-0001): bus TVS forward-clamps a
  reversed feed near −1 V; the 10 Ω sense-tap resistors limit INA input
  current; the electronics branch is series-diode protected. Sustained
  reversal is NOT survived — silk polarity marks + first-power ritual
  are the primary mitigation at 60 A.
