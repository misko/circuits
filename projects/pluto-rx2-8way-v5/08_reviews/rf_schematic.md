review_kind: RF_SCHEMATIC
subject: Pluto RX2 8-Way v5 independent RF schematic review
reviewer: Codex sub-agent /root/v5_escape_review (GPT-5)
independence: independent-from-design-author
source_commit: 4cf5c818684e4c39f594b50a567fb086b9cf6f13
artifact_sha256: 1abd0c209be27ac602f55f8e81cf25e4e98bb3a99a2fb76494fc8bbfcf20603b
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Independent RF schematic review

This is a fresh review of the exact sealed schematic identified above, not a
renewal by assertion of the older review. The reviewer inspected the current
`rf.yaml`, architecture and accepted ADRs; pSemi DOC-75785-4; ST DS13866; the
exact part dossiers; the current schematic; and a new KiCad netlist export
from that schematic. The new export passed all 32 authored electrical
invariants. Direct examination of its RF, control, supply and ground nodes is
the basis of the four verdicts below.

requirement: RF-SCH-TOPOLOGY PASS

U1 is one PE42482A-X true absorptive SP8T. `RF_COMMON` contains only J2.1 and
U1.22/RFC. `RF_ANT1` through `RF_ANT8` contain J3.1 through J10.1 and U1 RF1
through RF8 respectively. Every J2-J10 shell/ground pin is on GND. There are no
splitters, cascaded switches, stubs made by parallel schematic branches, or
simultaneous RF outputs. With LS low, DOC-75785-4 Table 5 assigns each approved
code to exactly one throw and assigns `V4..V1=1000` to the terminated all-off
state. Off throws are absorptively terminated by U1, subject to valid U1
power and the manufacturer's RF-port conditions.

requirement: RF-SCH-PINMAP PASS

The exact netlist matches DOC-75785-4 Table 8: RF2/3/4 are U1 pins 2/4/6,
RF5/6/7/8 are pins 13/15/17/19, RFC is pin 22, RF1 is pin 24, VDD is pin 8,
V1-V4 are pins 9-12, and LS is pin 1. U1 pins 3/5/7/14/16/18/21/23 and exposed
pad 25 are on GND; NC pin 20 is explicitly unconnected, which the data sheet
allows. STM32 PA0-PA3 are physical U2 pins 7-10 and connect in order to U1
V1-V4. The resulting LS-low codes independently reproduce the manufacturer
truth table: ANT1..ANT8 are 0000, 0100, 0010, 0110, 0001, 0101, 0011 and 0111.

requirement: RF-SCH-DC PASS

U1 VDD is on 3V3, inside its 2.3-5.5 V recommended range, all U1 ground pins
and its exposed pad are grounded, and C4 is a 100 nF local supply bypass in
the schematic. Every RF net contains only one SMA centre contact and one U1
RF pin, so the board introduces no intentional RF-port bias. This passes only
under the exact-part dossier's zero-DC interface constraint: DOC-75785-4 page
20 requires all nine RF pins to remain at 0 VDC. No DC-blocking capacitors are
fitted, so biased antennas, bias tees, or any external source that places DC
on J2-J10 are outside the supported interface and must not be connected.

requirement: RF-SCH-DEFAULT PASS

U1.1/LS is tied directly to GND. R3 is 10 kohm from 3V3 to V4; R4-R6 are
10-kohm pull-downs on V1-V3. ST DS13866 states that PA0-PA3 reset as analog
inputs, so the passive word is `V4..V1=1000` while U1 is validly powered and
the MCU is reset or tri-stated. Even allocating U1's 5 uA maximum control-input
current to one 10-kohm pull produces only 50 mV of error, leaving wide margin
to U1's 1.17 V minimum high and 0.6 V maximum low thresholds. The accepted
control sequence preloads the complete 1000 GPIO word before enabling outputs,
then uses an atomic approved word with a 5 ms all-off guard; this exceeds U1's
1.4 us maximum settling time by more than three orders of magnitude. The
all-off guarantee expressly ends when U1 VDD leaves 2.3-5.5 V; neither the
manufacturer nor this review claims a defined RF state for an unpowered U1.

## RF budget and interface assessment

The selected device covers 10 MHz-8 GHz. In its 4-6 GHz data-sheet band the
worst listed maximum insertion loss is 2.3 dB, leaving 1.2 dB from the
provisional 3.5 dB board target at 5.9 GHz for launches and routed copper. The
worst listed minimum RFC-to-off isolation is 34 dB in 2-4 GHz and 29 dB in
4-6 GHz, which makes the provisional 30 dB through 4 GHz and 25 dB at 5.9 GHz
targets plausible but layout-sensitive. The return-loss tables are typical,
not guaranteed minima. Therefore none of the four assembled-board RF targets
is promoted to a schematic or data-sheet guarantee; all eight paths and all
required off states still require calibrated first-article VNA measurement at
the SMA mating planes.

The switch is not the receive-chain protection limit. The project retains a
0 dBm operator limit and treats +2.5 dBm only as the external AD9363 receiver's
absolute-maximum ceiling. There is no RF limiter and no system-level IEC ESD
network on the nine SMA centres; U1 is rated only to 1 kV HBM/CDM at the
component level. That is consistent with the declared no-high-power-protection
boundary, but it requires controlled handling and must not be represented as
receiver overdrive or connector-level ESD protection.

## Findings

- P0: none.
- P1: none within the declared zero-DC, 0 dBm, valid-U1-power schematic scope.
- P2: U1's RF state below 2.3 V VDD is unspecified; do not describe board
  power-off as guaranteed all-off.
- P2: the exposed SMA ports have no system-level RF ESD or overdrive limiter;
  operator limits and ESD handling are part of the accepted interface boundary.
- P2: insertion loss, isolation, balance and return loss remain first-article
  measurements, not schematic conclusions.

PCB impedance, launch geometry, return paths, coupling, assembly, fabrication
outputs and physical measurements are outside this schematic verdict. The
schematic is SOUND for progression to those separately reviewed gates, not
for ordering on this verdict alone.

## Latest exact renewal — commit 6d1d01ca

The exact schematic and PDF bytes remain unchanged. I exported a new
S-expression netlist and independently reran the full RF lens: 32/32
electrical invariants, 21/21 label survival, 131/131 pin-map assertions,
22/22 schematic-to-board nets with zero discrepancy, zero ERC errors, and
8/8 generated control states/windows all pass. The new machine-readable
J2-J10 through-hole assembly contract changes neither RF topology nor ratings.
P0/P1 RF schematic defects remain 0/0, with the same three P2 interface and
first-article evidence boundaries above. Verdict: **SOUND / DO-NOT-ORDER**.

## True-final exact renewal — commit 770ac064

Official local ST DS13866 Rev 5 now replaces the online-only lifecycle gap;
the earlier local document is correctly retained as Rev 3. Independent direct
reading confirms unchanged TSSOP-20 pin order, PA0-PA3 and PA13/PA14 roles,
BOR4 thresholds, HSI48 limits, supply range and package facts. The exact RF
schematic and PDF remain unchanged. A new export again passes 32/32 invariants,
21/21 labels, 131/131 pin maps, zero-discrepancy parity over 22 nets and zero
ERC errors. P0/P1 RF schematic findings remain 0/0, with the same three P2
interface/measurement boundaries. Verdict: **SOUND / DO-NOT-ORDER**.

## Final authoritative renewal — commit 3ecf08ab

V5-F2 is now correctly closed against the official local DS13866 Rev 5
evidence already independently checked. No part, RF contract, schematic, PDF,
netlist or board byte changed from the prior renewal. A fresh exact export and
gate run again passes 32/32 invariants, 21/21 labels, 131/131 pin maps, 22/22
schematic-to-board nets with zero discrepancy, zero ERC errors and 8/8 control
states/windows. P0/P1 RF schematic findings remain 0/0 with the same three P2
boundaries. Verdict: **SOUND / DO-NOT-ORDER**.

## Final bounded renewal — commit 4cf5c818

The only part-dossier delta corrects J11's `mates` value to the connector-role
schema term `plug` and retains the exact keyed FFSD receptacle relationship in
an explanatory note. P-ESC now passes 13/13. The exact schematic, PDF,
normalized connectivity, RF contract and board remain unchanged. The fresh
`3ecf08ab` electrical, pin-map, parity and ERC results therefore remain exact
for these bytes; the J11 role correction changes no RF fact. P0/P1 RF
schematic findings remain 0/0 with the same three P2 boundaries. Verdict:
**SOUND / DO-NOT-ORDER**.
