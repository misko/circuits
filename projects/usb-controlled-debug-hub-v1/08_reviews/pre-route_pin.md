# Pre-route pin review — USB Controlled Debug Hub v1

review_stage: pre-route
review_kind: pin
reviewer: independent-agent (fresh exact-artifact pin/connector re-audit)
reviewed_at: 2026-08-16
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 523ef6c6665d4f3c91f3b073b764bf13a86ca8dd18bfacd339f597555a3b1d86
prepared_r0_sha256: 66c4b55ee1c5c59fecce2356fe86c603e32cd99d01685ae54de7b6d7c512eb26
parts_sha256: 737e094242d31f2989dca17f67f3e86c85a55bd023ef09eb2d01e04150149da2
design_rules_sha256: b2e7dee272545938667ca333de08555eed6938b854e999e68d2e69c60aa9bcc6
nets_sha256: 076104230e08f62e3957c8a788f6d7bb1ed238247a7dc9de997e494168f3a258

## Findings

- P0: none.
- P1: automated datasheet evidence generation is not fully reproducible.
  `pin_audit.py` stops at `PESD2USB3UX-TR` because its dossier lacks a
  digest-selected local PDF. Independent review of the manufacturer pin
  authority found no corresponding pin/net defect. Add the pinned evidence
  before release.
- P2: none.

## Exact subjects and authority

- The checker-normalized KiCad netlist SHA-256 is
  `3a03dd6c9d770c4d820ffb2b228f482adec3715ec350f65c07be13511b708662`;
  its raw SHA-256 is
  `0d3fbddb082f4e1772205914cc65cbb9c8241c96a6e5152c5e32c68bb4e53087`.
- The nine-page schematic PDF SHA-256 is
  `caf453be6210b81c2e6d928bbf897bed2a86d8a234769bd90f7b7ad25def9d1c`;
  current TSX SHA-256 is
  `595bc3d60fc781ae08d1de825c273f23db3a66a9261904425baf251da3176590`.
- TE drawing ENG_CD_292304 revision D4 is locally digest-bound at
  `1cf7e9b81d3071586b98174bfea75b38a9c63589428fbd3eeecdb5d4b9543476`.
  The exact project footprint SHA-256 is
  `ffbe155c351b652c4b73a1c14c8dd788e1f625f97e04e809727994509f2e4c4b`.

## J_UP physical pin and mating review

- J_UP is the exact TE 292304-1 / JLC C86462 USB Type-B receptacle at
  (32.2, 57.0) mm, front-side rotation 270 degrees, not flipped. The TE front
  mating view numbers the contact rectangle as 2/1 on the upper row and 3/4
  on the lower row. The footprint reproduces that order with 0.92 mm drills at
  local pad coordinates 1=(+1.25,-2), 2=(-1.25,-2), 3=(-1.25,0) and
  4=(+1.25,0) mm.
- The exact board therefore realizes pad 1 at (34.2,58.25) on `USB_UP_VBUS`,
  pad 2 at (34.2,55.75) on `UP_HUB_N`, pad 3 at (32.2,55.75) on
  `UP_HUB_P`, and pad 4 at (32.2,58.25) on GND. The 2.5 x 2.0 mm contact
  rectangle, pin numbering and VBUS/D-/D+/GND identities agree with the
  drawing and schematic.
- The two 2.3 mm shell board-lock holes are 12.04 mm apart with the drawing's
  2.71 mm offset. They appear at (29.49,50.98) and (29.49,63.02) mm and are
  deliberately fused as duplicate physical pad 5 on GND, matching the dossier
  and schematic shell identity.
- The footprint's connector access direction is local +Y. At the realized
  rotation it maps to board -X, toward the west edge. The current exact-board
  orientation receipt independently measures access axis [-1,0,0], model/
  footprint alignment 1.0 and mating-plane edge offset 0.25 mm, all PASS.
  Thus the receptacle faces outward and remains cable-accessible.

## Upstream and management lane identity

- The complete upstream D- chain is J_UP pad 2 -> `UP_HUB_N` -> U_ESD_UP
  pin 1 -> USB2517I upstream DM pin 58. The complete upstream D+ chain is J_UP
  pad 3 -> `UP_HUB_P` -> U_ESD_UP pin 2 -> USB2517I upstream DP pin 59.
  U_ESD_UP common-anode pin 3 is GND. The current route seeds begin on those
  exact ESD pads, land on J_UP pads 2/3 without a logical crossing, and keep
  the VBUS/GND row out of the B.Cu signal approach.
- The explicit layer crossover preserves electrical identity and continuity.
  `UP_HUB_N` remains on B.Cu from U_ESD_UP pad 1 through J_UP pad 2, changes
  to F.Cu only through the declared same-net via at (38.1,57.77), and reaches
  its handoff at (39.2,57.77). `UP_HUB_P` runs from U_ESD_UP pad 2 on B.Cu to
  J_UP pad 3, uses that same-net plated through-hole contact as its only layer
  transition, then reaches its F.Cu handoff at (39.2,58.154). Graph traversal
  of every declared seed bank, crediting only exact same-layer edges plus a
  declared via or same-net plated through pad, proves continuity for 48/48
  banks. No P/N edge or transition is assigned to the opposite net.
- The additional anonymous seed bank contains no `pin` claim and no signal
  segment. It declares one via at (38.1,56.9) on GND with the explicit reason
  `UP_HUB N layer-transition return path`. The exact r0 object at that location
  is a 0.2 mm-drill GND via. It is neither assigned to `UP_HUB_N` nor
  `UP_HUB_P`, does not touch their declared centrelines, and does not pretend
  to establish connectivity to a component pin.
- `USB_UP_VBUS` contains only J_UP pad 1 and the R_VBUS_TOP sense-divider
  input. It has no path to the protected 5 V source, so the corrected connector
  pin map does not create an upstream-VBUS backfeed path.
- USB2517I downstream management port 1 is a separate deliberate swap:
  physical DM1 pin 1 carries `MGMT_P`, physical DP1 pin 2 carries `MGMT_N`,
  and R_SWAP1 pad 2 is `3V3_MAIN`. With CFG_SEL[2:0]=000 this asserted
  `PRT_SWP1` makes the logical association correct. MCP2221A pin 13 is
  `MGMT_P`/D+ and pin 12 is `MGMT_N`/D-. External R_SWAP2..7 remain grounded.
  The management swap does not alter the normally mapped J_UP-to-upstream-
  DM/DP path.
- The deterministic management seeds now form exactly one complete component
  per net. Exact graph traversal proves U_CTRL pad 13 -> `MGMT_P` -> U_HUB pad
  1 and U_CTRL pad 12 -> `MGMT_N` -> U_HUB pad 2, with every authored node
  reached from its controller pad. Both paths use F.Cu exclusively with zero
  vias; P/N endpoints never coincide and fresh DRC finds no cross-net contact.
  MGMT preflight now consumes `source: seed_stubs`, declares the pair as
  `MGMT_P`/`MGMT_N`, restricts it to F.Cu and requires no vias, agreeing with
  the complete realized paths rather than delegating their closure to KRT.

## Complete exact-artifact checks

- The canonical board and r0 each contain 146 footprints and 593 physical
  pads. Their complete reference/pad/net/position/drill maps are identical.
  The track-free board has zero copper items; r0 has 321 prepared copper items,
  including 120 vias. No footprint or pad identity changes during preparation.
- All 48 pin-owned seed banks start at an exact board pad carrying the declared
  net. All 183 expanded line primitives match same-net, same-layer and
  same-width r0 copper within 0.0011 mm. The pin-owned crossover via and the
  separately declared anonymous GND return via also exist at their exact
  coordinates on their declared nets. This proves preparation retained the
  authored pin/net identities without attributing the return via to a pin.
- `P-PINMAP` passes 22 multi-pin references / 265 declared physical pin
  identities. `S-COUNT` agrees 4/4 over 139 component references. `E-INV`
  passes 82/82 and `E-ADR` passes 4/4.
- Placement gates pass with zero failures or warnings. Fresh board DRC reports
  zero error violations, zero schematic-parity findings and 375 expected
  unconnected items on the track-free subject. Fresh r0 DRC reports zero error
  violations, zero schematic-parity findings and 364 unconnected items.

## Verdict boundary

The exact current schematic-to-footprint pin mapping, corrected J_UP contact
pattern, outward mating direction, shell grounding, upstream D-/D+ path and
management-port swap are SOUND. Findings are P0/P1/P2 = 0/1/0. This is a pin-
identity verdict only: it does not authorize routing, fabrication or ordering.
