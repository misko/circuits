subject: pluto-rx2-8way-v4 v1.1 exact release source
date: 2026-08-01
reviewer: redteam-agent (GPT-5 topology/protection lens)
independence: independent-from-design-author
context-given: full-tree
review_kind: redteam_topology
source_commit: bc1fb1003cd9b7f06c70b15d973c5c018d0ff458
board_sha256: 72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7
design_verdict: SOUND
order_verdict: ORDER

# Fresh adversarial topology and protection review

## Verdict

The exact v1.1 board and schematic are **SOUND**. I found no open P0 or P1
topology, power, protection, pin-use, or ratings defect. Catalog evidence is
clear for all 11 placed BOM lines, so the review contract's independent
orderability verdict is **ORDER**. Uploader/service-selection checks remain
mandatory buyer actions, and first-article tests remain production/service
acceptance; neither is circularly treated as evidence that an otherwise
buyable design cannot be ordered.

## Independent evidence

- Fresh KiCad DRC against a clean release-local source tree reports zero
  geometric violations, zero unconnected items, and zero schematic-parity
  discrepancies.
- The release netlist passes **25/25** electrical invariants. Critical facts
  re-derived there include `3V3_MOD -> FB_3V3 -> 3V3`, U_SW VDD and C_BULK on
  the filtered side, two separate 220-ohm tap resistors, all four 100-ohm
  control series resistors, all four switch-side 10-kohm pull-downs, LS/NC/EP
  grounding, and the RF1/RF8/RFC assignments.
- Power grading passes 1/1 rail: the RP2040-Zero module's linear 3.3-V source
  has 1384 mV minimum input headroom versus 250 mV declared dropout, 252 mW
  worst-case dissipation versus 400 mW, and 934 mV load-brownout headroom
  after the conservative 12 mV delivery drop. De-energization by unplugging
  USB is correctly N-A for a stored-energy/off-control circuit.
- BOM and CPL contain 11 catalog lines and 27 top-side placements. The
  RP2040-Zero is intentionally user-fitted; it is not a bare RP2040 and is not
  an unexplained population omission. Assembly coverage is 32 board
  footprints / 27 CPL placements / 5 declared unpopulated, with zero gaps.
- The RF boundary is explicit and internally consistent: passive 50-ohm
  receive-only ports, +18 dBm CW maximum, 0 VDC in powered/unpowered/fault
  states, no bias tee/transmitter/active antenna, and ESD-controlled bench
  handling. Under that locked envelope, omitting broadband shunt ESD parts
  and DC blocks is a deliberate bandwidth/protection trade, not an unstated
  protection omission. Any wider deployment envelope requires a redesign.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| TOP-v1.1-01 | Closed / no defect | The switch defaults safely and deterministically: LS is grounded and V1..V4 have switch-side pull-downs; `0000` selects RF1 and the explicit V4 state can terminate all ports. | Accept. Firmware must preserve the documented truth-table mapping and settling interval. |
| TOP-v1.1-02 | P1 order-execution control, not a design/sourcing defect | Gerbers cannot prove that JLC will execute filled/capped 0.25/0.15-mm POFV, controlled impedance, or ten plug-in SMA joints, and the uploader preview is not present. | During order entry, select/confirm those services and confirm U_SW pin 1, LED cathode, SMA identities, stackup, POFV, and BOM resolution in the actual uploader. Stop only if the vendor rejects the authored process. |
| TOP-v1.1-03 | P1 production/service acceptance, not a pre-order defect | Actual RP2040-Zero fit/current/thermal behavior, rail ripple, SMA DC isolation, switching behavior, and RF loss/isolation/phase are not proven by CAD. | Complete the documented module-fit, electrical, firmware, X-ray, TDR, and VNA acceptance before service or production release. |

## Severity summary

- P0: 0
- P1 design defects: 0
- P1 order-execution/first-article controls: 2; neither contradicts `ORDER`
- New P2 findings: 0
