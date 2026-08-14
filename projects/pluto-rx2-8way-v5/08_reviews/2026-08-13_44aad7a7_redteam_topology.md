review_kind: redteam_topology
subject: Pluto RX2 8-Way v5 final exact schematic and PCB topology
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5 topology/protection lens)
independence: independent-from-design-author
context-given: full-tree
source_commit: 44aad7a7a7fe8e4102987c811ef137768656dec2
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
board_sha256: 0b8ab1962ef798e77eb29f09bcc809695d092e130c627cd2fd5b535e3a1aea41
netlist_sha256: 17f2724216be5597a3c518c7078293532300cf2af8145e247b39b270674bdefc
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Final adversarial topology, protection and exact-board review

## Verdict and boundary

The exact schematic and saved PCB identified above are **SOUND**. I found no
P0 or P1 electrical/topology defect: the saved board implements the approved
one-of-eight receive selector, reset-safe control word, power-only USB-C
source, protection path and keyed SWD interface without a schematic-to-board
connectivity discrepancy. The verdict binds both artifacts to the stated
source commit; each artifact is byte-identical to that commit.

The order verdict is **DO-NOT-ORDER**. Population/process declarations,
firmware, evidence lifecycle, final fabrication/release artifacts and actual
JLC uploader confirmations remain open. These controls do not make the routed
copper topology defective, but they do prevent treating this review as an
order or functional-acceptance authorization.

## Independent exact-artifact evidence

- A new KiCad netlist export from the sealed schematic passes 32/32 electrical
  invariants. Independent schematic-to-saved-PCB parity covers 22/22 nets,
  131/131 connected physical nodes and 24/24 intentional no-connects with zero
  real discrepancies.
- Fresh KiCad PCB DRC reports 0 violations, 0 unconnected items and 0 footprint
  errors. Fresh error-severity ERC reports 0 errors. The all-severity ERC
  baseline contains 190 warnings: 99 synthetic-library-context, 89 off-grid
  geometry and two unconnected-wire-endpoint presentation warnings; none
  changes the independently exported connectivity above.
- Manifest, Circuit JSON, schematic and retained netlist agree over the same
  29/29 populated refdes. The saved board contains all 22 functional nets with
  copper or a pour. Every RF net is one connected F.Cu path at 0.295 mm with
  zero RF vias; there are no RF stubs, layer swaps or parallel schematic
  branches.
- Early power/protection grading passes 4/4: both surge paths are coordinated
  to the declared operating boundary, and the LDO input/output banks each
  retain 1.798 uF effective against a 1 uF minimum. Power topology passes 1/1
  rail: 1.409 V minimum headroom versus 250 mV dropout and 44.8 mW worst-case
  dissipation versus the adopted 238 mW board-dependent ceiling.
- Saved-board rules pass 20/20. Placement gates pass with no findings;
  different-footprint pad/paste separation passes over 167 copper pads; all
  29/29 fitted footprints resolve a 3D body. A fresh placement-policy run on a
  disposable copy passes all four measurable manufacturer keep-short budgets,
  with the tightest U3.5-to-C2.1 span 1.88 mm against 2.5 mm.
- The route-following GND-fence check grades 18/18 RF flanks. Its worst saved
  aperture is 1.3979 mm on RF_ANT8-R against the 1.4000 mm maximum. This result
  credits the exact route and package/connector-owned endpoint structures,
  not the unrelated 5 mm whole-board stitch lattice.
- Imported Pluto cable-boundary facts pass 3/3 provenance checks. The board
  consumes no Pluto dimensions: only SMA mating, operator port identification
  and the receiver absolute-maximum boundary cross the cable interface.
- The current top-copper and 3D renders show nine outward-facing exact-code SMA
  jacks, accessible USB-C and keyed SWD connectors, all 29 fitted bodies, four
  mounting holes and unobstructed connector mating directions. Visual evidence
  is supporting evidence only; pad/net identity comes from the saved board.

## End-to-end topology trace

### Receive-only RF path and state control

`J2.1/RF_COMMON` connects only to U1.22/RFC. J3.1 through J10.1 connect in
order to U1 RF1 through RF8 on pins 24, 2, 4, 6, 13, 15, 17 and 19. Every
J2-J10 ground leg and every specified U1 ground pin, including exposed pad 25,
is on GND; U1.20 remains an allowed no-connect. This is one PE42482A-X
absorptive SP8T, not a splitter or switch tree.

U1.1/LS is hard-low. U2 PA0-PA3, physical pins 7-10, connect in order to U1
V1-V4. R3 pulls V4 high and R4-R6 pull V1-V3 low, so reset/tri-state requests
`V4..V1=1000`, the manufacturer's terminated all-off state, while U1 VDD is
inside 2.3-5.5 V. The approved ANT1-ANT8 words independently reproduce the
PE42482 truth table. The control contract preloads 1000 before enabling GPIO,
uses one atomic approved word and inserts a 5 ms all-off guard; U1's maximum
settling specification is 1.4 us.

The exact RF nets contain no source of intentional DC and no DC-blocking
capacitors. Operation therefore remains conditional on 0 VDC at every SMA
centre. The selector itself is specified over 10 MHz-8 GHz, while the assembled
100 MHz-5.9 GHz loss, balance, isolation and return-loss targets remain
first-article measurements. User-accepted operation of physical AD9363 silicon
outside its official range is not converted into an ADI guarantee here.

### USB-C input, regulation and protection

J1 is a sink-only, power-only receptacle. All four VBUS contacts join
`VBUS_RAW`; all GND contacts and shell stakes join GND. CC1 and CC2 remain
separate through U4 IO1/IO2 to their own 5.1 kohm Rd resistors. D+/D-/SBU are
explicit no-connects, so the board has no USB data or PD path.

The complete supply chain is `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`.
D1 pad 1/cathode shunts from `VBUS_PROTECTED` to pad 2/anode at GND, so it does
not forward-clamp normal VBUS. U3 IN and EN are on the protected node, GND is
ground, NC is open and OUT is 3V3. C1/C2 are the required input/output banks;
C3-C5 provide rail bulk/local bypass and C6 returns NRST to ground. The board
has no external power output or Pluto backfeed path and de-energizes by
unplugging USB-C. The TVS is transient protection, not sustained-overvoltage
cutoff, matching the user-approved boundary.

### Controller and programming interface

U2 VDD/VDDA and VSS/VSSA are on 3V3/GND; PA0-PA3 own only the four switch
controls. J11 implements the keyed Cortex 10-pin mapping: pin 1 is target
VTref/3V3 sense, pins 2/4 are SWDIO/SWCLK, pins 3/5/9 are GND and pin 10 is
NRST; pins 6/7/8 are explicit no-connects. A Pi or ST-LINK must sense the
self-powered target and must not source J11.1. There is no live configuration
or data connection to the Pluto.

## Findings

| ID | Severity | Finding and evidence | Required disposition |
|---|---|---|---|
| V5-RT-TOP-001 | Closed; no defect | Exact schematic-to-board parity is zero-discrepancy over 22 nets/131 connected nodes/24 no-connects; DRC is 0/0 and the required RF, power, protection, control and SWD paths agree with the exact part dossiers. | Accept the final routed topology as SOUND. Any schematic, footprint, pad-net or routed-connectivity change invalidates this hash-bound review. |
| V5-RT-TOP-002 | P1 order/process blocker; not a topology defect | A fresh A-POP run against the exact board and current pre-route BOM/CPL fails 11 findings. H1-H4 are absent from the CPL but the declared exempt prefix is `MH`, not `H`; the release manifest has no generated `not_assembled` line. J2-J10 are through-hole parts on an SMT CPL with no paste, while `assembly.yaml` describes wave solder only in prose rather than the gate's machine-readable THT process declaration. | Before any order, make the population/process contract machine-readable, regenerate the final BOM/CPL/MANIFEST and rerun A-POP. Either obtain documented JLC THT/wave execution for J2-J10 or remove them from the SMT placement set and control their hand installation. |
| V5-RT-TOP-003 | P1 evidence/freeze blocker; not a topology defect | The findings ledger still requires a local current ST DS13866 Rev 5 capture. Current pin facts were cross-checked online, but the retained local file identifies an older revision. Exact Samtec lands differ materially from JLC generic CAD, and the Amphenol manufacturer drills differ by 0.10 mm from JLC catalog CAD. | Capture/recheck current ST evidence before design freeze. At order time preserve the manufacturer J11 and SMA lands and obtain explicit JLC DFM/assembly confirmation; a vendor-requested geometry change requires new artifacts and reviews. |
| V5-RT-TOP-004 | P1 order/release blocker; not a topology defect | There is no final sealed fabrication package, final BOM/CPL, stackup/order document, MANIFEST, uploader preview/allocation echo or exact-Gerber RF fabrication review. The KiCad board also carries no embedded dielectric stackup block, so the JLC04161H-7628 build and controlled impedance must be conveyed and echoed by the release/order artifacts. | Generate and independently review the exact final fab package, select four-layer 1.6 mm JLC04161H-7628 plus controlled impedance, confirm U1 filled/capped via-in-pad processing, and complete the release/seal gates before payment. |
| V5-RT-TOP-005 | P1 functional/bring-up blocker; not a PCB-topology defect | `05_firmware` contains the generated profile header/decoder JSON and programming instructions but no STM32 application source, build output or host tests. No article has demonstrated BOR/watchdog recovery, atomic state writes, unique dwells, Pi SWD attachment, rail behavior, thermal behavior or RF performance. | Implement/build/test/flash the firmware and decoder, then complete first-article programming, logic-analyzer, power, thermal and all-path VNA acceptance before functional or production approval. |
| V5-RT-TOP-006 | P2 accepted interface risk | U1's all-off guarantee ends below 2.3 V VDD. The nine SMA centres have no system-level IEC ESD or receiver-overdrive limiter, and no RF DC blocks. The declared scope is 0 VDC, 0 dBm normal operator limit, controlled ESD handling and no guaranteed RF state for an unpowered U1. | Preserve these limits in operating/test documentation. Any requirement for bias tees, powered antennas, hot-plug ESD immunity, high-power survival or guaranteed power-off isolation requires a protection/interface redesign. |
| V5-RT-TOP-007 | P2 process debt | Raw ERC remains noisy at 190 warnings despite zero errors and exact connectivity parity. The warning floor makes future genuinely new presentation/connectivity warnings harder to notice. | Retain the exact warning baseline for this artifact and improve the schematic producer/library/grid presentation before a later design; do not suppress a new warning merely because this baseline is large. |

## Severity summary

- P0: 0.
- P1 electrical/topology design defects: 0.
- P1 order, evidence, release and functional-qualification controls: 4.
- P2 accepted interface/process risks: 2.

The board is suitable to advance into fabrication-package generation and the
remaining independent reviews. It is not ready to order, and no physical or
production performance claim follows from this topology verdict.
