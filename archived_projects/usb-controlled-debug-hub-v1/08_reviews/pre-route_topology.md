# Pre-route topology review — USB Controlled Debug Hub v1

subject: usb-controlled-debug-hub-v1 corrected upstream delivery and USB topology
date: 2026-08-16
reviewer: independent topology/ratings agent (fresh exact-artifact topology re-review after upstream-protector repair)
context-given: exact current normalized KiCad netlist, TSX, part dossiers, brief, architecture, ADRs, adopted rules, machine reports, and bounded placement/routing delta
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
netlist_sha256: 3a03dd6c9d770c4d820ffb2b228f482adec3715ec350f65c07be13511b708662
parts_sha256: 737e094242d31f2989dca17f67f3e86c85a55bd023ef09eb2d01e04150149da2
design_rules_sha256: a07bbbdd824643533aaaed6c1f6184acffcee54d61eed61a54ed015f9e929fb6
raw_netlist_sha256: 0d3fbddb082f4e1772205914cc65cbb9c8241c96a6e5152c5e32c68bb4e53087
tsx_sha256: 595bc3d60fc781ae08d1de825c273f23db3a66a9261904425baf251da3176590
power_tree_sha256: ae34fda05059d3e73ec18ae3ae0f302b616febdf2c7cf36c59d2b0397b049cd0
brief_sha256: ff472db8015c293c5ad004a8076697396cdf0befa858d016af9f73d6a2a13063
architecture_sha256: 9dce11f55c04b7cadf5e396db224eab49131d643b8ddea7c4ddfd8eb811c03f7
adr_0002_sha256: ed4f971f9b5f9ede07b144cc63f2d726049c671b64fd3aed35401d1115f8f05a
adr_0006_sha256: 882808e5d1c18647d766e97433dd42de8c6885a7863631bfa1b4e7d11d247a9b
adr_0007_sha256: 91fab92fc29ad2c0c358b759c547e20121ebbbaf06f0083c89a15983ed6d5287

## Findings

- P0: none. The prior protected-trunk-floor defect is closed.
- P1: none. The corrected F.Cu `UP_HUB_P` dogleg remains below J_UP.4/GND and
  J_UP.1/VBUS until x=35.5, then rises to the right of both lands with the
  required deterministic-launch clearance.
- P2: none. ADR 0006's explanatory narrative now matches its machine-checkable
  obligations and the exact repaired design: upstream bottom-side 90 degrees,
  `IO1=D-`, `IO2=D+`, signal bank toward J_UP, and GND behind it.

## Bounded geometry-delta recheck

The repair keeps bottom-side `U_ESD_UP` at rotation 90 degrees and, in the
latest bounded clearance delta, translates it from `[33.2, 54.0]` to
`[33.2, 52.85]`.  The original repair reverses its
rotation from 270 to 90 degrees, exchanges the two equivalent shunt-channel
assignments, and updates the deterministic short B.Cu branches accordingly.
The exact result is coherent:

- `J_UP.2/D_MINUS`, `U_ESD_UP.1/IO1`, and `U_HUB.58/UP_DM` are exactly
  `UP_HUB_N`; `J_UP.3/D_PLUS`, `U_ESD_UP.2/IO2`, and `U_HUB.59/UP_DP` are
  exactly `UP_HUB_P`; `U_ESD_UP.3` remains GND;
- the part dossier and Nexperia topology identify IO1 and IO2 as equivalent
  bidirectional shunt channels, so exchanging their per-instance assignment
  is electrically neutral and is now explicitly bound by TSX and E-INV;
- at bottom-side 90 degrees, pad 1 now realizes at `[34.15, 53.7875]` and pad
  2 at `[32.25, 53.7875]`, directly behind the matching J_UP D- land at
  `[34.20, 55.75]` and D+ land at `[32.20, 55.75]`; the two 1.963 mm branches
  are parallel, via-free, do not cross, and remain on their named nets.  The
  1.9625 mm center separation also leaves approximately 0.8125 mm copper-edge
  clearance between the 1.7 mm connector lands and 0.6 mm ESD-pad dimension,
  closing the prior same-net pad overlap;
- ground pad 3 now realizes at `[33.20, 51.9125]`, behind the signal bank
  rather than between it and the connector.  Pads 1/2 are 1.9625 mm from the
  J_UP signal-row centroid while pad 3 is 3.8375 mm away, satisfying the
  explicit `pad_bank_faces` margin and remaining inside the stated 2 mm
  connector-to-protection signal-land budget; and
- no power-tree, part selection, protection rating, hub configuration, or
  downstream-port topology changed.  The exact rules, TSX, normalized
  netlist, and raw-netlist identities changed as expected and are rebound by
  this receipt.

The final bounded route-seed delta changes only the F.Cu `UP_HUB_P` fanout
after J_UP.3: `[32.2,55.75] -> [31.0,56.95] -> [31.0,59.55] ->
[35.5,59.55] -> [36.5,57.6916] -> [37.0,57.6916]`.  Net ownership, ESD
placement, shunt assignment, and the final coupled handoff remain correct.
Against each 1.7 mm J_UP power land and the 0.2332 mm route width, the x=31.0
vertical retains about 0.233 mm copper-edge clearance from J_UP.4, the
y=59.55 horizontal retains about 0.333 mm from both power-pad lower edges,
and the rising segment's closest centerline approach to J_UP.1's lower-right
corner is about 0.609 mm (about 0.493 mm after half trace width).  All exceed
the exact deterministic-launch 0.15 mm clearance, so neither different-net
power pad is crossed or approached illegally.

E-INV independently passes all 82/82 exact assertions and the early-design
gate passes 5/5 families.  Placement clearance, realized copper, impedance,
skew, and DRC remain owned by their later exact-board gates.  The repaired
protector topology and its authored connector fanout are SOUND.

## P0 re-review — source to mated USB-A plug

The revised proof no longer assumes `P5V_PROTECTED=4.89 V`. It derives the
shared floor from the commissioned 5.20 V minimum at `P5V_RAW`:

```text
fixed fuse allowance                         121.000 mV
(45 + 18) mOhm x 2.58 A                      162.540 mV
nominal admitted shared drop                 283.540 mV
shared drop charged by 5%                    297.717 mV
5.200 V - 0.297717 V                       = 4.902283 V
declared P5V_PROTECTED floor               = 4.890000 V
additional floor reserve                      12.283 mV
```

This is conservative and non-circular for a first-article design:

- The fuse's 121 mV figure is a published typical rated-current drop rather
  than a guaranteed maximum. The rules label it `engineering_bound`, not
  `manufacturer_maximum`, and charge the full 4 A rated-current drop unchanged
  at the lower 2.58 A board load. The exact fuse dossier also requires
  first-article thermal/drop testing; the figure is not presented as a
  production-lot guarantee.
- TPS259474L contributes 45 mOhm from the manufacturer's maximum RON, applied
  at the complete 2.58 A shared current.
- The holder plus common-input copper contributes an explicit 18 mOhm
  `budgeted_max`, not a hidden zero. Its evidence requires hot four-wire
  first-article qualification. The 5% charge applies to the complete shared
  loss stack, and the declared floor retains another 12.283 mV below the
  calculated result.
- The four branch calculations start from the proven conservative 4.89 V
  floor. Each branch then charges 35 mOhm TPS2557 maximum RON, 25 mOhm
  PCB/via/joint budget, and 100 mOhm mated-contact budget at 0.5 A: 80 mV
  physical drop, 96 mV after the independent 20% branch margin. The available
  140 mV headroom leaves 44 mV after that charged branch loss.
- U_AGG is correctly absent from the individual 0.5 A branch series-device
  list because its loss is already charged once, at total trunk current, in
  the shared proof. It has not been omitted or double-counted.

`E-MARGIN` independently reproduces a 4.902 V shared derived floor and passes
the declared 4.890 V floor, then passes all four external rails. The 18 mOhm
input allocation, 25 mOhm branch-copper allocation, 100 mOhm exact mated-
contact allocation, exact fuse behavior, and hot voltage remain first-article
measurements. They are order holds, not unevidenced schematic assumptions;
accordingly this design verdict is SOUND while the order verdict remains
DO-NOT-ORDER.

## USB-B, protection, and hub configuration

The exact netlist retains the previously verified topology:

- `J_UP.2/D_MINUS`, `U_ESD_UP.1/IO1`, and `U_HUB.58/USBUP_DM` share
  `UP_HUB_N`; `J_UP.3/D_PLUS`, `U_ESD_UP.2/IO2`, and
  `U_HUB.59/USBUP_DP` share `UP_HUB_P`; `U_ESD_UP.3` is GND.
- PESD2USB3UX IO1 and IO2 are equivalent bidirectional shunt channels. Their
  deliberate upstream assignment preserves physical D-/D+ land order without
  changing logical polarity or introducing a series split.
- `J_UP.1` reaches only `USB_UP_VBUS` and the 100 kOhm/100 kOhm VBUS-detect
  divider. It has no path to the self-powered 5 V trunk.
- `CFG_SEL[2:0]=000` selects the USB2517I internal defaults with straps
  enabled. Internal default register 06h is `0x9B`: self-powered, High-Speed,
  Multi-TT, individual over-current sensing, and individual port power.
- `PRT_SWP1` is high, intentionally assigning management D+ to physical
  `DN1_DM` and D- to physical `DN1_DP`. `PRT_SWP2..5` are low, preserving
  normal external DM=D- and DP=D+ polarity.
- `01_docs/ARCHITECTURE.md` now correctly states that physical ports 2–5 keep
  their swap straps low. The stale opposite statement from the prior review is
  gone.
- Each symmetric FSUSB42 path carries D- through pins 7-to-3 and D+ through
  pins 6-to-4 with SEL low and HSD2 unconnected. `NON_REM[1:0]=01` declares
  physical port 1 non-removable; both data pins of ports 6 and 7 have the
  documented disable pull-ups.

No EEPROM image, board firmware, or runtime port-swap programming is required.

## Remaining power, protection, and control topology

- Power is `P5V_RAW -> F_IN -> P5V_FUSED -> U_AGG -> P5V_PROTECTED`; all five
  TPS2557 inputs and AP63203Q are downstream. U_AGG retains the reviewed ILM,
  ITIMER, dV/dt, input-bypass, UVLO, and OVLO support network.
- The protected-trunk capacitor proof remains 128.664 uF effective against the
  120 uF USB hub-source requirement.
- Each external TPS2557 receives `HUB_PRTPWRn AND PWR_CMDn`, has the reviewed
  165 kOhm ILIM setting, and reports its active-low open-drain fault directly
  to the matching hub OCS pin. The current-limit window is 0.535–0.794 A.
- Each FSUSB42 connects only when `DATA_CMDn AND PWR_ENn` drives its open-drain
  OE inverter. External pull resistors make reset/unpowered states fail with
  VBUS off and data disconnected.
- MCP2221A and MCP23017 share switched `VBUS_CTRL`; I2C pull-ups remain on that
  5 V island, while the 3.3 V 74LVC08 inputs are 5.5 V tolerant. MCP23017's
  reset-input defaults and the external command pull-downs preserve safety.
- AP63203Q and USB2517I support networks retain their reviewed values and
  topology.

## Machine evidence

- `E-MARGIN`: 5/5 graded rows pass — one shared delivery proof plus four
  external-port branches.
- `E-TOPO`: 6/6 rails pass and cover 1/1 converter dossier.
- Early design: 5/5 families pass, including 4/4 external path claims,
  128.664/120 uF effective source capacitance, and the aggregate fault/timer/
  startup envelope.
- `E-INV`: 82/82 exact netlist assertions pass.
- `E-ADR`: 4/4 topology/protection ADRs emit assertions.
- `S-NETMERGE`: 103/103 labels survive export.
- `S-COUNT`: 4/4 representations agree over 139 references.
- ERC: 0 error-severity violations.

## Boundary

This receipt permits continuation to the schematic-readability checkpoint and
then placement/routing only if the separate exact-PDF review is also SOUND and
current. It does not approve placement, connector orientation, routed copper,
USB impedance/skew, thermal realization, fabrication payloads, ordering, or
production. First-article hot four-wire input/branch measurements, connector-
lot qualification, simultaneous four-port voltage tests, exact-source 5 A / 6
ms transient qualification, and USB compliance remain mandatory.
