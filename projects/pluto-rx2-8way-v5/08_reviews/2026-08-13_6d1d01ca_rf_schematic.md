review_kind: RF_SCHEMATIC
subject: Pluto RX2 8-Way v5 seal-final exact RF schematic review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5)
independence: independent-from-design-author
source_commit: 6d1d01cabb06301646136c6f729a027d8235160e
artifact_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_findings: 0
p1_findings: 0
p2_findings: 3

# Seal-final independent RF schematic review

This verdict was renewed from the exact commit-bound artifact, not inherited
from a prior review. I reopened pSemi DOC-75785-4, the exact PE42482A-X
dossier, `rf.yaml`, control contracts, the schematic and all four PDF pages.
A fresh KiCad S-expression export passes 32/32 electrical invariants, 21/21
global-label survival and 131/131 physical pin-map assertions. Exact
schematic-to-saved-board parity covers 22/22 nets, 131/131 connected nodes and
24/24 intentional no-connects with zero discrepancies. Fresh ERC has zero
errors; the known 190-warning presentation/library baseline does not replace
the independent connectivity evidence.

requirement: RF-SCH-TOPOLOGY PASS

U1 is one PE42482A-X absorptive SP8T. `RF_COMMON` joins only J2.1 and
U1.22/RFC. `RF_ANT1` through `RF_ANT8` join J3.1 through J10.1 in order to U1
RF1 through RF8. All SMA shell pins are grounded. No splitter, switch tree,
parallel RF branch or simultaneously active output exists. With LS low,
pSemi Table 5 selects one throw per approved code and defines
`V4..V1=1000` as terminated all-off.

requirement: RF-SCH-PINMAP PASS

The fresh netlist reproduces pSemi Table 8: RF2/3/4 are pins 2/4/6;
RF5/6/7/8 are pins 13/15/17/19; RFC is pin 22; RF1 is pin 24; VDD is pin 8;
V1-V4 are pins 9-12; LS is pin 1. Ground pins 3/5/7/14/16/18/21/23 and exposed
pad 25 are grounded, while allowed NC pin 20 is explicit no-connect. STM32
PA0-PA3, physical pins 7-10, own V1-V4 in order. The eight words 0000, 0100,
0010, 0110, 0001, 0101, 0011 and 0111 match RF1-RF8 in the LS-low table.

requirement: RF-SCH-DC PASS

U1 VDD is on regulated 3V3, inside its 2.3-5.5 V range, and C4 is its local
100 nF bypass. Each RF net contains one SMA centre and one U1 RF pin, with no
intentional DC source. DOC-75785-4 requires all nine RF pins at 0 VDC. No DC
blocks are fitted, so biased antennas, bias tees and DC-bearing RF sources are
outside the supported interface.

requirement: RF-SCH-DEFAULT PASS

U1.1/LS is hard-low. R3 pulls V4 high with 10 kohm; R4-R6 pull V1-V3 low with
10 kohm. Reset or tri-state therefore produces `1000` while U1 is validly
powered. At the data-sheet 5 uA maximum input current a 10-kohm pull shifts
only 50 mV, leaving ample threshold margin. The generated controller profile
passes 8/8 states and 8/8 windows, preloads all-off before enabling outputs,
uses atomic approved words and inserts a 5 ms all-off guard versus U1's
1.4 us maximum settling time. No RF state is guaranteed below 2.3 V VDD.

## Ratings and findings

PE42482 covers 10 MHz-8 GHz. At 4-6 GHz its worst maximum insertion loss is
2.3 dB and minimum isolation is path-dependent down to 29 dB. These values
make the provisional assembled targets plausible, not guaranteed after
launches and traces; return-loss entries are typical. All eight paths and
required off states still need calibrated mating-plane VNA qualification.

- P0: 0.
- P1: 0 within the declared zero-DC, 0 dBm, valid-U1-power scope.
- P2: power-off RF state is unspecified below U1's valid VDD.
- P2: SMA centres have no RF limiter or system-level connector ESD network.
- P2: loss, isolation, balance and return loss remain physical measurements.

The new machine-readable J2-J10 through-hole assembly contract changes no
schematic topology or rating. PCB, fabrication and hardware performance remain
separate gates, so this SOUND verdict is not an order authorization.
