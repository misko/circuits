subject: pluto-rx2-8way-v5 v0.1.0-2026-08-13 hardware release
date: 2026-08-13
reviewer: redteam-agent (GPT-5 Codex, topology/protection/ratings lens)
context-given: release-archive-plus-authorities
source_commit: 798ef9812019efb9e9857332736926d099192a03
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Independent hardware topology, protection, and ratings review

## Scope and method

This is a hardware-only review of the exact staged release source, fabrication
payload, verification evidence, project rules, and retained primary part
authorities. Firmware is excluded. Its absence is not treated as a hardware
design defect, and this review makes no claim of autonomous switching.

I derived the required signal and power paths from the part pin tables and
rules before comparing them with the exact board. The release board is
byte-identical to the staged project board. Schematic-to-board parity reports
22/22 nets, 131/131 connected nodes, 24/24 intentional no-connects, and zero
real discrepancies. The release-local ERC and both board DRC reports contain
zero violations or unconnected items.

## Findings

### RF topology and state safety

The receive path is a true one-common/eight-throw absorptive switch topology.
J2.1 reaches U1.22/RFC. J3.1 through J10.1 reach U1 RF1 through RF8 on the
manufacturer pin order: U1.24, 2, 4, 6, 13, 15, 17, and 19. Every SMA ground
post reaches GND. U1 LS/pin 1 and exposed pad/pin 25 are grounded; the other
documented ground pins are grounded; pin 20 is intentionally open.

U1 V1..V4 are driven on pins 9..12. Independent 10 kohm biases pull V1, V2,
and V3 low and V4 high, producing the documented `V4..V1 = 1000` ALL_OFF
state while 3V3 is valid and the controller pins are high impedance. That is
the correct passive reset/tri-state hardware state. The design correctly does
not claim a defined RF state after U1 supply leaves its operating range.

PE42482A-X is rated 10 MHz to 8 GHz, so the board's 100 MHz to 5.9 GHz target
is inside the switch rating. Its 2.3 V to 5.5 V supply and 1.17 V minimum
logic-high requirements are met by 3V3; 3.3 V logic is below the 3.6 V input
maximum. The stated 0 dBm operating ceiling is far below the switch's RF
power capability. The provisional loss, isolation, and return-loss limits are
credible against the data-sheet ranges but remain physical-article claims.

All nine RF pins must remain at 0 VDC because the schematic intentionally has
no series DC-blocking capacitors. Accordingly, bias-fed or DC-present antenna
ports are outside this release boundary. There is also no claim of IEC-level
RF-port ESD or surge immunity. Those are explicit application limits, not
hidden protection provided by the switch.

### USB-C input, protection, and 3V3 rail

All four J1 VBUS contacts combine only on VBUS_RAW. The complete series path
is `J1 -> F1 -> VBUS_PROTECTED -> U3 -> 3V3`. F1 is the selected 100 mA PPTC;
its 30 mA hold rating at 85 degC remains above the 20 mA design load. This is
fault coordination, not an active current limiter.

D1 is correctly polarized with cathode/pad 1 on VBUS_PROTECTED and
anode/pad 2 on GND. The SMBJ6.0A 6.0 V standoff is above the admitted 5.5 V
normal input. Its 10.3 V rated-waveform clamp, even with the declared 20%
margin, remains below the 15 V F1 limit, 16 V C1 rating, and 20 V U3 absolute
maximum. This is a transient shunt clamp only; sustained overvoltage is
deliberately outside the product boundary.

U3 pin 1 receives VBUS_PROTECTED, pin 3/EN is tied to the same input, pin 2 is
GND, pin 5 produces 3V3, and pin 4 is open as permitted. C1 and C2 are exact
4.7 uF, 16 V parts. The conservative 1.798 uF effective-capacitance bounds on
both sides exceed the regulator's 1 uF minimum. At 5.5 V and the 20 mA load
bound, the retained 44.825 mW estimate is far below the adopted 238 mW
85-degC board-level ceiling; temperature remains a first-article measurement.

CC1 and CC2 are separate nets, each terminated by its own exact 5.1 kohm,
1% Rd and each protected by one TPD2E2U06 channel. U4 pin 4 is grounded and
its two NC pins are open. USB D+/D-/SBU contacts are explicit no-connects, so
the port is correctly power-only and cannot imply USB data service.

### Control and debug hardware

U2 has its combined supply on pin 4, ground on pin 5, local bulk and 100 nF
decoupling, and a 100 nF reset capacitor. PA0..PA3 on physical pins 7..10 map
in order to U1 V1..V4. J11 is the keyed ten-position hardware access point:
pin 1 is target-powered 3V3/VTref, pins 2 and 4 are SWDIO/SWCLK, pins 3/5/9
are GND, and pin 10 is NRST. Pins 6/7/8 are intentionally open. Nothing in
the hardware connects a programmer supply into the power path; operators must
sense J11.1 and must not drive it.

### External boundaries

The board does not rigidly mate to the Pluto. J2 is a cable interface, and
the +2.5 dBm AD9363 figure is retained only as an absolute-maximum receiver
ceiling. Operation of AD9363 silicon under an AD9361 profile outside the
official AD9363 band is accepted system risk and cannot become an Analog
Devices guarantee through this board review.

## Verdict and order hold

No hardware topology, pin-function, polarity, protection-margin, or local
rating defect was found in the exact staged design. The hardware design is
SOUND for a controlled first-article build within the boundaries above.

The order verdict remains DO-NOT-ORDER until JLC's uploader echoes the exact
BOM/CPL, controlled-impedance stack, selective 0.25 mm via fill/cap process,
and exact C429844 through-hole service; the human preview confirms U1, U2,
J11, D1, J1 and connector orientation; and the physical first-article plan
passes. Catalog stock is clear, so this is not a sourcing block.

The examined directory is intentionally pre-seal and still carries manifest
placeholders. Manifest stamping is release bookkeeping after these reviews,
not evidence of a hardware defect and not permission to order.
