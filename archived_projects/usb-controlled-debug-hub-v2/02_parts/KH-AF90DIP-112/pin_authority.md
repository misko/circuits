# C503996 exact-catalog pin authority

Captured 2026-08-17 from the JLC/EasyEDA library by exact LCSC code `C503996`.
The returned symbol identifies MPN `KH-AF90DIP-112` and maps pad 1=`VCC`,
2=`D-`, 3=`D+`, 4=`GND`. The paired footprint places pads 1..4 at X = -3.49,
-0.99, +1.01, +3.51 mm, with the receptacle extending toward local +Y and the
two shell holes at X = +/-6.57 mm, Y = +1.36 mm.

The project footprint is the same numbered contact row translated +3.49 mm:
X = 0, 2.50, 4.50, 7.00 mm. Its shell field and mating-mouth direction also
match. The Kinghelm drawing independently confirms the 2.50/2.00/2.50-mm row
and shell geometry. This closes the physical mapping as 1=VBUS, 2=D-, 3=D+,
4=GND for the exact assembly part.

Retained release evidence:

- exact symbol SHA-256: `f267353bb2612f0908fdb660f4cb2fda7ea8e1b2d367d80004047df7cc4b7992`
- exact footprint SHA-256: `918e73b3f9e26fd6821f5e894f46b5ad8824ec31994a80df2d446e73896510fd`
- full fetched library: release `verification/twin/easyeda/C503996/`
