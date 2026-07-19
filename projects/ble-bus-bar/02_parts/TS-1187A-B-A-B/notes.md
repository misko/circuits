# TS-1187A-B-A-B — footprint vendoring data (EasyEDA C318884)

Footprint to generate as `esp32_laser_timing:SW_TS-1187A`.

## Pad positions (EasyEDA CAD JSON, `https://easyeda.com/api/products/C318884/components?version=6.4.19.5`)

EasyEDA raw units are 10 mil (x0.254 = mm). Center normalized to (0,0), y+ = down in
EasyEDA; converted here to KiCad convention (y+ = down as well in .kicad_mod files):

| Pad | EasyEDA x,y (units) | KiCad at (mm) | Size (mm) | Shape |
|-----|--------------------|---------------|-----------|-------|
| A   | 3988.189, 2992.717 | -3.0, -1.85   | 1.0 x 0.75 | rect |
| B   | 4011.811, 2992.717 | +3.0, -1.85   | 1.0 x 0.75 | rect |
| C   | 3988.189, 3007.283 | -3.0, +1.85   | 1.0 x 0.75 | rect |
| D   | 4011.811, 3007.283 | +3.0, +1.85   | 1.0 x 0.75 | rect |

Cross-check vs datasheet PCB layout (drawing rev A0): pad columns 7.0 outer / 5.0 inner
in x -> center-to-center 6.0mm ✓ (matches ±3.0 with 1.0 wide pads); rows 4.5 outer /
3.0 inner in y -> center-to-center 3.7mm ✓ (matches ±1.85 with 0.75 tall pads).
Body 5.1 x 5.1mm, 6.5±0.25 over leads.

## Internal pairing (CRITICAL)

A–B internally common (top rail), C–D internally common (bottom rail); the switch
closes top-rail-to-bottom-rail. Route net1 to {A,B}, net2 to {C,D} — never both
nets onto the same rail. Source: circuit diagram on drawing TS-1187A-X-X-X rev A0;
EasyEDA symbol agrees (pins labeled A/B on one side, C/D on the other).

EasyEDA symbol pin-number-to-letter map (if numeric pads are ever used):
pin 1 = B, pin 2 = A, pin 3 = C, pin 4 = D.
