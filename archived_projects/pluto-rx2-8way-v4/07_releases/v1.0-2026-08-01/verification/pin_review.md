subject: pluto-rx2-8way-v4 git 8c8d0466fb3ffca63335c40b284f2f864185e058
date: 2026-08-01
reviewer: pin-review (targeted exact-artifact rebind)
context-given: full-tree
review_type: pin_review
source_commit: 8c8d0466fb3ffca63335c40b284f2f864185e058
board_sha256: 4828a4a0dab6fed6e1d17afcd806877f84cf9e77bbf9b7741d3164fb880f0e30
fab_zip_sha256: 38c7bb16f22cc58d44e2d225429ff20bbbf404376cd70972bc75c4064eabf45f
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Final targeted pin rebind

pin_review_verdict: PASS
p0_count: 0

## Evidence

- Exact HEAD, board, and Gerber-archive hashes reproduce the header values.
- The complete pin-bearing artifact set is unchanged from reviewed commit
  `344dfba0`: part dossiers, TSX source, generated and native schematics,
  footprint library, frozen netlist, BOM, and CPL have no diff. The board repair
  adds only two GND fence vias plus regenerated F.Cu GND fill; no footprint,
  pad, pin, net, placement, or population mapping changed.
- I exported a fresh KiCad XML netlist to a temporary path and independently
  compared its nodes and the saved board pads against the manufacturer-derived
  expected maps. Result: **100/100 critical pads agree, zero mismatches**:
  U_SW 25/25, U_MCU 23/23, ten SMA connectors 50/50, and LED_ST 2/2.
- U_SW remains the correct PE42482A-X top-view CCW winding. RF1..RF8/RFC,
  VDD, V1..V4, LS, all GND pins, and exposed pad 25 retain their required nets;
  pin 20's GND connection is permitted by the datasheet.
- U_MCU remains the correct RP2040-Zero module top-view CW winding: GP0..GP3
  drive `SEL_V1..SEL_V4`, GP4 drives `LED_STAT`, pad 21 is `3V3_MOD`, pad 22 is
  GND, and pad 23/5V plus unused GPIOs remain deliberately unconnected.
- Every SMA has centre pad 1 on its intended RF net and pads 2..5 on GND.
  J_ANT1..7 map to ANT1..7, J_ANT8 and J_RX1 share `RX1_MAIN`, and J_RX2 maps
  to `RX2_OUT`. LED_ST retains KiCad convention pad 1 cathode/GND and pad 2
  anode/`LED_STAT_A`.

## Findings and verdict

| Severity | Count | Result |
|---|---:|---|
| P0 | 0 | No pin-map, package-winding, connector, power-pin, exposed-pad, or polarity defect. |
| P1 pin defect | 0 | No action. |
| P2 pin debt | 0 | No action. |

`design_verdict: SOUND`. The exact repaired artifact passes final pin review.

`order_verdict: DO-NOT-ORDER`. This is not a pin or sourcing failure: the
separate exact-artifact release, vendor POFV/plug-in/controlled-impedance,
uploader orientation, and first-article gates remain open. Before payment, the
uploader must still confirm U_SW pin 1 and LED cathode orientation.
