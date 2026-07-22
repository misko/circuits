# Render review — crowsync-recorder v1.2 (schematic-only change)

v1.2 replaces every GND global-label plate with a standard KiCad power
symbol (ground triangle) at the pin tip — 45 icons. The engine
(schwriter2) emits a `(power)`-flagged GND symbol whose hidden power_in
pin (named "GND", length 0 at the connection point) names the net; refs
#PWR01-#PWR45 are virtual (in_bom no both sides) so BOM/netlist/parity
see nothing. Value text is HIDDEN (the icon is unambiguous). One
PWR_FLAG (#FLG01, hidden power_out) rides on J1.A1's tip so ERC's
power_pin_not_driven check stays at zero. Rails (VBUS_5V/3V3A/VDDI...)
stay labels by design. Fab files byte-identical to v1.0-v1.1.

- Orientation verified in render crops (150dpi full page + zooms):
  L-side pins extend the icon LEFT (angle 270), R-side RIGHT (angle
  90) — connection point exactly at the pin tip.
- Crops inspected: J1 USB-C GND bank (+ PWR_FLAG on A1), U1 PCM2900C
  AGNDP/DGNDU/AGNDC (left icons) and DGND/AGNDX (right icons), Y1
  crystal G pins, U3 TPS7A2033 GND, U2 TLV9062 V-, decoupler banks
  (C12/C13/C15-C18/C20/C21), D3/D4 LED cathodes, J2/J3 P3/MP pins.
  Ground icons present and sane, no new collisions, all 13 wires intact.
- Icons carry a real 2.8x2.0mm envelope in the layout engine; internal
  S-OCCL 0 at emission and policy_audit's independent S-OCCL confirms 0
  (icons are not text).
- Gates re-verified: ERC 0 total at severity-all (PWR_FLAG satisfies
  the power_in driver requirement); DRC + schematic parity 0/0/0 on the
  UNTOUCHED board (sha c764ee86 unchanged); netlist node-for-node
  identical to v1.1 (44 nets / 165 nodes); policy_audit zero FAIL.
- S6 readability: unchanged from v1.1 (same wires/chains); GND fan-out
  now reads conventionally as ground symbols instead of a label sea.
