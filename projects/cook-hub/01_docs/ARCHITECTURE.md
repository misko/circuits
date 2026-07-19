# ARCHITECTURE — cook-hub

One 4-layer board, 185 × 112 mm, that is the entire SELV electronics of the
SMC0985KS Phase-1 rig except the load-cell front-end (cook-loadcell) and the
Pi 5 itself. A pluggable Raspberry Pi Pico 2 is the deterministic controller;
the Pi 5 talks to it only over the Pico's own USB (§2.2).

## Block diagram (text)

```
                       ISOLATED KEYPAD ZONE (top/NE, milled slots, no planes)
                   J11 2x16 keyed header ── 32 contact traces ── 16x reed
                                                                 contact pairs
 ══════════ isolation boundary: >=6mm creepage + 7 slots + silk ══════════
        16x DIP05-1A72-12L coils (5V, 10mA)
              ▲ RELAY_5V (switched)                    ┌ J3 I2C0: MLX90640+SHT45
 Q1 AO3401 high-side ◄─ Q2 ◄─ AND3 (74LVC1G11):       ├ J4 I2C1: SHT45
   WD_OK ∧ ESTOP_OK ∧ RLY_EN                          ├ J5+MAX31856 (SPI0/CS0)
 2x ULN2803A ◄─ 2x 74HC595 ◄─ GP11/12/13              ├ J15 DNP MAX31865 (CS1)
   /OE ◄─ NAND(74LVC1G00): RLY_EN ∧ WD_OK, 10k pullup ├ J6 HX711 dig (GP6/7)
 SN74LVC1G123 watchdog: GP5 5-20Hz → Q=WD_OK (390ms)  ├ J7 door (GP8, EOL)
                                                      ├ J8 E-stop (GP9 + HW)
 Pico 2 on 2x20 sockets (J2): USB→Pi5                 ├ J9 2+1 NTC dividers
   5VP ─SS34→ VSYS (USB ORs internally)               ├ J10 contactor (opto)
                                                      ├ J12/J13 turntable DNP
 J1 5V/2A ─ polyfuse ─ reverse PFET ─ SMBJ5.0A ─ 5VP  └ J14 spare I2C0/GP4
   5VP → AMS1117-3.3 → 3V3 → ferrite → 3V3A (analog corner)
```

## Safety chain (§1.8, §6.5, §7.4) — three independent hardware locks

All-off is the unpowered default; each lock alone kills the coils:

1. **/OE lock**: 74HC595 output-enable is pulled up (disabled) by R;
   driven low only by NAND(RLY_EN, WD_OK). Boot/reset/unprogrammed pin →
   RLY_EN pulled down → outputs Hi-Z → ULN2803 inputs see their internal
   pulldown path → all Darlingtons off.
2. **Coil-rail lock**: RELAY_5V exists only while AND3(WD_OK, ESTOP_OK,
   RLY_EN) drives Q2 (2N7002) which pulls Q1's (AO3401) gate low. Gate
   pulled to 5VP by default → rail dead. 10 k bleeder on RELAY_5V.
3. **Watchdog**: SN74LVC1G123, retriggered by GP5 edges. No edges for
   ~390 ms → WD_OK low → locks 1 AND 2 drop (§6.5a+b). Firmware cannot
   defeat it (§6.5 "not acceptable: firmware-only").

E-stop (§3.9): NC loop, opening it drops ESTOP_OK (74HC14 Schmitt) → lock 2,
monitored on GP9. Its second, independent contact interrupts the external
contactor enable in the HARNESS (documented on silk + ORDER_README), not
through this board (§7.5).

Contactor output (§7.5): GP15 → LTV-817S opto → open-collector pair on J10,
30 V / 50 mA max marked on silk. No mains anywhere on the board (§1.3, §3.11).

## Isolation zone (§2.3, §6.3, §8.4)

Relay bank = 8 super-columns × 2 rows in the NE corner. Within a super-column
the coil pin column and contact pin column are the package's own 7.62 mm row
spacing (edge-edge air ≥6.1 mm over the sealed body). Between super-columns a
7.62 mm gap carries a 2 mm milled slot (7 slots + 1 guarding the west end of
the contact strip). All contact copper (32 traces, KC*A/KC*B nets) lives in
the comb-shaped region {north strip + 8 vertical corridors}; no plane of any
layer enters it; a dedicated `.kicad_dru` rule holds KEYPAD-class copper
≥6 mm from every other net, and audit I-ISO re-measures the geometry
independently. Boundary is silk-labelled on both sides.

§2.3 combining conditions, demonstrated: (a) isolation spacing — DRC rule +
I-ISO ≥6 mm + 1.5 kV relay dielectric; (b) serviceability — relays and J11
are the only things in the zone, all THT, replaceable; patch harness leaves
via keyed J11 without touching SELV side; (c) routing — contact routing is 32
short generator-drawn traces confined to the comb; SELV routing never crosses.

## Power tree (§7)

Ext 5 V ≥2 A (J1 barrel) → F1 polyfuse 2 A → Q3 reverse-PFET → **5VP**
(SMBJ5.0A + 220 µF + 100 µF bulk for §7.3 relay transients)
- → Q1 high-side → **RELAY_5V** (16 coils; worst-case all-on 160 mA, one-at-
  a-time 10 mA; ULN2803 COM flybacks return here)
- → D1 SS34 → **VSYS** (Pico ≤150 mA; USB co-power ORs inside the module)
- → AMS1117-3.3 → **3V3** (sensors + logic, ≤300 mA budget; Pico's own 3V3
  stays module-internal per §7.2)
- 3V3 → FB1 ferrite → **3V3A** (MAX31856 AVDD/DVDD, thermistor dividers,
  J15). Budget: 150+300+160 = 610 mA vs 2 A supply ⇒ margin 227% (§7.6 ≥50%).

## Layers (§8.1)

L1 components/signals · L2 solid GND (absent in keypad zone) · L3 power pours
(5VP / RELAY_5V / 3V3 / 3V3A; absent in keypad zone) · L4 signals. Analog
corner (MAX31856 + NTC dividers) NW; relay coils NE — max diagonal
separation (§8.3). Ambient derating: all parts rated ≥85 °C; board spec'd for
50–60 °C ambient (§8.2, DETAIL_DESIGN #9).

## Resource contract (§5) — preserved

I2C0 GP0/1 (J3), I2C1 GP2/3 (J4), SPI0 GP16-19 + CS0 GP17 + CS1 GP20 (J15),
ADC GP26/27 + spare GP28, HX711 GP6/7 (J6), relay GP11/12/13/14, door GP8,
E-stop GP9, arc GP10 (TP), turntable GP21/22/GP4 (J12/J13, D7), contactor
GP15 (J10). WD_PULSE = GP5 (D6). USB direct to Pi 5.
