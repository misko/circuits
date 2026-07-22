# COST_ESTIMATE — cook-hub (qty-1 prototype build, §14.2 math)

Spec targets: PCB A hub < $60 **plus** PCB B relay board < $80. This board is
A+B combined (D1a) ⇒ envelope **< $140 BOM**, excluding Pico ($5–7) and
excluded items per §14.3.

| Block | Parts | Est. |
|---|---|---|
| 16× DIP05-1A72-12L (global sourcing, ~$3.9 @16) | relays | $62.4 |
| MAX31856MUD+T | C2653162 | $4.1 |
| J11 X9555WV-2x16 + XH family + KF350 + DC-005 + PCC-SMP-K + sockets | connectors | $6.5 |
| 2×74HC595 + 2×ULN2803 + LVC1G123 + LVC1G11 + LVC1G00 + 74HC14 + opto | logic | $2.6 |
| AMS1117 + FETs (3) + SS34 + TVS/PESD (8) + polyfuse | power/prot | $1.6 |
| Electrolytic + MLCC (~40) + resistors (~45) + ferrite + jumpers | passives | $4.5 |
| **Total BOM (excl. Pico, PCB, sensors)** | | **≈ $81.7** |

vs combined envelope $140 → 42% headroom. (Sensor modules MLX90640/SHT45/TC
probe/load cells are §14.1 items, not board BOM.) PCB fab 4L 185×120 qty 5 ≈
$40–60/order (excluded from BOM target per §14.2 "BOM"). Within budget even
if relay pricing lands at $5.5/pc ($88 relays → $107 total).
