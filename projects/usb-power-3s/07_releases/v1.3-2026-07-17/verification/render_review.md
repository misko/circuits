# Render review — usb-power-3s v1.3 (schematic-only change)

v1.3 replaces every GND global-label plate with a standard KiCad power
symbol (ground triangle) at the pin tip — 82 icons. The engine
(schwriter2) emits a `(power)`-flagged GND symbol whose hidden power_in
pin (named "GND", length 0 at the connection point) names the net; refs
#PWR01-#PWR82 are virtual (in_bom no both sides) so BOM/netlist/parity
see nothing. Value text is HIDDEN (the icon is unambiguous). One
PWR_FLAG (#FLG01, hidden power_out) rides on J1 pin 1 (XT60 "-") so
ERC's power_pin_not_driven check stays at zero. Rails (VBATT/VSW/5V_A/
5V_C/VCC...) stay labels by design. Fab files byte-identical to
v1.1-v1.2, including the ADVANCED small-via requirement.

- Orientation verified in render crops (150dpi tiles): L-side pins
  extend the icon LEFT (angle 270), R-side RIGHT (angle 90) —
  connection point exactly at the pin tip.
- Crops inspected: region 1 (J1 XT60 "-" icon + PWR_FLAG, C15/CE1),
  region 2 (U1 LM74800 GND, C16/C2 caps), buck A/B (U2/U3
  AGND/PGND/EP, QA2/QB2 sources, CA/CB decoupler banks), USB-A region
  (U4-U6 TPS2557 GND/PAD, J2-J4 GND/SHIELD), rail clamps/LEDs. Ground
  icons present and sane, no new collisions, all 25 wires intact.
- Icons carry a real 2.8x2.0mm envelope in the layout engine; internal
  S-OCCL 0 at emission and policy_audit's independent S-OCCL confirms 0
  (icons are not text).
- Gates re-verified: ERC 0 errors, 1 warning = isolated_pin_label
  PGOOD_B — exactly the existing documented baseline (max 1); DRC +
  schematic parity 0/0/0 on the UNTOUCHED board (sha 81a01c2e
  unchanged); netlist node-for-node identical to v1.2 (68 nets / 303
  nodes); policy_audit zero FAIL.
- S6 readability: unchanged from v1.2 (same wires/chains); GND fan-out
  now reads conventionally as ground symbols instead of a label sea.
