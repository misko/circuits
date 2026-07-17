# ORDER_README — xt60-usb-supply v1.0

## What to order

- **PCB**: upload `xt60-usb-supply_gerbers.zip`. 4-layer, JLC standard
  stackup (JLC04161H-7628), 1.6 mm, 1 oz outer. NO small-via option
  needed (min via 0.55/0.3). Min track/clearance in design: 0.2/0.127 —
  standard capability.
- **Assembly (economic, top side)**: upload `bom.csv` + `cpl.csv`.
  20 coded lines. Quantity: 5 boards.

## Hand-solder list (NOT assembled by JLC — order separately)

| Ref | Part | LCSC (for the parts order) |
|---|---|---|
| J1 | XT60PW-M battery connector | C98732 |
| J2,J3,J4 | XY-AF90-WJDG USB-A THT receptacle | C53133490 |

J5 (USB-C, C5337088) IS on the assembly BOM (SMD pads); its 4 THT shell
legs reflow/hand-touch fine.

## JLC preview checklist (before paying — do not skip)

1. **Rotations flagged by the digital twin** (rotation-DB disagreements;
   verify each in JLC's 3D preview against the board silk/fab):
   CB1/CB2 (polymer caps: + marking must match silk +), Q1 (TO-252 tab
   north), J5 (USB-C), U3-U6 (SOT-23-6 pin 1), LED2/LED3 green + LED1
   red (LED reel orientation is per-part; cathode = silk bar side).
2. Qty-0-no-price lines = "confirm manually", not stock-out (click row).
3. Layer count 4 confirmed in the order form.
4. Re-run the stock check the day of ordering
   (`python3 skills/jlcpcb-fab/scripts/jlc_stock_check.py bom.csv`).

## First-power ritual (when boards arrive)

1. NO battery yet. Multimeter continuity: XT60 **housing-marked "+"
   blade** -> F1 pad 1; XT60 "-" blade -> GND plane. The footprint's
   pad 1 is the "-" blade (verified three ways in
   02_parts/XT60PW-M/part.yaml) — this beep test is the final word.
1b. USB-A jacks: shell (metal case) -> pin 4 region continuity to GND,
   and VBUS (pin 1, the pin nearest each jack's LED-side edge) NOT
   shorted to shell. The XY-AF90-WJDG drawing lacks signal labels (pin
   map rests on three agreeing sources — pin_review.md); this beep test
   closes it physically.
2. Check VBAT_P to GND: no short (should read capacitor charging).
3. First power via a current-limited supply at 12 V, 0.5 A limit: both
   green LEDs + red LED on; 5 V on every port VBUS, no load.
4. Load test: 2.5 A per USB-A, 6 A on USB-C (electronic load), check
   5 V regulation and converter temperatures (SY8368 theta_JA 30 C/W).

## Operating notes

- Input 3S LiPo only (9.0-12.6 V). Fuse: 15 A littelfuse NANO2.
- USB-C advertises 5 V/3 A via Rp (CC1/CC2, 10 k to 5V_C); data pads
  carry a BC1.2 DCP short for legacy A-to-C cables (ADR 0008). The rail
  and connector are sized for 6 A (converter valley limit 8 A).
- OVP/short-circuit on the SY8368 is LATCH-OFF: power-cycle to recover.
- ILMT pins are tied to GND BY DESIGN: the SY8368 pin table defines
  low = 8 A valley current limit (pin_review.md verified; ADR 0007).
