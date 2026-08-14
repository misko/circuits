subject: Pluto RX2 8-Way v5 exact-board physical-pin renewal with J12 bench power
date: 2026-08-14
reviewer: Codex fresh-context physical-pin reviewer
context-given: current v5 exact artifacts only
review_stage: pre-route
review_kind: pin
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 3fc9efc86e75025084e7b0a4555e7417adfa6f3a07c22129de7ca7fc6b6ff9dd
parts_sha256: e275db04f5e06b63d92714a9bb6f3c609f447e41d74a042001161ed2cc9bf6cb
design_rules_sha256: f5837640a458d8dfeb85e076ae7b501c87a30d3c880be0e44efe480d303299d8
circuit_json_sha256: 3ba4cf6381822872ac295705c5bab3479b1fe75fc5337b4b05eeb09d7c3a1ac8
kicad_schematic_sha256: 9f373e13e6eb008e96d0d90521d585e8e2f17e17d0aa3561ab36ec3c03b32b45
bom_sha256: 6583037303ee74a7d569563c11034ad375e4c351c9f5f503b8dd206abaca5523
cpl_sha256: ae54c2d6efd0e6d2a8b4b792d56307ba197d9dbb87b8709c319a17e0d10c9ff0

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

## Targeted post-route-cleanup renewal

A fresh current-worktree-only review verified that the only rule-digest delta
is post-route cleanup and stricter stitch-via site screening. It changes no
pin, net, footprint, placement, BOM/CPL identity or prepared/promoted route
copper. Exact replay identifies twelve unused single-layer barrels and retains
every barrel that the routed NRST/SW_V3 paths, U1 exposed-pad field or GND
plane drops actually use. P0/P1/P2: none; **SOUND** under the digest above.

The final R3.1 renewal retains R3.1=3V3 and R3.2=SW_V4, ends the source-owned
3V3 dogbone at an assembly-safe via outside the resistor land, and changes no
pin or net identity. The post-route bridge is same-net and wholly contained in
the existing via copper envelope. P0/P1/P2: none; **SOUND**.

## 2026-08-14 focused J12 bench-power renewal

Fresh inspection of the exact artifacts bound above confirms J12 is exact CJT
`A2541WV-2P` / LCSC `C225477`. Pin 1 is the square 1.00-mm drilled land at
`(54.00,77.00)` on `VBUS_RAW`; pin 2 is the round 1.00-mm drilled land at
`(51.46,77.00)` on GND. The 2.54-mm pitch, 1.00-mm drills and body geometry
agree with the retained manufacturer recommendation of 1.02 +/- 0.05 mm holes.
The netlist, schematic, board and dossier agree on both pins, and the generated
BOM/CPL carry J12 as `C225477` with its measured part-specific JLC rotation.

J12 joins J1 only at `VBUS_RAW`, upstream of the existing F1 fuse, D1 clamp and
U3 regulator. It therefore does not bypass the board's existing passive input
protection. It also has no reverse isolation: the explicit operating contract
is one 4.75--5.5 V source at a time, with polarity checked before energizing.
P0/P1/P2 findings: none; **SOUND / DO-NOT-ORDER** remains the verdict.
