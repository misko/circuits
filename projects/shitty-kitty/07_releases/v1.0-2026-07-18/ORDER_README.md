# ORDER_README — shitty-kitty v1.0 (JLCPCB)

Cat-litter toilet-lid motion controller: ESP32-S3, TMC2209 stepper driver,
4x MPR121 cap-touch (24 electrode lines), LIS2DH12 accel, 12V-in power tree
(buck 5V + LDO 3V3). 4-layer, 130.2 x 75.2 mm. Quantity 5 (prototype).

## PCB order page
- Upload `shitty_kitty_gerbers.zip` (13 files: 4 copper + F/B mask + F/B
  silk + F/B paste + Edge_Cuts + PTH/NPTH drills).
- Layers: **4**. Thickness 1.6 mm. Surface finish HASL (or ENIG if you plan
  to hand-solder the fine-pitch parts yourself — not needed for JLC assembly).
- **Min via 0.45/0.30 mm, min trace/space ~0.09 mm = JLC 4-layer STANDARD
  tier. Do NOT select the advanced/small-via option** — not required here.
- Impedance control: not required (no controlled-impedance nets).

## Assembly (SMT)
- Upload `bom.csv` (Comment,Designator,Footprint,MPN,LCSC) and `cpl.csv`
  (Designator,Val,Package,Mid X,Mid Y,Layer,Rotation) on the assembly step.
- **Top side only.** 27 coded lines / 72 placements.
- All rotations are pre-corrected in the CPL via the community rotation DB.
  STILL eyeball the JLC preview for: the two SOT-23-6 (D1 USBLC6, D2/D5 LEDs),
  the SMB diode D3, the DPAK Q1, and the polymer caps C40/C41 (polarity).
- **Do NOT populate (hand-soldered after delivery):** J1 barrel jack, J3/J4
  1x13 electrode headers, J5 JST-XH motor, J6 endstop screw terminal, J8 1x6
  host header. These are marked not_assembled in the MANIFEST (THT, D6/D7).

## Order-day checklist
1. **Re-run stock check the day you order** — extended parts (ESP32 C2913204,
   4x MPR121 C91322, TMC2209 C2150710) move; verify stock >= 5x qty.
2. Confirm 4-layer / standard stackup in the order form.
3. Eyeball rotations/polarity of the parts listed above in JLC's 3D preview.
4. Qty-0 / no-price on a matched IC line = JLC wants manual confirm (click the
   row, confirm the code) — NOT a stock-out.

## Environment note (litter-box deployment)
This board lives near a cat toilet: **high humidity + ammonia + litter dust +
occasional splash.** For any real deployment (beyond bench bring-up):
- Apply **conformal coating** (acrylic or silicone) to the assembled board,
  masking the connectors, the USB-C mouth, the two buttons, and the MPR121
  electrode-header pads. Ammonia + humidity will corrode fine-pitch QFN/LGA
  leads and cause cap-sense drift otherwise.
- Mount the PCB **above** the litter cup, connectors facing down/away from
  splash; strain-relieve the 24 electrode wires.
- The cap-touch baseline auto-calibrates (MPR121) but heavy condensation will
  still shift readings — enclose or coat.

## FIRST-POWER RITUAL (do this BEFORE the first real 12V supply)
The motor is **hardware-disabled at boot** (TMC2209 ENN pulled to 3V3 via R8;
ENN active-low, high = driver outputs off) so the cup cannot lurch on
power-up — but verify the power entry first; polarity bugs are electrically
self-consistent and invisible to every automated check:
1. With NO power applied, multimeter-beep the **barrel jack J1**: center pin
   (TIP) must read continuity to VIN_RAW / the polyfuse F1 input; the sleeve
   pins to GND. **J1 is center-positive** (silk: "2.1mm CENTER +").
2. Confirm F1 (2A polyfuse) and Q1 (P-FET reverse-polarity) are in the +12V
   path: TIP -> F1 -> Q1 drain(tab) -> VIN_12V. A reversed barrel supply is
   blocked by Q1's body-diode orientation, but verify before trusting it.
3. Apply 12V. Confirm 5V (U8 buck) and 3V3 (U9 LDO) rails come up; PWR LED
   (D2) lights. ENN should sit HIGH (~3V3) — motor driver OFF until firmware
   drives it.
4. Only after rails verify: connect the NEMA-17 to J5 and let firmware enable
   the driver. **Never hot-plug the motor with the driver enabled.**

## Host header (J8) — TX/RX are BOARD-SIDE labels
Silk "TX"/"RX" are the ESP32's TX/RX (decision D8). Connecting a Pi/Arduino:
board **TX -> host RX**, board **RX -> host TX** (standard cable crossover).
J8 supplies **5V** (1.5A budget) + GND to the host.
