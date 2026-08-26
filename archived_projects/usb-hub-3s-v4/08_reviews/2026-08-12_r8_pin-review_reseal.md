subject: usb-hub-3s-v4 routed r8 final pin/package reseal
date: 2026-08-12
reviewer: pin-review
context-given: full-tree (exact-artifact commission; local board/netlist/dossiers/PDFs)
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Exact scope and evidence

This time-boxed reseal reviewed only physical pin identity, footprint winding,
polarity, completed-copper pin semantics, and via-family ownership on the exact
canonical routed board. Entry and exit board SHA-256 were identical. The bound
machine evidence was `06_build/drc/gate.json` SHA-256
`b795882fe8cd6a5ade1e28fb60b4b406f65cd3148e2cf4a53d91d4413ffde116`
(zero violations, zero unconnected items, zero schematic-parity items) and
`06_build/verification/via_process.json` SHA-256
`afb11ddc257b4235b2402e42dedf60a6d1c962e565ee05b602d8a74f61c1258f`.
The exact exported netlist SHA-256 was
`cdfe6036d270e6e030a363d3e756aaebc80ea5cafc320dadc7652f1c345e9265`.

# Coverage and observations

- The board contains 95 footprints, 379 pads, 446 track segments, and 183 vias.
  All 23 active/protection/connector refs (`U1-U9`, `Q1`, `D1-D6`, `J1-J5`,
  `F1`, `SW1`) were graded. Their dossier-declared numbered-pin sets exactly
  equal their board numbered-land sets: no missing, unexpected, or
  divergent-net duplicate identity. An independent exact netlist/board
  comparison graded 206/206 identities with zero findings. `P-PINMAP` also
  graded 17 multi-pin refs / 192 declared physical identities and passed.
- The U1 RDF22 and U2 RDL20 perimeter windings, internal ground lands, and
  deliberate SW/VCC/NC open dispositions match the pinned TI top-view pin
  tables. U3's RVC20 winding and grounded pad 21 match TPS25810. U4-U6 match
  TPS2559 DRC0010J: pin 1 and pad 11 are GND, pins 2-4 IN, pin 5 active-high EN
  on `5VA`, pin 6 ILIM, pins 7-9 OUT, and pin 10 FAULT. U7/U8 match the
  TPS2513A DBV winding; U8's unused second-channel I/O lands remain explicit
  open circuits. No completed copper changes those meanings.
- U9 matches the pinned TPS259827O RGE top view and preserves the counterclockwise
  perimeter winding under board rotation. Pins 1/2/3/6/16 and split PowerPAD 25
  are `5VA_RAW`; pins 17-24 are `5VA`; pins 4/5/10/12/14 and split PowerPAD 26
  are `GND`. Pad 25 owns four `0.500/0.200 mm` filled/capped vias and pad 26 owns
  two; the separated lands, paste apertures, vias, and routed nets are not
  merged. The 14 ordinary `0.700/0.300 mm` U9-output transfers are all `5VA`.
- Q1 preserves the pinned PowerDI3333 bottom-view identity: source pins 1-3 are
  `VIN`, gate 4 is `RPP_GATE`, and drain pins 5-8 are `VBAT_FUSED`. D1 is
  cathode/pad 1 `VIN`, anode/pad 2 `GND`; D5 is cathode/pad 1 `VIN`, anode/pad 2
  `RPP_GATE`. Polarized C1, C17-C19, C22, and C23 all put pad 1 on their positive
  rail and pad 2 on `GND`.
- J1 is the deliberate board-owned non-polar terminal assignment 1=`BAT_POS`,
  2=`GND`; F1's two duplicated holes per terminal remain 1=`BAT_POS` and
  2=`VBAT_FUSED`. SW1 is 1=`GND`, common 2=`EN_BUS`, and throw 3 explicit open.
  J2-J4 are 1=individual VBUS, 2=D-, 3=D+, 4=`GND`, shell=`GND`; their data
  contacts terminate only in local charge-signature/protection circuitry.
  J5 retains all four VBUS contacts on `VBUSC`, all GND/shell contacts on
  `GND`, separate CC1/CC2 through D6, and explicit open D+/D-/SBU contacts.
- Via flags were independently enumerated 183/183: 65 filled+capped
  `0.500/0.200 mm`, 104 ordinary `0.600/0.300 mm`, and 14 ordinary
  `0.700/0.300 mm`, with zero partial protection and drill-disjoint process
  families. `A-VIA` passed 4/4 declared series banks: 11.76 A credited versus
  8.00 A at U9 OUT, and 3.91 A versus 2.849 A at each U4-U6 input boundary.

# Findings and ungraded obligations

- P0: none in this pin/package lens.
- P1: none in this pin/package lens.
- P2 — Board metadata and a passing via census do not prove JLC executed resin
  fill/copper cap or soldered every exposed land uniformly. Preserve the exact
  Type-VII order instruction, obtain fabricator acknowledgement, and verify
  coupons/cross-sections plus loaded package/via thermal rise on first article.
- P2 — The board establishes land numbering and polarity, not physical reel
  orientation or assembly execution. Final CPL/assembly-preview pin-1 and
  polarity checks, AOI/inspection, and loaded current-sharing measurements
  remain ungraded here. Sourcing, enclosure fit, full electrical performance,
  and release archive completeness are also outside this lens.

# Verdict

`SOUND / DO-NOT-ORDER`. No pin-map, footprint-winding, polarity, split-land,
via-ownership, or routed-copper semantic defect was found on the exact board.
The prior U4-U6/U9/D1 authority blockers are closed by local PDFs whose hashes
match their dossiers. The order remains prohibited until the independent
release/manufacturing lenses and explicit first-article obligations are closed.
