subject: usb-hub-3s-v4 exact placed board a8404ae41e79
date: 2026-08-11
reviewer: Codex root, adversarial physical-pin/package-land pass over exact board, circuit JSON, dossiers and manufacturer lands
independence_limit: same task owns design and review; P-PINMAP and direct pcbnew inspection are independent instruments, but external-human independence remains a declared process boundary
review_stage: pre-route
review_kind: pin
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: a8404ae41e79fb12a9428e40100be15e66aa58a752e795845e6920c0d083160b
parts_sha256: 61b5e8c654c88512b75d139c4fd3caff4a17dafec9cbc3b0e32c028742b25c8f
design_rules_sha256: 44e0cf9caa8eb833647413b7f8af90907852b9fcee18efbc54081117af9e5cd6
circuit_json_sha256: b40a3c9f3ad9e15108c98eec1026861c4351c6104ba889acc9d4647e16b959a4

# Pre-route physical-pin and package-land review

## Verdict

No P0/P1 physical-pin, pad-order, package-land, polarity or fused-land finding
remains. The exact placed board is SOUND to proceed to routing under this
lens. It is unrouted and not an order candidate.

P-PINMAP passes 16 multi-pin references and 160 declared physical pin
identities. S-COUNT passes all four generated representations over 76 refdes.
The board generator independently passes 18 named pad/net assertions.

## Critical sweep

- U1 TPSM63610 uses the exact 22-position RDF0022A perimeter/ground-land
  pattern measured from TI's TPSM63610EVM editable board. VIN is physically on
  the west after rotation 90, VOUT on the east, and all four split ground lands
  retain their identities and via fields. SW, VCC and NC are explicit
  no-connects as required by the module pin table.
- U2 TPSM63604 uses the exact 20-position RDL0020A land measured from TI's
  pin-compatible TPSM63606EVM. Rotation 90 likewise places VIN west and VOUT
  east. SW, VCC and NC remain explicit no-connects; every split ground land is
  present.
- U3 TPS25810 retains pins 1-20 plus the grounded exposed pad: input pins 2-8
  are `5VC_RAW`, output pins 14/15 are `VBUSC`, pins 11/13 are separate CC1/CC2,
  and REF/REF_RTN are distinct pins 10/9. Debug/audio/polarity/UFP/LD_DET are
  explicit no-connects, not silently omitted.
- U4-U6 TPS2557 instances preserve GND, three IN lands, ILIM, two OUT lands,
  FAULT and exposed GND. The three cells are exact structural repetitions;
  no port net crosses into another port.
- U7/U8 TPS2513 and D2-D4 USBLC arrays preserve each USB-A D-/D+ identity.
  Those nets terminate in their local charging-signature cells; they are not
  board-wide USB data pairs.
- J2-J4 GCT USB1130 lands preserve VBUS=1, D-=2, D+=3, GND=4 and both grounded
  shell stakes. Their horizontal mouths face the east board edge. The exact
  2.26 mm shell holes and 0.92 mm contact holes come from GCT's drawing.
- J5 GCT USB4105 preserves all 17 logical contact/shell identities. All four
  VBUS contacts share `VBUSC`, all four GND contacts and shell stakes share
  GND, A5/B5 remain separate CC1/CC2, and every D+/D-/SBU contact is an
  explicit no-connect. The connector is power-only and cannot carry USB data.
- D6 TPD2EUSB maps CC1/CC2/GND in the manufacturer order. Q1's three source
  and four drain lands preserve the P-channel reverse-polarity orientation;
  D1 and D5 retain their cathode/anode assignments. F1's duplicated physical
  holder clips are explicit same-net aliases rather than lost pins.

The project-local aliases for GCT, TI and the frozen `SOT-9X3` name all load in
KiCad and their actual pad sets—not library labels—are what P-PINMAP grades.

design_verdict: SOUND
order_verdict: DO-NOT-ORDER
