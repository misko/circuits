subject: USB Hub 3S v4 exact track-free placement
date: 2026-08-12
reviewer: Codex fresh-context independent pre-route layout lens
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: e0c6e592f5063d0e7af710c3682f05cfb2f577adff22e79132ac9a84c7f8621e
design_rules_sha256: 1836747093e3a866efaae089ac787a6db42133ead8d09d0dc948c9b35a20af21
floorplan_sha256: bc08b2c6fd2cdd80c259a358d2788a1c5a99637d5727cd4264f8f40d5787d4ad
route_yaml_sha256: 8fd03f968e4f86403ae60b2e050d6b033f827b3ce1b8d737d19a0dbd827f3874
prepared_r0_sha256: 805308ae35a3042c43a533fed3bfa1777437ee766848d5b1696a5b58af11d94c
promoted_r8_sha256: 8ea0f50681d48c34c6e5f300cc8842f144937cd92fb118cad6a546d19acf173f
placement_drc_sha256: adc06f14e3b19c7aa3856d0926c45a2d7362fff4681b61c57d2e4a3dfd7bebaa
top_render_sha256: 14991062778cee2e4888696c7effa0c9ade3ed3edcf3109bf9dc5fe00be23560
iso_render_sha256: 98f313e57998b6f4e5b17612cb7bea6124f2173a3f60e2c199ad299c89140f3c

# Independent pre-route layout review

## Scope and method

I independently parsed the exact board with pcbnew, inspected the exact native
top and isometric renders at full resolution, reran the placement/body,
pad-separation and land-escape gates, read the current placement-policy report,
and compared the realized component relationships with the vendored
manufacturer layout guidance for the two power modules, TPS25982, TPS2559,
TPS2513A, TPS25810 and the connector-side ESD devices. I did not use a prior
layout verdict as evidence and did not require completed routing.

The subject contains 95 footprints, 48 zones, zero track segments and 48
placement-owned 0.50/0.20 mm filled/capped vias. The current exact refilled
placement DRC (`06_build/drc/pre_route.json`, generated after the board) reports
seven permitted preliminary `isolated_copper` findings, 118 expected unrouted
connections, and zero schematic-parity findings. The older
`pre_route_exact.json` count is stale and receives no credit.

## Findings

- **Functional floorplan and power flow — sound.** The physical story reads
  west to east: J1 -> F1 -> Q1 -> VIN; U1 feeds the protected USB-A aggregate
  path through U9, while U2 feeds the independent attach-controlled Type-C path
  through U3. The three USB-A cells repeat at 24 mm pitch and face outward on
  the east edge. J5 faces outward on the south edge. The fuse, master switch,
  battery terminal and every receptacle remain unobstructed.
- **Converter modules — sound.** U1 and U2 have symmetric input capacitors at
  2.35/2.36 mm and 1.60/1.60 mm pad-centre distance respectively. Their nearest
  output ceramics are 2.07 mm (U1) and 3.45 mm (U2); the remaining bank fans
  outward without blocking escape. BOOT resistors are 2.4--2.7 mm from their
  pin pairs, RT parts about 2.0 mm away, and the first FB parts 1.91 mm (U1) and
  3.21 mm (U2) away. The four ground lands on each module own two same-net
  Type-VII vias each, and both inner layers are uninterrupted GND planes. This
  is consistent with TI's symmetric capacitor, short feedback/BOOT/RT and
  thermal-land guidance.
- **U9 aggregate eFuse — sound with a route-preservation condition.** R26
  (ILIM), C29 (ITIMER) and C30 (dV/dt) are on the corresponding outward-facing
  pin sides at 2.03, 2.38 and 1.43 mm respectively; none must cross the package.
  PowerPAD 25 owns four 0.50/0.20 mm raw-rail vias and GND PowerPAD 26 owns two,
  with no accidental bridge between the split pads. The OUT lands face the
  protected distributor and the prepared contract reserves a 2.10 mm-deep
  collector plus fourteen ordinary transfer vias. The nearest 5VA_RAW ceramic
  bank is 11.28 mm from an IN land, not pin-adjacent. TI recommends the bypass
  closest to IN/GND but permits it to be minimized or omitted when input-path
  inductance is negligible; this short same-board module-to-eFuse plane path is
  acceptable at placement. Final copper must preserve a broad direct return
  with no neck/noisy coupling, and first-article input/output transient evidence
  remains mandatory.
- **USB-A cells — sound.** U4/U5/U6 each place the 100 nF input bypass 2.12 mm
  from an IN land, ILIM resistor 4.07 mm from the ILIM pin, and output bulk
  capacitor 3.90 mm from an OUT land. Each exposed pad owns six Type-VII ground
  vias. Their power sides face the B.Cu distributor and their output sides face
  separate broad VBUSA zones. D2/D3/D4 lie connector-side of the charge-
  signature branches; the approximately 8 mm exposed-contact-to-clamp runs are
  short, repeated and routeable for charge-only D+/D- lines. U7/U8 and their
  100 nF bypass capacitors remain local to the signature branches.
- **Type-C cell — sound.** U3 sits between the cold-socket capacitor bank and
  J5. C12 input bypass is 2.75 mm from IN; C13 output bulk is 3.14 mm from OUT;
  the REF/REF_RTN resistor is 2.81 mm from both pins. D6 is 2.95 mm from each
  connector CC land and precedes the controller; the prepared CC1/CC2 seed
  launches preserve separate, symmetric connector escapes. U3's ground pad
  owns six physical Type-VII vias and C23 owns two local GND return vias.
  No USB data or RF routing is commissioned.
- **Mechanical and assembly geometry — sound.** Fresh P-OUT measured a 1.55 mm
  tightest pad/outline margin. P-BODYCLR graded 88 assembled envelopes with zero
  close/overlap or envelope-to-foreign-pad findings at the positive 0.10 mm
  floor. P-PADSEP graded 346 pads, 57,771 inter-footprint pairs and 94,480
  paste-to-foreign-copper pairs at the 0.09 mm advanced-tier floor with zero
  failures. J5's intentional body/courtyard overhang follows its manufacturer
  PCB-edge datum; its copper remains inside. All four M3 holes have usable
  approach space, and the three top fiducials are non-collinear and clear.
- **Route feasibility — sound.** P-CAP's worst board cut is three demanded nets
  against 216-track estimated capacity. P-LAND grades 100 applicable lands,
  including three scoped launches, with zero unreachable lands. The exact
  prepared r0 preserves the 48 placement vias and adds the reviewed connector
  escapes and series-transfer reservations without changing placement. These
  facts establish credible routing corridors; they do not claim routed copper.
- **Test and silkscreen access — sound.** TP1--TP12 expose VIN, both regulated
  paths, VBUSC, EN, both PG nodes, four fault nodes and GND in open central
  areas. Every assembled electrical component has a visible F.Silkscreen
  reference. Functional legends identify battery polarity, fuse rating,
  hard-off switch, power-only/no-data behavior, each port rating and no-PD
  Type-C behavior. Mounting-hole and fiducial references are intentionally
  hidden; their geometry is unambiguous.

The placement-policy gate passes, but its P-ADJ and P-ADJ-PAIR rows are N-A
because the dossiers carry narrative layout constraints rather than numeric
`keep_short`/adjacency budgets. The measurements above are therefore human
review evidence, not a claim that the machine gate checked those distances.

## Disposition and limits

P0: None.

P1: None.

P2: Preserve the U9 short/broad input path and split-pad ownership, its full
OUT collector/transfer bank, both converter capacitor/feedback corridors, the
three repeated USB-A transfer cells, U3 REF keepout, connector-first CC and
charge-line clamps, test-point access and all functional silk during routing.

The exact track-free placement is **SOUND** for routing. It is **DO-NOT-ORDER**:
this review does not grade completed copper, filled-zone current sharing,
thermal rise, JLC catalog-body registration/rotation, production files,
assembly coverage, stock, or first-article electrical qualification.
