review_kind: RF_SCHEMATIC
subject: Pluto RX2 8-Way v5 renewed independent exact RF schematic review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5)
independence: independent-from-design-author
source_commit: dae8320d3a5bab507a5846c7886ea719dc05ef61
artifact_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Renewed independent RF schematic review

This review was performed from the exact artifact and current source
authority rather than inherited from an earlier verdict. I reopened pSemi
DOC-75785-4, the exact PE42482A-X dossier, `rf.yaml`, the accepted architecture
and control contract, the exact schematic and its four-page PDF. A fresh
KiCad S-expression netlist exported from the exact schematic passes 32/32
electrical invariants, 21/21 global-label survival and 131/131 physical pin-map
assertions. Exact schematic-to-saved-board parity is independently zero-
discrepancy over 22 nets, 131 connected nodes and 24 intentional no-connects.
Fresh ERC reports zero errors; its 190 warnings are reviewed presentation and
synthetic-library findings rather than a substitute for the connectivity
checks above.

requirement: RF-SCH-TOPOLOGY PASS

U1 is a single PE42482A-X true absorptive SP8T. `RF_COMMON` joins only J2.1
and U1.22/RFC. `RF_ANT1` through `RF_ANT8` join J3.1 through J10.1 in order to
U1 RF1 through RF8. Each SMA's four shell contacts are grounded. There is no
splitter, cascaded switch, parallel RF branch or second simultaneously active
throw. With LS low, pSemi Table 5 selects exactly one throw for each approved
code and defines `V4..V1=1000` as the internally terminated all-off state.

requirement: RF-SCH-PINMAP PASS

The fresh netlist reproduces pSemi Table 8: RF2/3/4 are pins 2/4/6,
RF5/6/7/8 are pins 13/15/17/19, RFC is pin 22, RF1 is pin 24, VDD is pin 8,
V1-V4 are pins 9-12 and LS is pin 1. Ground pins 3/5/7/14/16/18/21/23 and
exposed pad 25 are grounded; allowed NC pin 20 is explicit no-connect. STM32
PA0-PA3, physical U2 pins 7-10, own V1-V4 in order. The eight selected words
are 0000, 0100, 0010, 0110, 0001, 0101, 0011 and 0111, matching the LS-low
manufacturer table for RF1-RF8.

requirement: RF-SCH-DC PASS

U1 VDD is the regulated 3V3 rail, inside its 2.3-5.5 V recommended range, and
C4 is the local 100 nF bypass. Every RF net contains only one SMA centre and
one U1 RF pin, so the board adds no intentional DC. This passes only within
the declared zero-DC interface: DOC-75785-4 requires pins 2, 4, 6, 13, 15,
17, 19, 22 and 24 to be at 0 VDC. There are no DC-blocking capacitors; biased
antennas, bias tees and other DC-bearing RF sources are outside scope.

requirement: RF-SCH-DEFAULT PASS

U1.1/LS is hard-low. R3 pulls V4 to 3V3 with 10 kohm; R4-R6 pull V1-V3 to
ground with 10 kohm. When PA0-PA3 are reset or tri-stated the passive word is
therefore `1000`. Even assigning the data-sheet 5 uA maximum control-input
current to one pull produces only 50 mV error, with ample margin to U1's
1.17 V high and 0.6 V low thresholds. The generated control contract preloads
the complete all-off word before enabling GPIO, uses atomic approved words
and inserts a 5 ms all-off guard versus 1.4 us maximum switch settling. This
guarantee applies only while U1 VDD remains within 2.3-5.5 V; no defined RF
state is claimed for an unpowered U1.

## RF ratings and evidence boundary

PE42482 covers 10 MHz-8 GHz. Its worst listed maximum insertion loss in the
4-6 GHz band is 2.3 dB, leaving 1.2 dB to the provisional 3.5 dB assembled-
path target at 5.9 GHz. Its minimum RFC-to-off isolation is path-dependent,
including 29 dB for RF1/8 at 4-6 GHz. These data make the target plausible,
not guaranteed after launches and routing. Return-loss entries are typical.
All eight paths and required off states still need calibrated first-article
VNA measurements at the SMA mating planes.

The accepted receive interface retains a 0 dBm operator limit and treats
+2.5 dBm only as the external AD9363 receiver absolute maximum. There is no
RF limiter, connector-level IEC ESD network or DC block on the nine SMA
centres. Component HBM/CDM qualification is not a system-level connector ESD
claim.

## Findings

- P0: 0.
- P1: 0 within the declared zero-DC, 0 dBm, valid-U1-power schematic scope.
- P2: U1's RF state below 2.3 V VDD is unspecified.
- P2: exposed SMA ports rely on operator power limits and controlled ESD
  handling rather than an RF limiter or system-level ESD network.
- P2: assembled insertion loss, isolation, balance and return loss remain
  first-article measurements.

The corrected selective via-process contract does not alter this schematic
artifact or its connectivity. PCB impedance, launch construction, return
paths, fabrication and physical performance remain separate review stages.
