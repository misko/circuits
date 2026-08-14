subject: Pluto RX2 8-Way v5 clean-room schematic topology after D13
date: 2026-08-13
reviewer: Codex exact-artifact topology and datasheet review
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
checkpoint_sha256: 6f6506b1a405ac8fa0e753b4987183abd9f91c108b15e5c009645f36c77f8b24
circuit_json_sha256: c66c3e1a242d03f9312fa4fc03ac90634af704041461446e9e955232c3163f63
kicad_schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
schematic_pdf_sha256: 9cbef2e62613c12b64c3d8367b602360343411974053848b02e2bb2759f5d955
netlist_sha256: 817a6cea93afa2ee3e387cf861702dfe4e06c9a8fa7af192f7f9d53cea1f2ecd
exact_netlist_sha256: e39508799698657495d058021a990f9e02c0ff7f526efbf44939f0cf13bbb795
parts_sha256: 5f5fd1858798e18facce8ed0264edf4808ce6eaa1e1e5dbde1088ee9aef6f905
design_rules_sha256: 5c8ccde65b844267b1c9c293997c979c2a26eb8264bda0369335a1c465f50640
authoring_source_sha256: 4959ed7107a3dae3969df2b8306b591187bda34f79720c9b410676f7908ef53b

# Pre-route topology review after programming-connector decision D13

## Verdict and boundary

**SOUND / DO-NOT-ORDER.** The regenerated schematic retains the reviewed
receive-only one-of-eight RF topology, protected USB-C power path, autonomous
controller and fail-safe all-off bias. Decision D13 replaces five loose SWD
test pads with one keyed, standard 10-pin Cortex Debug connector. No blocking
schematic-topology, physical-pin, polarity, value or intentional-open defect
remains in the exact artifacts bound above.

This verdict authorizes PCB placement review only. It does not approve routing,
fabrication, firmware behavior, assembled orientation or RF performance.

## Exact connector delta review

- J11 is exact Samtec `FTSH-105-01-L-DV-K-P-TR`, JLC `C2932107`, a keyed
  vertical 2x5 1.27 mm SMT Cortex Debug header.
- J11.1 joins the target's `3V3` rail only as VTref/sense. J11.2 is `SWDIO`,
  J11.4 is `SWCLK`, and J11.10 is `NRST`.
- J11.3, J11.5 and J11.9 join GND. Pins 6 (SWO), 7 (key/reserved) and 8
  (TDI) remain explicit no-connects because this target exposes neither SWO
  nor JTAG TDI.
- U2's corresponding physical pins remain STM32C011 PA13 pin 18 for SWDIO,
  PA14/BOOT0 pin 19 for SWCLK and PF2/NRST pin 6 for reset.
- The Pi is not permitted to power the target. The board is powered through
  its USB-C input; J11.1 lets a probe observe the resulting target voltage.

This is the standard Cortex 10-pin mapping rather than a private harness
pinout. The connector's manufacturer-recommended SMT land pattern and exact
3D body are governed by its local part dossier; those are checked again at
placement/assembly review.

## Retained topology

The USB-C connector remains power-only: all USB data and SBU contacts are
explicitly open, CC1 and CC2 have independent 5.1 kOhm Rd paths, and the rail
sequence remains `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`. The SP8T
mapping remains RFC-to-J2 and RF1-RF8-to-J3-J10 with every SMA outer conductor
grounded. LS remains low and passive pulls still select the documented
all-ports-terminated word during controller reset. The eight active state
words and generated `fast20-v1` schedule are unchanged.

The complete source gates report 29/29 component parity, 131/131 declared pin
maps and 32/32 electrical invariants. KiCad ERC reports zero errors; the
remaining warnings are known generated-symbol presentation warnings and do
not override this human exact-artifact review.

A fresh exact-hash renewal after the placement-policy repair confirmed that
the USB fused-contact declarations, U4/J1 and U3/capacitor distance budgets,
and corrected DS13866/SBVS386E document labels do not alter connectivity,
ratings, or pin semantics. The digest-selected TPS7A24 document is SBVS386E
and its fixed-output layout example is Figure 8-7. P0/P1/P2 blockers: none.

The earlier pre-D13 topology certificate is retained separately for audit
history. Blocking findings in this review: none.

The current rule-digest renewal changes only post-route via cleanup and
stitch-via collision screening. It changes no schematic, component, pin, net,
power path, state truth table or RF topology. Fresh exact-artifact review finds
P0/P1/P2 = 0/0/0; the topology verdict remains **SOUND**.

The final same-net via-contained bridge changes no schematic connectivity or
topology. P0/P1/P2: none; **SOUND**.

The D-MATE renewal makes the existing cable boundary machine-readable without
restating values: Pluto Plus SMA gender, port order and the receiver absolute
maximum are referenced to their single `spf/plutoplus_hardware` evidence home
and graded 3/3. No dimension is consumed and no topology changes. **SOUND**.

The 2026-08-13 `dae8320d` renewal independently reopened all current part
dossiers, their retained local evidence, every adopted design-rule YAML, the
exact schematic PDF and the normalized electrical netlist. The changed part
and rule digests describe the corrected selective U1 via-process contract:
nine protected 0.45/0.25-mm filled/capped sites are drill-distinct from
ordinary 0.45/0.20-mm vias. They do not change a schematic component, value,
pin, net, truth-table word or rating. Fresh checks remain 32/32 electrical
invariants, 21/21 surviving labels, 131/131 pin-map assertions, 29/29 source
component parity and zero ERC errors. The four RF schematic requirements and
the USB-C/protection/control paths were retraced against the current pSemi,
TI, ST and connector dossiers. P0/P1/P2 schematic defects remain 0/0/0;
**SOUND / DO-NOT-ORDER**.

The `6d1d01ca` renewal rechecked the unchanged exact schematic, normalized
netlist, four-page PDF and part authority after adding the machine-readable
J2-J10 through-hole assembly contract. The new broad design-rule digest changes
only the assembly ownership/order contract: it names the required JLCPCB
wave/manual process, exact connector denominator and uploader stop condition.
It changes no component, value, pin, electrical net, truth-table word, rating
or schematic geometry. Fresh checks remain 32/32 electrical invariants,
21/21 labels, 131/131 pin-map assertions, 29/29 component parity and zero ERC
errors. P0/P1/P2 schematic defects remain 0/0/0; **SOUND / DO-NOT-ORDER**.

The `770ac064` renewal replaces no design fact: it binds the STM32 dossier to
official local ST DS13866 Rev 5 and renames the retained historical byte copy
to its correct Rev 3 identity. I independently reopened both PDFs. Rev 5
confirms the consumed TSSOP-20 pin sequence, PA13/PA14 SWD roles, 2.0-3.6 V
supply, BOR4 rising 2.80-3.00 V/falling 2.70-2.90 V, HSI48 -1/+1% at
0-85 C and -2.5/+2% full-temperature, and 6.5 x 4.4 mm 0.65-mm-pitch package.
Fresh exact checks remain 32/32 invariants, 21/21 labels, 131/131 pin maps,
29/29 components and zero ERC errors. No schematic topology or rating changes;
P0/P1/P2 schematic defects remain 0/0/0. **SOUND / DO-NOT-ORDER**.

The `3ecf08ab` renewal closes V5-F2 in the findings ledger using the same exact
official Rev 5 evidence independently checked above. Its remaining source delta
is changelog/research cleanup only. Part and broad design-rule hashes,
schematic, normalized netlist and PDF are unchanged from `770ac064`. A fresh
exact export still passes 32/32 invariants, 21/21 labels, 131/131 pin maps and
zero-discrepancy PCB parity over 22 nets; ERC errors remain zero. P0/P1/P2
schematic defects remain 0/0/0; **SOUND / DO-NOT-ORDER**.

The `4cf5c818` renewal changes only J11's dossier-level mating-role vocabulary:
the board-side FTSH male header is now schema-valid `plug`, while the note
retains its keyed 1.27-mm FFSD-family cable-receptacle relationship. P-ESC
passes 13/13. The schematic, normalized netlist, PDF, component identity,
J11 pin map and adopted design rules are unchanged. No topology, rating or
readability conclusion changes; P0/P1/P2 schematic defects remain 0/0/0.
**SOUND / DO-NOT-ORDER**.
