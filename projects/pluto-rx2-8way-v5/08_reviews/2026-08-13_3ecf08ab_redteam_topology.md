review_kind: redteam_topology
subject: Pluto RX2 8-Way v5 final authoritative topology, protection and order review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5 topology/protection lens)
independence: independent-from-design-author
source_commit: 3ecf08abe5f44c098144abfc8cea31fc89354c59
schematic_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
stm32_rev5_sha256: e392b1542086b25f6bcb8856b6c0467aa3ec10e31f03bdafca74796485c531fe
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
evidence_lifecycle_verdict: PASS
via_process_verdict: PASS
assembly_contract_verdict: PASS
project_state_verdict: DRAFT
p0_findings: 0
p1_design_findings: 0
p1_maturity_order_controls: 4
p2_findings: 2

# Final authoritative adversarial topology, protection and order review

## Verdict and boundary

The exact schematic and PCB are **SOUND**, byte-identical to commit
`3ecf08ab`, with no P0/P1 electrical, protection, rating or routed-topology
defect. Official local ST Rev 5 is correctly bound and V5-F2 is now accurately
closed in the findings ledger.

The order verdict remains **DO-NOT-ORDER**. `project_state.py --no-write`
derives `DRAFT`: V5-firmware and V5-placement-and-routing remain pending at
the DESIGN_CLEAN maturity boundary. Final population/release evidence and
actual JLC uploader/DFM interpretation are also absent.

## Independent evidence

- Official local Rev 5 confirms U2's TSSOP-20 pin sequence, PA13/PA14 SWD,
  2.0-3.6 V supply, BOR4 2.80-3.00 V rising/2.70-2.90 V falling, HSI48 bounds
  and 6.5 x 4.4 mm 0.65-mm-pitch package. The Rev 3 comparison shows no
  consumed-fact change.
- Fresh exact export passes 32/32 invariants, 21/21 labels and 131/131 pin
  maps. Schematic/PCB parity is zero-discrepancy over 22 nets, 131 nodes and
  24 no-connects; component parity is 29/29.
- Fresh DRC is zero violations/unconnected/footprint/parity findings. ERC has
  zero errors. Both surge paths, capacitance banks and the 3V3 rail pass;
  LDO headroom is 1.409 V versus 250 mV dropout and dissipation about 45 mW
  versus the adopted 238 mW ceiling.
- Rules pass 20/20; placement, pad/paste separation and 29/29 body coverage
  pass. All nine RF routes are stub-free 0.295 mm F.Cu with zero RF vias;
  fence coverage is 18/18, worst 1.3979 mm versus 1.4000 mm.
- Via grading covers 638/638: nine U1 0.45/0.25 mm filled/capped sites and
  629 untreated ordinary 0.45/0.20 mm vias, with disjoint drill families and
  zero new post-route via-in-pad.

## Population and topology trace

The J2-J10 machine-readable THT contract passes. A-POP recognizes all nine
refs, all H/FID exemptions and 29 placement datums (worst 0.00050 mm at J1),
with no unexplained population delta. Its sole finding is the absent final
MANIFEST `not_assembled:` line. Uploader acceptance of exact C429844 wave/
manual assembly remains mandatory.

RF is `J2.1 -> RF_COMMON -> U1.22` and J3-J10 centres -> RF1-RF8. Shells,
required U1 grounds and pad 25 are GND; U1.20 is NC. LS low plus R3 high and
R4-R6 low makes valid-power all-off `1000`. RF remains zero-DC and 0 dBm.

J1 is a power-only sink with independent CC Rd paths and data/SBU no-connects.
Power is `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`; D1 cathode is on the
protected-positive node and anode on GND. J11 is target-powered keyed Cortex
SWD and must not back-power the board.

## Findings

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| V5-3E-RT-001 | Closed; no design defect | Connectivity, protection arithmetic, RF routing/fence, stackup, via process and source evidence are green. | Preserve hashes; design-artifact changes require renewal. |
| V5-3E-RT-002 | P1 maturity control | Project state remains DRAFT because V5-placement-and-routing is still pending at DESIGN_CLEAN, even though exact final lenses are being completed. | Close the gate only after its objective exact-review/checkpoint condition is satisfied and recorded. |
| V5-3E-RT-003 | P1 population/order control | THT ownership passes, but the final MANIFEST line and JLC acceptance of C429844 wave/manual assembly do not exist. | Generate final BOM/CPL/MANIFEST, rerun A-POP, require uploader acceptance or stop for the distinct hand-solder release. |
| V5-3E-RT-004 | P1 fab/release/order control | No sealed fab package, exact-Gerber RF review, same-day stock, uploader echo or order preview exists; connector land/drill deltas still need DFM acceptance. | Generate/review the package and confirm stackup, impedance, fill/cap, allocation, geometry, orientation and assembly process. |
| V5-3E-RT-005 | P1 firmware/functional control | V5-firmware is pending; no application source, reproducible build, tests/binary or first-article timing/power/thermal/RF proof exists. | Implement/build/test/flash and complete first-article qualification. |
| V5-3E-RT-006 | P2 accepted interface risk | U1 all-off requires valid VDD; SMA centres lack DC blocks, limiter and system-level IEC ESD. | Preserve zero-DC, 0 dBm and controlled-ESD limits; redesign if scope expands. |
| V5-3E-RT-007 | P2 process debt | Raw ERC retains 190 presentation/library warnings despite exact connectivity and zero errors. | Reduce producer noise later; never hide a new warning in the baseline. |

## Severity summary

- P0: 0.
- P1 electrical/protection/rating/PCB-topology defects: 0.
- P1 maturity, order, release and functional controls: 4.
- P2 accepted interface/process risks: 2.

The design remains SOUND but is not order-ready or physically qualified.
