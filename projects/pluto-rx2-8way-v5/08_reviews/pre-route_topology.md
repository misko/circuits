subject: Pluto RX2 8-Way v5 schematic topology after D18 bench-power input
date: 2026-08-14
reviewer: Codex exact-artifact topology and datasheet review
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
checkpoint_sha256: f8d17bb351beb74fe62add8c62ce0d30a3788b95235db34e50a6761515f6b3bf
circuit_json_sha256: bf7063ed5f5239afb2dc0b9785d1b82ce092a30b4687dd85d5abf62a34f064f9
kicad_schematic_path: 04_kicad/pluto_rx2_8way_v5.kicad_sch
kicad_schematic_sha256: a21b84984b934ee37d65d04976193df6f5ff2ac8747323c22397e003744c7b0f
schematic_pdf_sha256: eafe50122e048fde289ecfdc26dcf6e28a2bc27e6c5b232db9c9f0786da365c0
netlist_sha256: 72bea8142a167c10d90c2ad1f5a5cac519e564bbb16755808a1fcd2675200021
exact_netlist_sha256: dab68a6458c2f3070380a3c887e862a1d8277970fd8f159d498990decdfc94e0
parts_sha256: e275db04f5e06b63d92714a9bb6f3c609f447e41d74a042001161ed2cc9bf6cb
design_rules_sha256: 70af3e20c1338c9d83b96348de0f3193434e387c39241ba59cd28c73a8acfb79
authoring_source_sha256: d7780efb61bf5f3f1577aef4776a7f32484847a4fd121f88ebbbf11b07b52d73

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

The current-working-tree renewal reviews the regenerated pinned native KiCad
schematic after the converter began treating each TSX `schematic_sheet_id` as
its own coordinate space. The authored TSX, circuit JSON and four-page
tscircuit PDF remain byte-identical. A fresh native-netlist export has the same
canonical digest `817a6cea...` as the already reviewed netlist: 29/29 refdes
still agree with the manifest, 21/21 intended labels survive, all 131/131
label-to-pin assertions hold, and the independent native drawing check finds
zero places where two nets share conductor ink. Fresh ERC has zero errors; its
205 warnings are the known generated-library/off-grid presentation classes.
The coordinate-space repair is therefore geometric and topology-neutral.

The current part digest incorporates stronger `verified` citations in ten
dossiers. I reopened the retained exact manufacturer evidence and checked the
stated pages, sheets, figures and drawing revisions: the final citations are
supported, S-VER grades all 12 applicable dossiers, and P-ESC remains 13/13.
The current broad-rule digest adds the corrected RF-fab artifact name and
evidenced twin adjudications; neither changes a component, pin, net, value,
rating or state word. The pending `floorplan.yaml` changes move the
`USB-C POWER ONLY` silk caption and add `FUSE`; they require board replay and
board review, but do not alter this schematic verdict. P0/P1/P2 schematic
defects remain 0/0/0; **SOUND / DO-NOT-ORDER**.

The D18 renewal adds only J12 to the electrical topology: exact CJT
`A2541WV-2P` / LCSC `C225477`, pin 1 on `VBUS_RAW` and pin 2 on GND. I traced
both allowed source stacks independently:

```text
J1 VBUS -> VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3
J12.1  -> VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3
J12.2  -> GND
```

The new header does not bypass F1, the shunt TVS or the LDO. The important
limitation is explicit and accepted as a bench-use contract: J1 and J12 are
directly joined at `VBUS_RAW`, have no reverse isolation, and may not be
connected or energized together. The schematic page title, exact-part
dossier, power/protection rules and planned silk all repeat that rule. A
reverse-input mux or ideal-diode stage would be required to make simultaneous
or hot-plug use safe; it is not silently implied here.

Fresh generated evidence reports 30/30 component parity, 133/133 pin-map
assertions, 34/34 electrical invariants, 21/21 surviving labels and zero ERC
errors. The 4.75-5.5 V envelope, 20 mA design load, USB data no-connects,
independent CC resistors and RF/control topology are unchanged. P0/P1/P2
schematic defects remain 0/0/0; **SOUND / DO-NOT-ORDER** pending PCB replay,
route, assembly preview and first-article tests.

The strict-RF integration renewal changes only the RF process contract and
the already-connected RF centreline geometry: it adopts bounded
`rf-module-v1` context, a blocking 3W minimum-radius bend policy, and the
realized 1.10 mm fence band. It adds no schematic component, pin, net, value,
state word, or power path. I retraced the regenerated 30-component netlist:
the canonical netlist digest and all 34/34 electrical invariants remain
unchanged. P0/P1/P2 schematic-topology defects remain 0/0/0;
**SOUND / DO-NOT-ORDER** pending exact routed-board renewal.
