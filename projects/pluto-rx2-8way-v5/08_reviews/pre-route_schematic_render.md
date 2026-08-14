subject: Pluto RX2 8-Way v5 delivered schematic readability after D13
date: 2026-08-13
reviewer: Codex exact-PDF human readability review
review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
schematic_pdf_sha256: 9cbef2e62613c12b64c3d8367b602360343411974053848b02e2bb2759f5d955
netlist_sha256: 817a6cea93afa2ee3e387cf861702dfe4e06c9a8fa7af192f7f9d53cea1f2ecd
exact_netlist_sha256: e39508799698657495d058021a990f9e02c0ff7f526efbf44939f0cf13bbb795
parts_sha256: 5f5fd1858798e18facce8ed0264edf4808ce6eaa1e1e5dbde1088ee9aef6f905
design_rules_sha256: 5c8ccde65b844267b1c9c293997c979c2a26eb8264bda0369335a1c465f50640
circuit_json_sha256: c66c3e1a242d03f9312fa4fc03ac90634af704041461446e9e955232c3163f63
kicad_schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
schematic_checkpoint_sha256: 6f6506b1a405ac8fa0e753b4987183abd9f91c108b15e5c009645f36c77f8b24
authoring_source_sha256: 4959ed7107a3dae3969df2b8306b591187bda34f79720c9b410676f7908ef53b

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
