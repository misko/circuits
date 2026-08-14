subject: Pluto RX2 8-Way v5 delivered schematic readability after D18 bench-power input
date: 2026-08-14
reviewer: Codex exact-PDF human readability review
review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
schematic_pdf_sha256: eafe50122e048fde289ecfdc26dcf6e28a2bc27e6c5b232db9c9f0786da365c0
netlist_sha256: 72bea8142a167c10d90c2ad1f5a5cac519e564bbb16755808a1fcd2675200021
exact_netlist_sha256: dab68a6458c2f3070380a3c887e862a1d8277970fd8f159d498990decdfc94e0
parts_sha256: e275db04f5e06b63d92714a9bb6f3c609f447e41d74a042001161ed2cc9bf6cb
design_rules_sha256: 70af3e20c1338c9d83b96348de0f3193434e387c39241ba59cd28c73a8acfb79
circuit_json_sha256: bf7063ed5f5239afb2dc0b9785d1b82ce092a30b4687dd85d5abf62a34f064f9
kicad_schematic_path: 04_kicad/pluto_rx2_8way_v5.kicad_sch
kicad_schematic_sha256: a21b84984b934ee37d65d04976193df6f5ff2ac8747323c22397e003744c7b0f
schematic_checkpoint_sha256: f8d17bb351beb74fe62add8c62ce0d30a3788b95235db34e50a6761515f6b3bf
authoring_source_sha256: d7780efb61bf5f3f1577aef4776a7f32484847a4fd121f88ebbbf11b07b52d73

# Pre-route human schematic render review after D13

## Verdict

**SOUND / DO-NOT-ORDER.** I rendered and visually inspected all four pages of
the exact PDF bound above. Every page is present, legible and free from
blocking overlap, clipping, false junction or misleading pin label. The only
material schematic change since the retained pre-D13 review is the replacement
of TP1-TP5 by keyed connector J11 on page 4.

## Page review

- **Page 1 — USB-C power only:** The separate CC resistors, explicit USB data
  no-connects, fuse, transient shunt, LDO and decoupling remain readable.
- **Page 2 — RF switch core:** RFC/RF1-RF8, ground/EP, control inputs, pulls
  and bypassing remain unambiguous.
- **Page 3 — RF interfaces:** J2 is visibly the common port and J3-J10 are the
  eight numbered antennas; center and four shell pins are separately visible.
- **Page 4 — autonomous control:** J11 is clearly identified by exact Samtec
  part number. Pin 1 is labelled `VTREF_3V3`; pins 2/4/10 are
  `SWDIO`/`SWCLK`/`NRST`; pins 3/5/9 are ground/GNDDetect; and pins 6/7/8 are
  visibly `SWO_NC`/`KEY_NC`/`TDI_NC`. U2 and C3/C5/C6 remain legible.

The drawing therefore communicates the target-powered standard Cortex SWD
boundary without relying on a private pin list. The earlier pre-D13 render
certificate is retained separately for audit history. The PDF remains a
topology document, not fabrication or assembly proof. Blocking readability
findings: none.

The exact PDF was renewed after the placement-policy metadata repair. A direct
180-dpi raster of page 2 confirms that the long RF title is fully inside the
page and that its gray metadata is a separate unobscured line; an apparent
overlap in one scaled viewer was withdrawn as a display artifact. The PDF
bytes and normalized electrical netlist remain unchanged.

The current digest renewal is confined to post-route via cleanup/site
screening and changes no PDF, symbol, label, page geometry or schematic
topology. Fresh exact-artifact review finds P0/P1/P2 = 0/0/0; schematic
readability remains **SOUND**.

The final same-net via-contained bridge changes no delivered schematic byte or
page. P0/P1/P2: none; readability remains **SOUND**.

For the 2026-08-13 `dae8320d` renewal I reopened the current rule and part
authority, rerendered all four exact PDF pages at 180 dpi, and separately
rerendered page 2 at 300 dpi. Titles, metadata, symbols, values, pin numbers,
net labels, explicit no-connects and page boundaries remain readable without
clipping, false junctions or hidden text. The PDF hash, exact schematic hash,
normalized-netlist hash and circuit JSON hash are unchanged. The new part and
rule digests arise from the selective U1 via-process correction, which has no
rendered schematic geometry. P0/P1/P2 readability defects remain 0/0/0;
**SOUND / DO-NOT-ORDER**.

The `3ecf08ab` delta only closes the already-satisfied STM32 source-document
finding and removes stale research prose. It changes no part, design rule,
schematic or PDF byte, so all bound hashes remain current. I reopened the
four-page PDF and found no readability delta. P0/P1/P2 readability defects
remain 0/0/0; **SOUND / DO-NOT-ORDER**.

The `6d1d01ca` broad-rule renewal changes only the machine-readable J2-J10
through-hole assembly ownership and uploader stop condition. The exact PDF,
schematic, circuit JSON and normalized-netlist hashes remain unchanged. I
reopened all four PDF pages and confirmed the assembly-contract change creates
no schematic text, geometry, label, symbol or page-boundary delta. P0/P1/P2
readability defects remain 0/0/0; **SOUND / DO-NOT-ORDER**.

The `770ac064` renewal changes only the STM32 evidence bytes and dossier
provenance: official local DS13866 Rev 5 is now authoritative and the old copy
is correctly named Rev 3. The exact schematic PDF, schematic, circuit JSON and
normalized netlist remain byte-identical. I reopened all four schematic pages;
no symbol, title, value, pin, label, no-connect, junction or page geometry
changed. P0/P1/P2 readability defects remain 0/0/0;
**SOUND / DO-NOT-ORDER**.

The `4cf5c818` renewal corrects only J11's part-dossier connector-role term to
schema-valid `plug` and preserves the keyed FFSD cable-receptacle relationship
in prose. P-ESC passes 13/13. The exact four-page PDF, schematic, circuit JSON,
normalized netlist and design rules are unchanged; I found no rendered-symbol,
pin-label, page-geometry or readability consequence. P0/P1/P2 readability
defects remain 0/0/0; **SOUND / DO-NOT-ORDER**.

The current-working-tree renewal additionally reviews the regenerated pinned
native KiCad schematic at the path bound above. The converter now stacks the
four TSX sheet-local coordinate spaces on one non-overlapping native canvas.
I exported that exact native file to PDF and inspected each separated region:
USB-C power/protection, RF switch core, nine SMA interfaces, and autonomous
control/SWD are all readable at normal zoom; symbols, pin numbers, labels,
no-connect marks and wires do not clip or form false composites. The previously
superimposed J1/J2 and U1/U2 coordinate regions are visibly separated.

Independent `sch_occlusion.py` grades all 202/202 drawable objects (51 wires,
52 global labels and 99 symbol instances), reports S-WNET = 0 and S-OCCL = 0
against the zero ceiling. A fresh native export retains canonical netlist
digest `817a6cea...`, while the authored four-page tscircuit PDF remains
byte-identical. The ten strengthened dossier citations were checked against
their retained manufacturer pages/sheets/drawings and are supported. The two
pending floorplan silk-caption edits have no schematic-render consequence and
remain subject to later board replay/review. P0/P1/P2 readability defects are
0/0/0; **SOUND / DO-NOT-ORDER**.

For D18 I rasterized and inspected all four pages of the regenerated exact
PDF. Page 1 now has ten components and clearly shows J12 below the
`VBUS_RAW` input trunk: pin 1 is labelled `BENCH_5V`, pin 2 is labelled GND,
and the page title states `USB-C OR J12 BENCH 5 V — one input only`. J12 does
not overlap J1/F1, no pin label is clipped, and the long input trunk has no
false junction. Pages 2-4 are visually unchanged and remain readable at
normal zoom. P0/P1/P2 readability defects are 0/0/0; **SOUND /
DO-NOT-ORDER** pending physical placement and routing review.

For the strict-RF integration renewal I regenerated and inspected all four
pages again at 150 dpi and checked every PDF text bounding box against the
900 x 607.5 pt media box. All titles, metadata, symbols, values, pin labels,
no-connects, and page boundaries remain within the page. The new RF rules and
rounded copper do not alter schematic drawing content; page 1 still exposes
the one-input-only J1/J12 rule and pages 2-4 remain unambiguous. P0/P1/P2
readability defects remain 0/0/0; **SOUND / DO-NOT-ORDER**.
