# cook-loadcell v1.0 — order + bring-up README (sealed 2026-07-19)

## 1. Order
- PCB: `cook_loadcell_gerbers.zip`, 2 layer 55x45mm standard tier, qty 5.
- Assembly: `bom.csv` + `cpl.csv` (all SMD + XH THT lines coded).
  Re-verify stock on order day (`jlc_stock_check.py bom.csv`); watch
  C43656 HX711 (12k) and C8542 SS8550 (599k, basic).
- Hand-solder: JP1 3-pin 2.54 header + shunt (ship shunt on 1-2 = 10SPS).

## 2. Preview checklist
- U1 SOIC-16 rotation (twin suggests JLC offset 90 — verify in preview,
  don't blind-apply); XH shells' mouths face off-board (N row up, S row
  down); D1/D2 SOD-323 are BIDIRECTIONAL PESD — orientation indifferent.

## 3. Bring-up (§3.7 verification)
1. Power from the hub J6 cable (5V/3V3/GND/DAT/CLK, pin-for-pin).
2. Multimeter first: J6.1-J6.3 no short; E+ (TP1) vs GND.
3. Power on: TP1 E+ = 4.25-4.35V (AVDD = 1.25 x 28.2k/8.2k = 4.30V).
4. Half-bridge mode: plug 4 sensors J1-J4 (B/R/W per silk); raw counts
   on DAT/CLK at 10SPS; press each corner -> monotonic count change.
5. Full-bridge mode: unplug J1-J4, plug the cell into J5 — same nodes.
6. Shield: default hybrid bond (R7||C7); short SJ1 only if bench EMI
   testing prefers a hard bond.
7. Rate: move JP1 shunt to 2-3 for 80SPS; confirm rate change.

## 4. Open items
- RATE_SEL floats if JP1's shunt is lost — add a 100k pulldown next spin
  (pin-review advisory).
- Label wording inconsistency ("LOAD SENSOR 1" vs "SENSOR n") — cosmetic.
- J5/J6 twin models were placeholder blocks; their pad fits are 0.00mm
  and mouths were render-checked — re-eyeball in the JLC 3D preview.
