# cook-hub v1.0 — order + bring-up README (sealed 2026-07-19, git d0ed295)

## 1. What to order
- **PCB**: upload `cook_hub_gerbers.zip` — 4 layer, 185x120mm, standard
  tier (0.6/0.3 vias; NO small-via option needed). Qty 5.
- **Assembly**: `bom.csv` + `cpl.csv` (82 coded SMD lines). Re-run
  `jlc_stock_check.py bom.csv --min-stock 25` ON ORDER DAY; shallow lines:
  C9683 ULN2803 (2495), C125121 LTV-817S (8684), C2653162 MAX31856 (3838).
- **Hand-solder kit** (NOT in the JLC assembly, see MANIFEST
  not_assembled): 20x DIP05-1A72-12L from Digi-Key (DO-NOT-SUBSTITUTE,
  spec 15.4; approved alternate DIP05-1A72-12D), Pico socket headers,
  barrel jack, keypad IDC, terminals, jumper headers.
- **Pico 2 NOT INCLUDED**: buy a Raspberry Pi Pico 2 (RP2350) separately;
  it plugs into the J2 socket. USB routes through the module.

## 2. JLC preview checklist (before paying)
- SMD rotations vs preview (esp. U5/U6 SOIC-18W, U7 SSOP-8 — rotation DB
  suggestions logged in verification/twin_report.csv; verify, don't
  blind-apply). Diode reel orientations for D1/D2/D5-D8 by eye.
- J11 IDC numbering: JLC's CAD numbers the 2x16 grid row-major; OUR board
  uses IDC ribbon zigzag (CH n = pins 2n-1/2n). THT holes constrain the
  part — nothing to fix, just don't "correct" the rotation from the
  preview (adjudicated, twin_report).
- Layer count = 4 in the order form.

## 3. First power ritual (§1.9-adjacent; 30 seconds of beeping)
Before ANY supply: multimeter J1 center pin -> F1 pad (continuity), J1
center vs sleeve (no short), sleeve -> GND plane. Then power from a
current-limited 5V/0.5A bench supply FIRST (not the 2A brick).

## 4. §16-condensed bring-up checklist
1. **16.1 power/boot**: all relays OFF at power-up (verify: no relay
   click, TP33 RELAY_5V = 0V); no glitch on USB plug/reset; coil rail
   stays off until the watchdog is healthy (WD_OK TP low until firmware
   kicks 5-20 Hz on GP5).
2. **16.2 heartbeat/fault**: halt the Pico heartbeat -> WD_OK drops in
   <=0.47s -> relays release (watch TP RELAY_5V); open E-stop loop (J8)
   -> ESTOP_OK low -> COIL_EN low; door open (J7) aborts sequences
   (firmware); Pi USB disconnect -> firmware releases RLY_EN.
3. **16.3 sensors**: disconnect each sensor; short each I2C bus; open
   thermocouple (MAX31856 FAULT_N); remove loadcell cable; inject bad
   CRC frames — all must flag stale/fault, never auto-start.
4. **16.4 relay/keypad**: per-coil actuation via TP41-56; no
   cross-channel closure (contact continuity matrix on J11); all release
   on reset; keypad interposer end-to-end only AFTER the donor teardown
   gate (below).
5. **16.5 EMI**: per spec §16.5 with the appliance running.

## 5. §1.9 TEARDOWN GATE (do not wire to the appliance)
Spec §1.9: the keypad interposer connector/mapping is NOT final until a
donor SMC0985KS teardown confirms FPC pitch, key matrix, and scan
voltage. J11 + the ribbon patch harness are the *hub side* only. Do not
connect to a real appliance keypad until §17 items 1-4 close.

## 6. Review notes dispositioned (render review PASS-WITH-NOTES)
- Inner layers: In1 is a GND plane / In2 power pours, both generated as
  INSET L-shapes that exclude the isolated keypad NE region (geom.NOGO;
  audit I-ISO re-measures every build) — reviewer could not see inners in
  the PDF set; pcb_layers.pdf covers outer layers, inners are
  script-guaranteed + DRC-gated.
- Assembly-drawing text smear in dense SELV areas: board silk itself is
  de-collided; the F.Fab value overlay clutters only the PDF. Open item.
- "CONT GP15" + Pico pinout silk sit under installed parts by design
  (unpopulated-state documentation).
- Bottom side carries no isolation warning silk (top-only). Open item.

## 7. §17 open items (from the commission, hub-relevant)
1-4. Keypad FPC pitch / matrix vs MCU / key mapping / scan waveform —
  BLOCKED on donor teardown (§1.9). 5. Final relay channel count (16
  built). 6. Board/enclosure mounting location (ADR-0006 grew the board
  to 185x120; 6x M3 nylon standoffs). 7-8. Sensor module distances +
  thermal-port geometry. 9. Contactor coil voltage (J10 is a dry
  30V/50mA opto pair). 10. Load-cell platform (cook-loadcell v1.0 covers
  the electronics). 11. Third camera. 12. NTC vs PT1000 (J15 DNP
  MAX31865 provision on the board). 13. I2C extender after EMI. 14.
  Split boards (this hub combines PCB A+B). 15. Module vs integrated
  RP2350 next rev.
Board-local additions: RATE-class silk on the bottom side; F.Fab value
overlay cleanup; U8 datasheet PDF to cache (pinout verified by
convention); assembly PDF legibility in the SELV strip.
