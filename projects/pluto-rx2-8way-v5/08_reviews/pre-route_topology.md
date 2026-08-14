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
parts_sha256: 879aa0b01010b253ad07989de128d0035d4cf4a01266eaa37b18b21a27dc1ce8
design_rules_sha256: 442edd6040f0b990f94a76f0f21d702503c0ba365fe6c5464d55f1842ab6999e
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
