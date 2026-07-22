# ADR 0006 — USB-A port connector: 1001-011-01101 replaced by KH-AF90DIP-112

Status: accepted 2026-07-21 (post fresh-context pin review, pre-release)

## What the review caught

The fresh-context pin review (verification stage) rendered the archived
CNC Tech 1001-011-01101 drawing and read its title block: **"USB 4P AM
SMT"** — a USB Type-A **male plug**, SMT, rated **1.5 A max**. The parts
stage had recorded it as a receptacle; every downstream artifact (SMD
footprint, netlist, silk) was consistently wrong together, which is
exactly the failure mode the fresh-context protocol exists to catch
(machine gates compare project artifacts against each other; the review
compares them against the world).

Two independent defects:
1. **Gender**: a charging hub needs FEMALE receptacles; a male plug on
   the board mates with nothing a user owns.
2. **Rating**: 1.5 A max vs the D1 spec (2 A continuous, 2.5 A burst).

## Decision

Replace with **Kinghelm KH-AF90DIP-112** (LCSC C503996, stock 12 862 on
2026-07-21): USB 2.0 Type-A FEMALE receptacle, right-angle through-hole.
Vendored footprint `usb_hub_3s:KH-AF90DIP-112_Horizontal` drawn to the
vendor drawing's own PCB pattern (signal holes Ø1.0 at 2.5/2.0/2.5 mm,
shell holes Ø3.0 at 13.24 mm, 2.6 mm forward of the pin row); contact
order is the USB-standard 1=VBUS, 2=D−, 3=D+, 4=GND.

THT lands: JLC through-hole assembly optional; hand-solder fallback
stays on the ORDER_README list.

## Contact-rating disposition (the honest part)

Kinghelm states no current rating (contact resistance ≤30 mΩ). USB-A
contacts are a 1.5 A-class part per the connector standard — there is no
"2.5 A-rated" classic A receptacle; every 2.4 A phone charger on the
market runs the same contact system. Dissipation at the 2.5 A burst:
I²R = 2.5² × 0.03 ≈ 0.19 W in the VBUS contact — warm, standard, and
burst-limited by TPS2557 ILIM (2.72–3.29 A) upstream. Continuous spec
remains 2 A. Accepted as industry practice, recorded here rather than
silently passed.

## Residual risk + mitigation

Pin-1 assignment rests on the USB mechanical standard (which fixes the
contact order relative to the shell) and the Stewart-template footprint.
Mitigation: JLC order-preview check + first-power VBUS continuity check
port-by-port before plugging in a device (ORDER_README ritual).
