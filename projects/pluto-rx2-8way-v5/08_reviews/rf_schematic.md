subject: Pluto RX2 8-Way v5 independent RF schematic review
reviewer: Codex sub-agent /root/v5_rf_schematic_review (GPT-5)
independence: independent-from-design-author
source_commit: ded717018b2feb11bf9eb46c60558e9d1af7be2b
review_kind: RF_SCHEMATIC
artifact_sha256: 572849a8ea53b9fc3ef4d92d6dba5bb692d0779e9a4002090b3cfaacaacd517a
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Independent RF schematic review

The reviewer received only the v5 project artifacts, rules, dossiers and local
manufacturer documents and was explicitly prohibited from inspecting or using
any earlier Pluto project.  It independently recomputed the exact schematic
SHA-256 above.  A fresh KiCad netlist export differed from the checkpoint
netlist only in its generated timestamp.

requirement: RF-SCH-TOPOLOGY PASS

U1 is one PE42482-class absorptive SP8T. `RF_COMMON` connects J2.1 only to
U1.22/RFC; `RF_ANT1` through `RF_ANT8` connect J3.1-J10.1 respectively to U1
RF1-RF8. All SMA shell pins connect to GND. This matches pSemi DOC-75785-4's
absorptive SP8T topology and 10 MHz-8 GHz device rating.

requirement: RF-SCH-PINMAP PASS

The exact netlist mapping matches DOC-75785-4 page 20: RF2/3/4 on pins 2/4/6,
RF5/6/7/8 on 13/15/17/19, RFC on 22, RF1 on 24, VDD on 8, V1-V4 on 9-12, LS
on 1, every listed ground pin plus exposed pad on GND, and pin 20 NC. STM32
PA0-PA3 are physical pins 7-10 and connect in order to V1-V4, matching ST
DS13866.

requirement: RF-SCH-DC PASS

U1.8 is on 3V3, within the manufacturer's 2.3-5.5 V operating range; every U1
ground pin and EP is grounded, and C4 provides 100 nF rail bypassing. Each RF
net contains only its SMA center pin and applicable U1 RF pin, so the board
injects no DC onto an RF interface. This passes under the declared zero-DC RF
interface contract. DOC-75785-4 requires every RF pin to remain at 0 VDC;
externally biased sources and bias tees are therefore outside the supported
interface because no series DC-blocking capacitors are fitted.

requirement: RF-SCH-DEFAULT PASS

U1.1/LS is tied directly to GND. R3 is 10 kOhm from 3V3 to V4; R4-R6 are 10
kOhm pull-downs on V1-V3. The passive word is therefore `V4..V1 = 1000`, the
all-ports-terminated state in DOC-75785-4 Table 5. ST DS13866 states ordinary
GPIOs reset as analog inputs, so PA0-PA3 do not override these pulls during
reset. With U1's 5 uA maximum logic-input current, worst-case pull error is 50
mV, comfortably inside the 1.17 V VIH and 0.6 V VIL limits.

Defects within the declared zero-DC RF-interface scope: none.  PCB stackup,
impedance, launch, return-path, coupling and first-article RF performance
remain explicitly outside this schematic verdict.
