review_kind: RF_SCHEMATIC
subject: Pluto RX2 8-Way v5 final authoritative exact RF schematic review
date: 2026-08-13
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5)
independence: independent-from-design-author
source_commit: 3ecf08abe5f44c098144abfc8cea31fc89354c59
artifact_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
stm32_rev5_sha256: e392b1542086b25f6bcb8856b6c0467aa3ec10e31f03bdafca74796485c531fe
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_findings: 0
p1_findings: 0
p2_findings: 3

# Final authoritative independent RF schematic review

I reviewed the exact commit-bound schematic, not an earlier verdict. Evidence
included pSemi DOC-75785-4, official local ST DS13866 Rev 5, exact dossiers,
`rf.yaml`, control contracts and all four PDF pages. A new KiCad S-expression
export passes 32/32 electrical invariants, 21/21 global-label survival and
131/131 pin-map assertions. Schematic-to-board parity is zero-discrepancy over
22 nets, 131 connected nodes and 24 no-connects. Fresh ERC has zero errors;
the 190-warning presentation/library baseline is not used as connectivity
proof.

requirement: RF-SCH-TOPOLOGY PASS

One PE42482A-X implements the absorptive SP8T. `RF_COMMON` joins only J2.1 and
U1.22/RFC. `RF_ANT1` through `RF_ANT8` join J3.1 through J10.1 to U1 RF1-RF8
in order. Every SMA shell is GND. There is no splitter, switch tree, parallel
branch or simultaneous output. With LS low, pSemi Table 5 selects one throw
per approved word and defines `V4..V1=1000` as terminated all-off.

requirement: RF-SCH-PINMAP PASS

The exact netlist reproduces pSemi Table 8: RF2/3/4 pins 2/4/6; RF5/6/7/8
pins 13/15/17/19; RFC pin 22; RF1 pin 24; VDD pin 8; V1-V4 pins 9-12; LS pin
1. Ground pins 3/5/7/14/16/18/21/23 and exposed pad 25 are GND; allowed NC
pin 20 is explicit no-connect. Official ST Rev 5 confirms PA0-PA3 on U2 pins
7-10 and PA13/PA14 on pins 18/19. PA0-PA3 own V1-V4 in order. Approved RF1-
RF8 words are 0000, 0100, 0010, 0110, 0001, 0101, 0011 and 0111.

requirement: RF-SCH-DC PASS

U1 VDD is regulated 3V3 inside 2.3-5.5 V, with local C4 100 nF bypass. Each
RF net has only one SMA centre and one U1 RF pin. DOC-75785-4 requires every
RF pin at 0 VDC. No DC blocks exist, so biased antennas, bias tees and other
DC-bearing RF sources are explicitly unsupported.

requirement: RF-SCH-DEFAULT PASS

LS is hard-low. R3 pulls V4 high and R4-R6 pull V1-V3 low, all at 10 kohm,
so reset/tri-state produces `1000` while U1 is validly powered. U1's 5 uA
maximum input current shifts a pull only 50 mV. Official ST Rev 5 confirms the
MCU pin/supply/BOR facts. The generated profile passes 8/8 states and 8/8
windows, preloads all-off, uses atomic approved words and inserts 5 ms guards
versus 1.4 us maximum switch settling. No state is claimed below 2.3 V U1 VDD.

## Ratings and findings

PE42482 covers 10 MHz-8 GHz. Its 4-6 GHz worst maximum insertion loss is
2.3 dB and path-dependent minimum isolation reaches 29 dB. Launch/trace loss
is additional and return-loss values are typical. All paths and required off
states therefore require calibrated first-article VNA qualification.

- P0: 0.
- P1: 0 within the zero-DC, 0 dBm, valid-U1-power scope.
- P2: RF state is unspecified when U1 is unpowered/below range.
- P2: SMA centres have no limiter or system-level connector ESD network.
- P2: assembled RF performance remains physical measurement evidence.

V5-F2 is correctly closed by the official local evidence. PCB/fab/firmware and
physical qualification remain separate, so `SOUND` does not authorize order.
