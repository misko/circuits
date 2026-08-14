review_kind: redteam_topology
subject: Pluto RX2 8-Way v5 seal-final exact topology, protection and order review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5 topology/protection lens)
independence: independent-from-design-author
source_commit: 6d1d01cabb06301646136c6f729a027d8235160e
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
via_process_verdict: PASS
assembly_contract_verdict: PASS
p0_findings: 0
p1_design_findings: 0
p1_order_controls: 4
p2_findings: 2

# Seal-final adversarial topology, protection and order review

## Verdict and exact boundary

The exact schematic and saved PCB are **SOUND** and byte-identical to source
commit `6d1d01ca`. I found no P0 or P1 electrical, protection, ratings or PCB-
topology defect. The one-of-eight receive selector, reset-safe state word,
power-only USB-C sink, fused/transient-protected regulator and keyed SWD
interface agree between contracts, exact netlist and saved board.

The order verdict remains **DO-NOT-ORDER**. The machine-readable J2-J10
through-hole ownership correction closes the nine paste-free-THT-on-SMT-CPL
findings, but final population paperwork, current-source evidence, firmware,
fabrication package and actual JLC uploader confirmations remain open.

## Independent exact-artifact evidence

- Fresh schematic export passes 32/32 electrical invariants, 21/21 labels and
  131/131 pin-map assertions. Exact schematic/PCB parity is zero-discrepancy
  over 22 nets, 131 connected nodes and 24 intentional no-connects.
- Fresh DRC reports zero violations, zero unconnected pads, zero footprint
  errors and zero parity findings. Error-only ERC has zero errors. Manifest,
  Circuit JSON, schematic and retained netlist agree over 29/29 components.
- Both surge paths, both effective-capacitance banks and the 3V3 power topology
  pass. The LDO has 1.409 V minimum headroom versus 250 mV dropout and about
  45 mW worst-case dissipation versus the adopted 238 mW ceiling.
- Rules audit passes 20/20. Applicable placement, inter-footprint pad/paste and
  body-model gates pass; all 29/29 fitted footprints resolve a body.
- All nine RF nets remain single, stub-free 0.295 mm F.Cu paths with zero RF
  vias. The route-following fence passes 18/18 flanks, worst 1.3979 mm versus
  the 1.4000 mm limit. The board embeds the intended four-layer 1.6 mm
  controlled-impedance stackup and ENIG finish.
- Via-process grading covers 638/638 vias and 9/9 via-in-pad sites: nine U1
  0.45/0.25 mm vias are filled/capped; 629 ordinary 0.45/0.20 mm vias are
  untreated; drill families are disjoint; no site is partial; and the exact
  selective-process order remark is complete. Final-chain-to-board comparison
  finds zero new via-in-pad.

## Population and through-hole contract

The revised `assembly.yaml` now explicitly names J2-J10, the required JLCPCB
wave/manual through-hole process, supporting catalog/FAQ evidence and a hard
stop if the uploader does not accept exact C429844. A fresh A-POP run confirms:

- H1-H4 and FID1-FID3 are covered by declared exempt prefixes;
- the board has 36 footprints, the CPL has 29 intended placements, and there
  are no unexplained population-set differences;
- all 29 CPL rows agree with pad-array centres, worst 0.00050 mm at J1; and
- all nine prior `CPL-NOT-SMT-PLACEABLE` findings are closed by the exact
  machine-readable `through_hole` denominator and evidence.

A-POP now reports one finding only: no final release MANIFEST exists with the
generated `not_assembled:` line. That is a release-paperwork blocker, not an
assembly-contract or board-topology defect. Actual JLC acceptance and allocation
remain order-time evidence; the authored stop condition correctly forbids a
silent connector drop.

## End-to-end trace

`J2.1 -> RF_COMMON -> U1.22/RFC`; J3-J10 centres connect in order to U1
RF1-RF8. SMA shells, required U1 grounds and exposed pad 25 are GND; U1.20 is
allowed NC. LS is hard-low; PA0-PA3 own V1-V4. R3 high plus R4-R6 low produces
valid-power all-off `1000`. The supported boundary remains zero RF DC, 0 dBm
operator maximum and no guaranteed unpowered-U1 RF state.

J1 is sink-only and power-only. CC1/CC2 retain separate 5.1-kohm Rd paths
through U4; USB data/SBU pins are explicit no-connects. Power follows
`VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`. D1 cathode is on the protected
positive node and its anode is GND. The TVS is transient protection, not active
sustained-overvoltage cutoff, matching the approved boundary.

U2 supply, ground, reset, control and SWD pins agree with its dossier. J11 is
the keyed Cortex map with target-powered VTref; a Pi or ST-LINK must not source
the target. There is no Pluto power or live-control connection.

## Findings

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| V5-6D-RT-001 | Closed; no design defect | Connectivity, DRC, protection arithmetic, RF routing/fence, stackup and selective via process pass against exact artifacts. | Preserve the hashes; any design-artifact change invalidates this verdict. |
| V5-6D-RT-002 | Closed contract / P1 release-paperwork blocker | Machine-readable J2-J10 through-hole ownership closes all nine SMT-process findings. A-POP has only the absent final MANIFEST `not_assembled:` line. | Generate final BOM/CPL/MANIFEST and rerun A-POP on the staged release. Obtain uploader acceptance of exact C429844 wave/manual assembly or stop and create the distinct hand-solder release. |
| V5-6D-RT-003 | P1 evidence/freeze blocker | The locally retained STM32 document predates current ST DS13866 Rev 5. Manufacturer Samtec lands differ from JLC C2932107 CAD, and SMA drills differ by 0.10 mm from JLC C429844 CAD. | Capture/recheck current ST Rev 5; preserve manufacturer lands and obtain explicit JLC DFM acceptance. |
| V5-6D-RT-004 | P1 fab/release/order blocker | No sealed Gerber/drill/BOM/CPL package, exact-Gerber RF review, MANIFEST, same-day stock result, uploader allocation echo or order preview exists. | Generate and review the exact package; confirm JLC04161H-7628 impedance, selective 0.25 mm fill/cap processing, part allocation, orientation and THT execution before payment. |
| V5-6D-RT-005 | P1 firmware/functional blocker | `05_firmware` has generated profile consumers but no STM32 application, reproducible build, tests or binary; no article has timing, power, thermal or RF evidence. | Implement/build/test/flash firmware and decoder, then complete first-article timing, rail, thermal and all-path VNA tests. |
| V5-6D-RT-006 | P2 accepted interface risk | U1 all-off requires valid VDD; SMA centres have no DC blocks, RF limiter or system-level IEC ESD network. | Preserve zero-DC, 0 dBm and controlled-ESD limits; redesign if the interface requirement expands. |
| V5-6D-RT-007 | P2 process debt | Raw ERC retains 190 presentation/library warnings despite zero errors and independently exact connectivity. | Baseline and reduce producer noise later; never hide a new warning in the existing count. |

## Severity summary

- P0: 0.
- P1 electrical/protection/ratings/PCB-topology defects: 0.
- P1 order, evidence, release and functional controls: 4.
- P2 accepted interface/process risks: 2.

The board may proceed through the remaining seal and fabrication-package
work, but it is not ready to order and this verdict is not physical performance
evidence.
