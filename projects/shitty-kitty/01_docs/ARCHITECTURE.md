# ARCHITECTURE — shitty-kitty controller

Self-contained controller for the motorized cat-toilet lid: ESP32-S3 module
(WiFi + native USB), TMC2209 stepper driver for the cup rail, LIS2DH12
lid-angle accelerometer, 4x MPR121 capacitive controllers driving 24
off-board foil electrodes (12 inner + 12 outer ring on the lid), 12V in,
optional 5V host header (RaspberryPi/Arduino class). Firmware later
(05_firmware); hardware guarantees the motor is DISABLED at boot.

## Power tree

```
J1 barrel 12V (center+) ── F1 polyfuse 2A ── Q1 AOD4185 (rev-pol P-FET)
 └─ VIN_12V  [TVS D3 SMBJ16A to GND; bulk C 100uF/25V x2]     (ADR-0001)
     ├─ TMC2209 VS (U2; motor 1A RMS chopped)  ─ motor phases A/B → J5
     └─ U8 AP63205 buck 1.1MHz (L1 10uH, 22uF/25V x2 out, 4.7uF x2 in)
         └─ 5V  (2A: 1.5A budget host header J8, 0.5A on-board) (ADR-0004)
             ├─ J8 HOST header 5V pins
             └─ U9 AMS1117-3.3 (4.7uF in / 22uF out)
                 └─ 3V3
                     ├─ U1 ESP32-S3-WROOM-1 (WiFi peak ~370mA)
                     ├─ U3-U6 MPR121 x4 (~1mA), U7 LIS2DH12
                     ├─ TMC2209 VCC_IO
                     ├─ I2C/IRQ/EN pullups, PWR + status LEDs
                     └─ (USB-C J2 powers NOTHING: VBUS only feeds the
                         ESD array reference — board runs from 12V)
```

USB-C is a data/programming port. VBUS is not diode-ORed into the rails
(single 12V power source; keeps the entry chain one path — bench flashing
still works because USB powers nothing: plug 12V too. Stated on silk.)

## Net domains

Machine-readable in `03_src/rules/nets.yaml`:

- **PWR12** (`VIN_RAW`, `VIN_F`, `VIN_12V`): entry chain + motor supply,
  0.8mm floor + In2 pour under the driver corner.
- **MOTOR** (`MOT_A1,A2,B1,B2`): 1A RMS chopped phases, 0.6mm floor,
  short driver→J5 runs in the SE corner, over In1 GND only.
- **PWR5/PWR3V3** (`5V`, `3V3`): 0.5mm floors, In2 pours.
- **SW** (`SW_BUCK`): the 1.1MHz hot node, kept tiny, 0.5mm floor.
- **ELEC** (`INNER1..12`, `OUTER1..12`): the sensitive class. MPR121s sit
  adjacent to their headers; stubs short (<20mm), matched-ish, spaced,
  over unbroken In1 GND; never crossing the driver/buck corner (audit I7).
- **USB** (`USB_DP/DM`): tight pair, connector→ESD→module.
- Default 0.25mm: I2C, IRQs, STEP/DIR/ENN/DIAG/INDEX, UART, endstop, LEDs.

## Stackup (ADR-0003)

4 layers, JLC standard tier (0.45/0.3 vias): F.Cu parts + routing;
In1.Cu solid GND plane (never broken by routing — audit-checked);
In2.Cu power pours (12V east region, 5V + 3V3); B.Cu routing + GND pour.

## Ground strategy

Single GND. In1 is THE return plane. Stitch grid + via next to every GND
pad. Motor/buck return currents localize under the SE power corner;
electrode stubs and I2C see quiet plane in the north/west. EPADs (ESP32,
TMC2209, MPR121 x4) grounded with thermal via clusters.

## Critical geometries

- **Antenna keepout**: WROOM-1 antenna (top 6mm of module) overhangs the
  SOUTH board edge; no copper any layer in the guard strip (audit I3).
- **Electrode stubs**: header pad → MPR121 ELE pad, F.Cu, no vias where
  avoidable, >=0.3mm spacing from neighbors, no aggressor crossings.
- **Buck hot loop**: C_in → VIN/SW → L1 → C_out tight at U8; SW node
  copper minimal; FB/VOUT sense away from SW.
- **Motor loop**: VS bulk caps at U2 pins; phase pairs run together.
- **MOTOR-DISABLED-AT-BOOT**: ENN 10k pull-up to 3V3 (TMC2209 ENN active
  low). Unprogrammed board = motor free. Audit asserts the pullup net.
- **Endstop** on an interrupt-capable GPIO with RC filter (all S3 GPIOs
  interrupt; chosen pin in the map below).

## Placement plan (board 130 x 75mm, origin (50,50)-(180,125))

```
N edge:  J3 ELECTRODES INNER 1-12+G (1x13)   J4 ELECTRODES OUTER 1-12+G (1x13)
         U3 U4 (inner MPR121s)               U5 U6 (outer MPR121s)
W edge:  J2 USB-C (opening W), ESD, BOOT/RESET, LEDs
center:  U1 ESP32 (antenna overhangs S edge), U7 accel, I2C pullups
E side:  J1 12V barrel (E edge) → F1 Q1 D3 → U8 buck+L1 → U9 LDO
SE:      U2 TMC2209 + bulk + sense Rs → J5 MOTOR (XH, E edge)
         J6 ENDSTOP (screw, E edge)          J8 HOST 1x6 (S edge, E of module)
```

4x M3 mounting holes, 5.5mm corner insets. Every connector labeled in
plain words; electrode pins numbered IN1..IN12/G and OUT1..OUT12/G.

## Connector map

| Ref | What | Where |
|---|---|---|
| J1 | 12V IN barrel 2.0mm center-positive | E edge |
| J2 | USB-C programming/debug (no power in) | W edge |
| J3 | ELECTRODES INNER: IN1..IN12 + GND | N edge west |
| J4 | ELECTRODES OUTER: OUT1..OUT12 + GND | N edge east |
| J5 | MOTOR: A1 A2 B1 B2 (JST XH-4) | E edge |
| J6 | ENDSTOP: SIG GND (screw 2P) | E edge |
| J8 | HOST: 5V 5V GND GND TX RX (1x6, 1.5A max) | S edge |

## MCU pin map (physical pads per 02_parts/ESP32-S3-WROOM-1-N8R2)

| Function | GPIO | Pad |
|---|---|---|
| I2C SDA / SCL | IO1 / IO2 | 39 / 38 |
| USB D- / D+ | IO19 / IO20 | 13 / 14 |
| TMC STEP / DIR / ENN | IO4 / IO5 / IO6 | 4 / 5 / 6 |
| TMC DIAG / INDEX | IO7 / IO15 | 7 / 8 |
| TMC UART TX / RX | IO17 / IO18 | 10 / 11 |
| ENDSTOP (interrupt) | IO16 | 9 |
| MPR121 IRQ 1..4 | IO8 / IO9 / IO10 / IO11 | 12 / 17 / 18 / 19 |
| ACCEL INT1 | IO12 | 20 |
| STATUS LED | IO13 | 21 |
| HOST UART TX / RX | TXD0 / RXD0 | 37 / 36 |
| BOOT / EN | IO0 / EN | 27 / 3 |
