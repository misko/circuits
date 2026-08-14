subject: pluto-rx2-8way-v5 v0.2.1-2026-08-14 physical pin and footprint review
date: 2026-08-14
reviewer: Codex exact-artifact physical pin/footprint lens
context-given: exact board, schematic, manufacturer models, BOM/CPL and drills
source_commit: 57687a87c09dd1aac6cec52fb68c34286b0dab36
board_sha256: e2d1deaf4052b18b84df02d1b5cab48e131c6debbd70a03678c3ed918b24c2d5
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Exact physical-pin and footprint review

The exact board, schematic, manifest, Circuit JSON and netlist agree on all 30
component identities. The physical-pin gate grades all 127 declared multi-pin
identities. U1 RFC remains pin 22 to J2.1 and RF1--RF8 remain pins
24/2/4/6/13/15/17/19 to J3.1--J10.1. Every SMA shell post is GND and every
connector retains the Amphenol Rev-C pattern: one 1.50-mm signal hole and four
1.70-mm ground holes.

The independent native-model gate binds the exact 901-143-6RFX STEP by SHA-256,
grades all nine connectors and finds all 45 drilled attachment centres inside
their rendered body envelopes. The measured body is inside F.CrtYd on every
connector. This closes the physical registration question that the converted
JLC catalog WRL could not answer.

J12.1 is `VBUS_RAW` and J12.2 is GND. J1 retains independent CC1/CC2 with
data/SBU open; U3 pin order, U2 PA0--PA3 to U1 V1--V4, keyed J11 SWD mapping
and D1 polarity are unchanged. BOM source identity passes 14/14 and CPL
population is 30/30. P0/P1/P2 findings are 0/0/0; the hardware is **SOUND**.
JLC uploader interpretation and through-hole service remain order-time gates.
