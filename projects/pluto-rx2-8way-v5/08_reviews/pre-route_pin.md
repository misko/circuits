subject: Pluto RX2 8-Way v5 corrected exact-board physical-pin renewal
date: 2026-08-13
reviewer: Codex fresh-context physical-pin reviewer
context-given: current v5 exact artifacts only
review_stage: pre-route
review_kind: pin
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: bdb0df87886cc15ed8a3ae2aee53c97f4a4cfd49734558967240816c5c73a22e
parts_sha256: 879aa0b01010b253ad07989de128d0035d4cf4a01266eaa37b18b21a27dc1ce8
design_rules_sha256: 6e1a3d39e0600855e690a001bfaeb55ac205940686e79215721a1096347266e7
circuit_json_sha256: c66c3e1a242d03f9312fa4fc03ac90634af704041461446e9e955232c3163f63
kicad_schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
bom_sha256: 7b01a6d1fa70ae7187c5ada14a963894acca97fa4a7c893df6eba447d8a06c65
cpl_sha256: 0eab823cfe6eaa8c087d7cc429334f524a9d6e60f3751d02567c3b340d3415e1

# Fresh physical-pin renewal

## Verdict and boundary

**SOUND / DO-NOT-ORDER.** A fresh reviewer used the current exact board,
current digest-selected manufacturer documents, current part dossiers,
Circuit JSON, exported netlist, preliminary BOM/CPL and all 15 generated pin
dossiers. P0/P1/P2 findings: none. This authorizes routing the exact board; it
does not approve final copper, assembly previews, firmware or RF performance.

## Exact findings

- J1 follows GCT Rev B. The four manufacturer-defined coincident pairs are
  explicitly fused and remain on identical nets: A1/B12 and A12/B1 on GND;
  A4/B9 and A9/B4 on VBUS. A5/CC1 reaches U4.3 and B5/CC2 reaches U4.5 as
  two independent channels. USB data/SBU contacts remain open and all four
  shell stakes are grounded.
- U3 at `(89, 73.5)`, 90 degrees, retains the SBVS386E DBV top-view map
  IN/GND/EN/NC/OUT = VBUS_PROTECTED/GND/VBUS_PROTECTED/open/3V3. U4 at
  `(65, 75.3)`, 0 degrees, retains the SLLSEG9C DRL map NC/NC/IO1/GND/IO2 =
  open/open/USB_CC1/GND/USB_CC2. BOM/CPL identities and rotations agree.
- U1 RF1--RF8 map in order to J3--J10 and RFC maps to J2. Every SMA uses one
  1.50-mm RF centre hole and four 1.70-mm ground holes from Amphenol Rev C.
- U2 PA0--PA3 map in order to U1 V1--V4. SWDIO/SWCLK/NRST map to J11 pins
  2/4/10; target sense and grounds map to the standard keyed Cortex header
  without mirroring.
- U1's 24 perimeter pins and grounded exposed pad, U2/U3/U4 winding, NC20 and
  all intended opens agree across schematic, board and dossiers. The producer
  token `N3V3` normalizes to physical `3V3` without changing membership.

Blocking findings: none.

## Targeted rule renewal — deterministic package escapes

The source board, schematic, Circuit JSON, parts, BOM and CPL hashes above are
unchanged. The adopted rule digest changed only because the routing recipe now
owns short deterministic escapes and executes a no-new-via-in-pad wave gate.
A fresh independent exact-r0 review checked all 30 declared seed banks against
the physical pads: every `pin` resolves once and its saved pad, segments and
via carry the declared net. Specifically, U1.9--12 and U2.7--10 retain the
ordered `SW_V1..4` symmetry, J1.A5/B5 reach U4.3/.5 on independent CC nets,
C6.1 is NRST, J11.3/.5/.9 are GND, and U1.8 reaches C4.1 on 3V3. No pin map,
footprint or source-board placement changed. P0/P1/P2: none; **SOUND** remains
the design verdict for the exact rule digest now bound above.

The second guarded switch-wave reflection widened the four U2 fan-outs and
added explicit R4/R5/R6/R3 signal dogbones. A fresh 34/34 seed-bank pin/net
census confirms U2.7--10 remain `SW_V1..4`, R4.1/R5.1/R6.1/R3.2 remain
`SW_V1..4`, and every saved segment/via inherits that exact net. The source
board and schematic identities remain unchanged. P0/P1/P2: none; **SOUND**.

The rail-wave gate then localized one remaining router via-in-pad to R3.1.
The exact recipe now gives R3.1 its own 3V3 dogbone while R3.2 retains SW_V4;
the two physical pin identities and nets are unchanged and independently
separate. P0/P1/P2: none; **SOUND** under the current digest.
