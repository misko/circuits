subject: Pluto RX2 8-Way v5 clean-room schematic topology
date: 2026-08-13
reviewer: Codex exact-artifact topology and datasheet review
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
checkpoint_sha256: 0130a38cd1d074450eb5e3a8a087550fc6698900d21ec75282c5e58cb005707e
circuit_json_sha256: 37c7a0083c4736f9ee5e63f3891537d3c187ccd01384c7002db584576c63cfd3
kicad_schematic_sha256: 572849a8ea53b9fc3ef4d92d6dba5bb692d0779e9a4002090b3cfaacaacd517a
schematic_pdf_sha256: 9f2778643675c639b5026482a8624ce2373c41b05425572ba60dd800999e6cf3
netlist_sha256: 51d52ddd49ab551677b656a7593c6fd0162ec5595a6c26ac6bfdbdda12c22ced
exact_netlist_sha256: 12e7039b3e2d185b53187ecdd53acec655969aa1b19b32cdc53c2af2d16ecf21
parts_sha256: af89e5d5be339883a97cdef1d523433c4ccda1cf6b645d0935b0498ef83f1b40
design_rules_sha256: 426089542e30284dddd34c08b222e3402510bcb7612a2c4f65b6bcf20e4094f2
authoring_source_sha256: 873f6598254556541fef9be544c0b88ca0628fa011834ff4940601ba771f711b

# Independent pre-route topology review

## Verdict and boundary

**SOUND / DO-NOT-ORDER.**  The exact v5 schematic implements the commissioned
one-of-eight, receive-only selector topology and the protected USB-C-powered
control circuit.  No blocking schematic-topology, physical-pin, value,
polarity or intentional-open defect remains in the exact artifacts bound
above.

This verdict authorizes the next design stage only.  There is no PCB,
impedance solution, approved SMA land pattern, firmware binary, fabrication
package or first-article evidence, and the project's open findings continue to
block any order or design-clean claim.

## Method

I reconstructed the final exported netlist independently after the machine
checks, then compared the resulting physical pins with the exact local part
dossiers and their cited manufacturer pin tables.  The export contains the
same 33 refdes in the manifest, Circuit JSON, KiCad schematic and netlist; 150
physical pins; 21 functional named nets; and 22 deliberately one-pin
`unconnected-*` nets, for 43 KiCad nets in total.  I checked every pin of J1,
U1-U4 and J2-J10, both TVS terminals, the control-bias network and TP1-TP5.
The final source-to-netlist result independently reports 129/129 contracted
pin-map assertions and 30/30 electrical invariants.

During this review I rejected the preceding generated checkpoint: U2's
connected pin numbers were correct, but several unused STM32 pin-function
labels were wrong in the human symbol.  The TSX source was corrected against
ST DS13866, the entire pipeline was rerun, and all hashes above refer only to
the replacement checkpoint.  This is evidence that human pin/readability
review is not redundant with connectivity parity.

## USB-C power-only path

- J1 A4/A9/B4/B9 all join `VBUS_RAW`; A1/A12/B1/B12 and `SH` join GND.
  A6/A7/A8/B6/B7/B8 are separate explicit no-connects, so no USB D+/D- or SBU
  path exists.
- J1 A5 is `USB_CC1` and B5 is `USB_CC2`.  The nets remain separate through
  U4 pins 3/5 and their own 5.1 kOhm Rd resistors R1/R2.  U4 pin 4 returns to
  GND; its internally unused pins 1/2 remain open.
- The complete supply sequence is `VBUS_RAW -> F1 -> VBUS_PROTECTED -> U3 ->
  3V3`.  D1 pin 1/cathode and C1 pin 1 shunt the protected side; both pin-2
  returns are GND.  U3 IN1 and EN3 are on `VBUS_PROTECTED`, GND2 is ground,
  NC4 is open and OUT5 is `3V3`.
- C1/C2 are the selected 4.7 uF input/output parts.  The source-level
  effective-capacitance checks retain 1.798 uF at each LDO side versus 1 uF
  minimum.  The worst declared 20 mA, 5.5 V input corner dissipates about
  45 mW versus the adopted 238 mW board-dependent limit.

The design deliberately has no USB data, USB-PD, runtime communications or
active overvoltage cutoff.  The SMBJ6.0A is a transient shunt after the PPTC,
not a sustained-overvoltage disconnect.

## RF topology and truth table

- U1 is the exact PE42482A-X.  RFC pin 22 connects only to J2.1
  `RF_COMMON`.  RF1 pin 24 connects to J3.1; RF2 pin 2 to J4.1; RF3 pin 4 to
  J5.1; RF4 pin 6 to J6.1; RF5 pin 13 to J7.1; RF6 pin 15 to J8.1; RF7 pin
  17 to J9.1; and RF8 pin 19 to J10.1.
- Every J2-J10 outer pin 2-5 is GND.  U1 pins 3/5/7/14/16/18/21/23 and exposed
  pad 25 are GND; VDD8 is `3V3`; NC20 is open.
- LS1 is hard-low.  U1 V1/V2/V3/V4 pins 9/10/11/12 receive
  `SW_V1/SW_V2/SW_V3/SW_V4`.  The active words 0000, 0100, 0010, 0110, 0001,
  0101, 0011 and 0111 in V4..V1 order reproduce pSemi Table 5 RF1..RF8 for
  LS=0.  Word 1000 is the documented terminated all-off state.
- R3 pulls V4 high while R4/R5/R6 pull V1/V2/V3 low.  Reset or tri-state
  therefore requests all-off while the switch 3V3 supply remains valid.

No RF blocking capacitors are fitted because the commissioned receive-only
boundary requires 0 VDC at all external RF ports, matching the pSemi
datasheet's stated condition.  The selected switch supports 10 MHz-8 GHz;
system operation from 100 MHz to 5.9 GHz remains subject to PCB geometry and
first-article VNA qualification.  Use of the Pluto's physical AD9363 outside
its official range remains the user's recorded accepted risk and is not
converted into an Analog Devices guarantee by this review.

## Autonomous controller and programming

- U2 STM32C011F4P6 has VDD/VDDA4 on `3V3`, VSS/VSSA5 on GND and PF2/NRST6 on
  `NRST`.  PA0/PA1/PA2/PA3 pins 7/8/9/10 drive V1/V2/V3/V4 respectively.
  PA13 pin 18 is `SWDIO` and PA14/BOOT0 pin 19 is `SWCLK`.  Every other MCU
  pin is an explicit one-pin no-connect with its DS13866 function visible in
  the delivered symbol.
- TP1/TP2/TP3/TP4/TP5 expose `3V3`, GND, `SWDIO`, `SWCLK` and `NRST`.  This is
  sufficient for a target-powered Raspberry Pi GPIO/OpenOCD connection or an
  external ST-LINK; it does not make the Pi a board power source.
- C3/C5 bypass U2 from `3V3` to GND and C6 filters `NRST` to GND.  U1 has its
  independent local C4 bypass.
- The source-bound `fast20-v1` revision-1 profile has disjoint nominal dwells
  20/23/26/30/34/39/44/50 ms, 5 ms all-off guards, an 85 ms observable marker,
  a 386 ms nominal frame and 772 ms arbitrary-phase guaranteed-capture
  minimum.  The generated firmware header and decoder JSON are byte-checked
  consumers of the same YAML schedule.  Firmware behavior itself remains
  unimplemented and is not claimed by this schematic verdict.

## Retained obligations

The following do not invalidate this schematic but remain hard downstream
boundaries: confirm or revise the provisional nine identical female
right-angle SMA interfaces; capture and approve the current Amphenol drawing;
solve and record the official JLC four-layer impedance geometry; review the
exact connector launch, RF return paths, isolation and coupling on the future
PCB; implement/test the firmware and decoder; confirm actual JLC population
and orientation; and qualify all eight paths, timing, power and recovery on
first articles.  Blocking topology findings in this review: none.
