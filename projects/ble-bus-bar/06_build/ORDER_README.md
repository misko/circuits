# ORDER_README — ble-bus-bar v1.0

## JLC order options (PCB step)

- **2 layers, 165 × 64 mm**, qty 5.
- **Outer copper weight: 2 oz** — REQUIRED (ampacity design assumes it;
  ADR-0002. A 1 oz board will overheat at rated load).
- **Min via hole 0.2 mm ("0.2mm/(0.25/0.3mm)" option)** — REQUIRED: the
  USB-C D+/D− weave uses 0.3/0.2 mm vias. Without this option JLC
  rejects the drill file.
- Solder mask any color; HASL or ENIG (ENIG preferred for the 0.5 mm-
  pitch INA238/USB-C, optional).
- Remove-order-number: yes (or accept a printed number on the silk).

## Assembly step

- Upload `bom.csv` + `cpl.csv` (top side only).
- **NOT assembled** (by design):
  - F1–F6 Keystone **3557-2** fuse holders (LCSC C352820) — THT,
    hand-solder; **order 30 pcs + spares separately**. 30 A joints: use
    a large iron tip, fill all 4 pins per holder generously.
  - J10 debug header — DNP (pads only).
  - J1–J8 are bare plated holes (no component).
- **Fuses are NOT included**: user supplies ATO/ATC blade fuses, one per
  port, sized for the load, **30 A maximum**. Note the automotive 80 %
  convention: a 30 A blade fuse is a ≈24 A continuous device.
- Preview checks before paying (jlcpcb-fab checklist):
  - U1–U6 (INA238) pin-1 dot orientation in the 3D preview.
  - D7–D11 diode cathode bands vs the board silk.
  - LED1/LED2 cathode mark orientation — no per-part datasheet;
    verify on the first reel (pin_review.md action). Both carry a
    rotation-DB suggestion (180) — confirm in the preview.
  - D8 (SOD-123) band orientation — model unmarked in the twin render;
    confirm cathode band faces the 3V3 side (render_review.md action).
  - U7 module presence/orientation — our KiCad STEP did not resolve in
    the twin render (pads+keepout verified); confirm the module body in
    the JLC preview, antenna WEST.
  - U1-U6 (MSOP-10) rotation-DB suggestion (90) — the INA238 pin-1 dot
    check above is the decisive verification.
  - U7 module antenna points WEST (off-board edge side).
  - J9 USB-C sits flush with the west edge.
  - Rotation of U9 (SOT-223) and U10 (SOT-23-6) — auto-corrected in the
    CPL (180°/270°), verify visually.
  - Stock re-check the same day (stock moves; INA238 line is 1.8 k).

## User-supplied hardware (per board)

| Position | Hardware | Torque |
|---|---|---|
| +12–24 V input (J7) | M5 bolt, nut, 2 washers + M5 ring lug on 6 AWG-class wire | 4.0–5.0 N·m |
| Ports 1–6 (J1–J6) | M4 bolt, nut, 2 washers + M4 ring lug on 10 AWG-class wire | 2.0–2.5 N·m |
| GND REF (J8) | M4 hardware + lug on any sense wire ≥22 AWG — **NOT a load return** | 2.0 N·m |
| Mounting (H1–H7) | M4 screws + STEEL or BRASS standoffs, DIN 125 flat washer (OD 9 — NOT fender/oversize: north lands sit 0.5 mm from the edge) + split washer both sides (holes are PLATED, Ø9 lands) — NYLON REJECTED, ADR-0007 | 1.2–1.5 N·m |

Brass or steel hardware; washer under both lug and nut. Re-torque after
the first thermal cycle.

Mounting (v1.1, ADR-0007): 7× M4 standoffs, height ≥10 mm (clears the
stud bolt tails + nuts under the board). Recommended enclosure class:
vented polycarbonate or painted-steel wall box, ≥180×90 mm internal,
with the six port studs facing the cable-gland wall. Standoff metal is
CHASSIS potential — the board's mount lands are floating copper and the
only ground bond is the J8 GND-REF stud (do not add others; D1).
DIN-rail OPTION: H4 (117,114.1) and H6 (193,114.1) are 76 mm apart on a
common line — a 2-point DIN adapter bolts to them.

## First-power ritual (DO NOT SKIP — ADR-0001)

1. **No fuses installed, nothing bolted yet.** Multimeter continuity:
   J7 stud ↔ each fuse holder's SOUTH clip pair (must beep);
   J8 stud ↔ USB-C shell (must beep); J7 ↔ J8 (must NOT beep).
2. **Polarity check at the source**: meter the supply leads — the
   POSITIVE lead goes to J7 (marked `+12-24V IN` with two big `+`),
   negative stays at the battery/chassis. A reversed hookup destroys
   the six monitors (documented residual risk).
3. Bolt J7 + J8 (reference only). Power up with NO fuses: PWR LED on,
   ≈3.3 V between J8 and the module's 3V3 pin (pin 1). USB-C
   enumerates as ESP32-C3 USB-Serial-JTAG.
4. **Sense calibration at a known load**: install one fuse, wire a known
   load (e.g. 5 A electronic load) on that port, read the INA238
   (address 0x40 + port−1). Expect I = load ±1 % ±2.5 mA and VBUS ≈
   supply. Repeat per port. Record offsets in firmware config.
5. Thermal check at max continuous load: after 30 min, trunk copper
   ≤70 °C (IR gun), shunt bodies ≤75 °C.
