# Order checklist — crowsync-recorder v1.1 (2026-07-17)

> v1.1 is a SCHEMATIC-PDF-ONLY release (schwriter2 port): all fab files
> below are byte-identical to v1.0-2026-07-16 (sha256-verified in the
> MANIFEST). Order instructions unchanged.

## PCB (upload crowsync_recorder_gerbers.zip)
- 4 layers, 65 x 42 mm, JLC7628 stackup (1 oz outer / 0.5 oz inner).
- **ADVANCED small-via option REQUIRED**: board contains 0.45/0.2 mm vias
  (thin-wave USB-column escapes). If the order form flags via size, the
  advanced option was not selected — do NOT waive it.
- Surface: HASL (LeadFree) fine — finest pitch is SSOP-28 at 0.65 mm;
  ENIG optional.
- Quantity: **5 PCBs** (P8).

## Assembly (upload bom.csv + cpl.csv)
- **3 boards assembled**, top side only. 51 placements, 27 BOM lines,
  27 coded — **zero hand-solder lines** (JST GH + USB-C are JLC-placed,
  decisions/0005).
- Stock re-check the same day (stock moves): re-run
  `python3 jlc_stock_check.py bom.csv --min-stock 15`. Thin lines at design
  time: **PCM2900CDBR C180425 (286)**, **SM03B-GHS-TB C514175 (40)**.
  If the SM03B is out: XY clone **C54582898** is the approved alternate
  (same footprint; decisions/0005). No approved substitute for the codec —
  wait or reduce assembled qty rather than substituting.
- Qty 0 + no price on U1/connector lines = JLC wants manual confirmation,
  not stock-out: click the row, search the code, confirm.

## Rotation / polarity preview checklist (JLC 3D preview, before paying)
- U1 SSOP-28: pin-1 dot NW corner (body long axis N-S, pin 1 top-left).
- U2 SOIC-8: pin-1 dot NW corner.
- U3 SOT-23-5: single-pin side (OUT) faces EAST.
- D1/D2 SOT-23-6: pin 1 top-left as in verification/twin_top.png;
  compare against the twin renders, not intuition.
- D3/D4 LEDs (KT-0805G, NO EasyEDA CAD — render as empty space, part
  still mounts): cathode marker must face WEST (pad 1 = cathode = GND on
  both). Check the green polarity glyph in the preview.
- J1 USB-C: opening overhangs the WEST board edge BY DESIGN.
- J2 (3-pin) / J3 (2-pin) JST GH: openings face EAST edge.
- Y1 crystal: orientation non-critical (verify it is not offset).
- SMD preview rotation is exactly what the machine does — fix, don't
  rationalize. Re-uploading the BOM resets matching; CPL re-upload only
  redoes placements.

## First-power ritual (when boards arrive, BEFORE first plug-in)
1. Multimeter, no cable: VBUS pad (J1 A4) to GND — no short (> 1 kOhm
   after cap charge kick). 3V3A test point (C15 +) to GND — no short.
2. Continuity: J2 pin 2 <-> GND <-> J3 pin 2 <-> USB shield.
3. Plug into a current-limited USB source or a hub you can sacrifice:
   D4 (PWR) lights immediately; D3 (ACT) lights after enumeration.
4. `lsusb` on the Pi: TI PCM2900C audio device appears (08bb:29c0 class).
5. `arecord -D hw:CARD=CODEC -f S16_LE -r 48000 -c 2` — CH1 picks up a
   finger-rub on the mic header pin 1 (through 2.2 V bias); CH2 shows a
   1 Hz tick with the GNSS PPS harness connected (~1 V pulses).
6. Mic capsule note: harness mic sees 2.2 V bias via 2k2 — ship gain is
   for -24 dB capsules (AOM-5024L-HD class); for -44 dB capsules swap
   R11 3k01 -> 39k (decisions/0003).

## Known intentional oddities (do not "fix" at order review)
- J1 body overhangs the board edge (mating face).
- VOUTL/VOUTR/TEST1/HID0-2 codec pins unconnected (datasheet-sanctioned).
- Two USBLC6-2SC6 with different rail references (5V vs 3V3A) — by design.
