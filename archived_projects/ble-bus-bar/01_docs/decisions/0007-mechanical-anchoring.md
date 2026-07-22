# ADR-0007 — durable mechanical anchoring (v1.1, from user feedback A4)

Status: accepted 2026-07-19

## Context

A4 (verbatim in BRIEF): "for the BLE bus bar we need a better way to
anchor the board to the enclosure, lets make it durable." v1.0 shipped
4× M3 UNPLATED holes + nylon standoffs. Load cases that design cannot
carry:

1. **Lug torque**: the M5 input stud is tightened to 4–5 N·m, each M4
   port stud to 2–2.5 N·m — reacted, in v1.0, through board flex into
   corner standoffs 30–60 mm away. Torsion twists the laminate and
   cyclically loads the trunk pours.
2. **Cable mass + vibration**: 6 AWG (input) and 10 AWG ×6 (ports)
   copper hanging off the studs; automotive/solar installs vibrate.
3. **ATO fuse insertion**: blade insertion force (tens of N per
   Littelfuse insertion/extraction spec class) pushes the board DOWN
   mid-span at the F1–F6 row — v1.0 had no support anywhere near it.
4. **Nylon M3 standoffs creep** under sustained preload and crack in
   cold; unplated holes let the screw head bear on bare laminate,
   which crushes and loosens (the classic re-torque death spiral).

## Decision

**7× M4 mounting holes, PLATED barrels, Ø9.0 mm washer lands both
sides (net-free), metal standoffs** — pattern placed where the loads
enter:

```
 y=49.9:  H1(117)      H2(155)      H3(193)            [north rail]
 y=114.1: H4(117)  H5(163)  H6(193)  H7(69.5)          [south rail]
```

- **Load paths**: H5 sits 12.6 mm center / 3.6 mm copper-gap from the
  M5 input stud — the 5 N·m lug torque is reacted in SHEAR at that
  standoff, not by plate bending. H1–H3 sit between the port-stud
  pairs (circle clearance to the Ø11 stud pads 0.9–2.3 mm, verified)
  for the six M4 lug torques. The north+south rails bracket the
  fuse-holder row so ATO insertion force spans ≤33 mm to the nearest
  support (vs ~55 mm to a v1.0 corner) on BOTH sides of every holder.
  H7 reacts the GND stud (J8) 11.5 mm away and carries the south-west
  zone. NO north-west mount: the ESP32 antenna keepout (which must
  stay copper- and hardware-free) plus the USB receptacle own that
  corner, and its only loads are in-plane (USB insertion) which any
  standoff pattern reacts in shear; the corner's cantilever span to
  H1/H7 is ~55 mm with no normal-force load source above it.
- **Plated M4 + Ø9 land**: the plated barrel ties both lands into a
  rivet-like column — screw preload compresses plating, not bare
  FR4 (no crush-loosen cycle). The Ø9 land carries a DIN 125 M4 flat
  washer (OD 9) at full contact.
- **Hardware (ORDER_README)**: steel or brass M4 standoffs, M4 screws
  with flat + split washers both sides, 1.2–1.5 N·m. Standoff height
  ≥10 mm (clears the stud bolt tails + nuts under the board). NYLON
  EXPLICITLY REJECTED: nylon 6.6 creeps >2 % at room temp under the
  ~1 kN preload of a properly torqued M4 and embrittles below 0 °C;
  the v1.0 M3 nylon posts would also have reacted the 5 N·m stud
  torque as bending over a 3 mm root — marginal against nylon's
  ~80 MPa flexural strength with zero fatigue margin.
- **Electrical isolation**: lands are NET-FREE floating copper — the
  GND stud (J8) remains the only reference bond (D1). Mounting metal
  is chassis potential: the mount pads carry a 0.8 mm local clearance
  override, so 24 V copper (trunk pour, port pours) keeps ≥0.8 mm to
  any land/barrel (IPC-2221 B2 external uncoated: 0.8 mm covers
  ≥30 V). Verified by DRC (pad clearance) at the gate.
- **Board grows 64 → 74 mm tall** (+5 mm rail each side). ALL
  electrical content keeps its v1.0 absolute coordinates — stud,
  holder and connector positions unchanged, so v1.0 wiring
  documentation remains valid (only the outline and mounting pattern
  changed).

## Options kept open (documented, not forced)

- **DIN-rail**: H4/H6 are 76 mm apart on a common rail line — a
  standard 2-point DIN-rail adapter (e.g. Phoenix UM-BEFESTIGUNG
  class) bolts to them; noted in ORDER_README as an option.
- Slotted holes were considered and rejected: slots trade shear
  location accuracy (the thing reacting lug torque) for assembly
  tolerance we don't need at ±0.1 mm hole placement.

## Rejected

- v1.0 4× M3 NPTH + nylon (all four load cases above).
- 6-hole variant (no west pair): leaves the USB/module corner
  cantilevered and J8 torque reacted 60 mm away.
- Chassis-grounding the mount lands: violates D1 (single reference
  bond through J8); floating lands avoid ground loops through the
  enclosure.
