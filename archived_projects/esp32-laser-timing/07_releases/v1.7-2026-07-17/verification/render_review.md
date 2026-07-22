# Render review — esp32-laser-timing v1.7 (schematic-only change)

v1.7 replaces every GND global-label plate with a standard KiCad power
symbol (ground triangle) at the pin tip — 46 icons. The engine
(schwriter2) emits a `(power)`-flagged GND symbol whose hidden power_in
pin (named "GND", length 0 at the connection point) names the net; refs
#PWR01-#PWR46 are virtual (in_bom no both sides) so BOM/netlist/parity
see nothing. Value text is HIDDEN — the icon is unambiguous; visible
"GND" text would recreate the noise being removed. One PWR_FLAG
(#FLG01, hidden power_out) rides on J1.A1's tip so ERC's
power_pin_not_driven check stays at zero. Rails (5V/3V3) stay labels by
design. Fab files byte-identical to v1.1-v1.6.

- Orientation verified in render crops (250dpi): L-side pins extend the
  icon LEFT (angle 270), R-side RIGHT (angle 90) — connection point
  exactly at the pin tip. Sideways ground icons are standard practice.
- Crops inspected: J1 USB-C GND bank (A1/A12/B1/B12 + PWR_FLAG),
  C11/C12 bulk caps, U1 ESP32 GND/EPAD pins, U3 LM339 GND, Q1-Q3
  source pins, VTH divider region. Ground icons present and sane, no
  new collisions, all 16 wires intact.
- Known minor: the PWR_FLAG glyph on J1.A1 slightly brushes the "A1"
  pin-number text (pin numbers are not part of the envelope model).
  Legible; accepted.
- Icons carry a real 2.8x2.0mm envelope in the layout engine, so
  spacing math stays collision-free; internal S-OCCL 0 at emission and
  policy_audit's independent S-OCCL confirms 0 (icons are not text).
- Gates re-verified: ERC 0 total at severity-all (PWR_FLAG satisfies
  the power_in driver requirement); DRC + schematic parity 0/0/0 on the
  UNTOUCHED board (sha 870b65e4 unchanged); netlist node-for-node
  identical to v1.6 (61 nets / 214 nodes); policy_audit zero FAIL.
- S6 readability: unchanged from v1.6 (same wires/chains); GND fan-out
  now reads conventionally as ground symbols instead of a label sea.
