# Order checklist — usb-power-3s v1.2 (2026-07-17)

> v1.2 is a SCHEMATIC-PDF-ONLY release (schwriter2 port): all fab files
> below are byte-identical to v1.1-2026-07-16 (sha256-verified in the
> MANIFEST). Order instructions unchanged — including the ADVANCED
> small-via option REQUIREMENT below.

## PCB (upload usb_power_3s_gerbers.zip)
- 4 layers, 100×60 mm, 1 oz outer / 0.5 oz inner (JLC7628 stackup)
- **ADVANCED option REQUIRED**: min via 0.25/0.15 mm (VQFN fanout).
  If the order form flags via size, the advanced/small-via option was
  not selected — do NOT waive it.
- Surface: HASL fine (no fine-pitch below 0.5 mm QFN — LeadFree HASL ok);
  ENIG optional.

## Assembly (upload bom.csv + cpl.csv)
- Top side only. 96 placements, 38 BOM lines, 37 coded.
- One BOM line intentionally uncoded: **USB-A jacks J2/J3/J4** (CNCTech
  1001-011-01101, Digi-Key 3064739) — mark "Do Not Place", hand-solder.
- CE1 (EEH-ZA1V101P hybrid) had thin stock (~25) at design time — if out
  of stock do NOT substitute a 6.3 mm can (land pattern is 8×10).
- Eyeball the JLC 3D preview: F1 fuse holder, J1 XT60 (nose overhangs west
  edge BY DESIGN), J5 USB-C, U1-U6 orientations, LA1/LB1 inductors.
- Rotation DB corrections were applied to VSON/VQFN parts; still verify
  pin-1 dots in the preview against the renders in build/renders/.

## After boards arrive
- Fit 15 A ATO blade fuse (user-supplied).
- Power-only smoke test: current-limited 12 V supply, check 5.08 V on both
  rails BEFORE plugging any USB device.

## v1.1 notes
- v1.0 is SUPERSEDED (mirror-numbered LM5145 land pattern) — order ONLY v1.1.
- Two intentional via-in-pad (0.2 mm drill) GND vias on 0402 pads (R16, CB4)
  and one at U2 pin 12 — accepted; sense/ground nets only.
- JLC twin verification passed (verification/twin_report.csv): eyeball LA1/LB1
  (no EasyEDA CAD) and the FET/fuse/XT60 orientations in the JLC 3D preview.
