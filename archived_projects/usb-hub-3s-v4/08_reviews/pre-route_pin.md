subject: USB Hub 3S v4 exact track-free placement
date: 2026-08-12
reviewer: Codex fresh-context pin/package reviewer r19
review_stage: pre-route
review_kind: pin
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: e0c6e592f5063d0e7af710c3682f05cfb2f577adff22e79132ac9a84c7f8621e
parts_sha256: 07da71701403799d279677f0a50f5817940c5a0b2cf15cdb2521b0860d563d97
design_rules_sha256: 1836747093e3a866efaae089ac787a6db42133ead8d09d0dc948c9b35a20af21

# Fresh pre-route pin/package review

The exact board, normalized netlist, circuit JSON, local `part.yaml` dossiers,
and vendored manufacturer PDFs were reviewed. P-PINMAP independently passes all
192 declared physical identities across 17 multipart references. The board is
intentionally track-free: its 48 copper items are the 48 authored thermal vias,
not routing.

- **U9:** PASS. RGE0024 perimeter pads retain the TI top-view winding: IN
  1/2/3/16 and distinct IN PowerPAD 25 are `5VA_RAW`; GND 4/5/14 and distinct
  GND PowerPAD 26 are GND; OUT 17-24 are `5VA`. Pad 25 owns four `5VA_RAW`
  0.50/0.20 mm filled/capped vias and pad 26 owns two GND vias. No split-pad
  bridge or foreign-net via was found.
- **Polarity:** PASS. D1 pad 1/cathode is `VIN` and pad 2/anode GND; D5 pad
  1/cathode is `VIN` and pad 2/anode `RPP_GATE`. C1, C17-C19, C22 and C23 each
  put pad 1 on the positive rail and pad 2 on GND.
- **Active packages:** PASS. U1 RDF0022A, U2 RDL0020A, U3 RVC0020A/EP21 and
  U4-U6 DRC0010J/PowerPAD11 match their local dossiers and manufacturer top-view
  pin maps. Every repeated VIN/VOUT/GND land is present; SW/VCC/NC or mode pins
  that are required open remain explicit unconnected nets. U1/U2/U3/U4-U6
  exposed-ground lands own the declared GND via fields.
- **Input and connectors:** PASS. J1 is BAT+/GND; F1 preserves its explicitly
  fused duplicate lands from `BAT_POS` to `VBAT_FUSED`; SW1 has pin 2 common on
  `EN_BUS`, pin 1 OFF on GND and pin 3 explicitly open. J2-J4 retain
  1=VBUS, 2=D-, 3=D+, 4=GND plus grounded shells. J5 retains all sixteen GCT
  alphanumeric contacts and grounded shell stakes: four VBUS contacts are
  `VBUSC`, four GND contacts are GND, A5/B5 are separate CC1/CC2, and all six
  D+/D-/SBU contacts are explicit no-connects.
- **Other active mappings:** PASS. D2-D4 retain IO1 1/6, IO2 3/4, GND 2 and
  local VBUS 5; D6 has separate CC1/CC2 at pins 1/2 and GND at pin 3. U7 and
  U8 match the TPS2513A DBV winding; U8's unused second channel is explicitly
  open rather than merged.
- **Physical-land completeness:** PASS. No required pad is absent, no distinct
  manufacturer contact is collapsed, and every duplicate/fused physical land
  is declared by the dossiers. The exact board contains 48 protected vias:
  U1 8, U2 8, U3 6, U4/U5/U6 6 each, U9 pad25 4, U9 pad26 2, and C23 pad2 2.

No pin winding, polarity, exposed-pad, connector-contact, missing-land or
merged-land defect was found. `SOUND` applies only to this exact track-free
pin/package realization. `DO-NOT-ORDER` remains mandatory because routing,
filled-zone connectivity, routed reviews and manufacturing release are outside
this pre-route review.
