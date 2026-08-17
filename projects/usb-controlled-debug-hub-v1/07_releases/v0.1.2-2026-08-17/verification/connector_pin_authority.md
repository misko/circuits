# Exact connector pin authority — C503996 / KH-AF90DIP-112

Date: 2026-08-17  
Disposition: PASS — the exact catalog identity independently binds the physical
tail row to USB signal names. No PCB edit is required.

## Identity and retained evidence

The JLC/EasyEDA library was fetched by exact LCSC code `C503996`. Its generated
symbol identifies itself as manufacturer part `KH-AF90DIP-112`, LCSC part
`C503996`, with the LCSC exact-part datasheet URL. The release twin retains the
complete fetched symbol, footprint, WRL, and STEP under
`verification/twin/easyeda/C503996/`.

| Evidence | SHA-256 |
|---|---|
| `jlc.kicad_sym` | `f267353bb2612f0908fdb660f4cb2fda7ea8e1b2d367d80004047df7cc4b7992` |
| `jlc.pretty/USB-A-TH_USB-A-F-90.kicad_mod` | `918e73b3f9e26fd6821f5e894f46b5ad8824ec31994a80df2d446e73896510fd` |

## Exact-code signal map

The exact-code symbol states:

| Pad | EasyEDA name | Project net role |
|---:|---|---|
| 1 | `VCC` | VBUS |
| 2 | `D-` | USB D- |
| 3 | `D+` | USB D+ |
| 4 | `GND` | Ground |

The exact-code footprint places pads 1, 2, 3, 4 at X = -3.49, -0.99, +1.01,
+3.51 mm, respectively, with the mating body extending toward local +Y. Its
two shell holes are at X = +/-6.57 mm, Y = +1.36 mm. After a pure +3.49-mm X
translation, the project footprint uses the identical contact row at X = 0,
2.50, 4.50, 7.00 mm and the identical body/mouth direction. The manufacturer
drawing independently confirms the 2.50/2.00/2.50-mm contact pitch and shell
field.

Therefore the project mapping `1=VBUS, 2=D-, 3=D+, 4=GND` is exact-part bound;
it is no longer inferred only from a generic USB-A convention. The earlier P1
in `pin_review.md` is closed by this retained evidence. Human connector-facing
orientation approval and JLC THT preview remain separate release gates.
