# First-article test plan — Pi USB port switch

Production remains on hold until five prototype boards complete this plan.
USB 3 operation is a qualification target, not a USB-IF compliance claim.

## Before assembly power

1. Compare the received PCB revision and Gerber preview with the v0.1.0
   manifest. Inspect all fine-pitch lands, filled/capped via-in-pad sites,
   plated holes, connector orientation and polarity marks.
2. Confirm JLC fitted `J1`, `J2`, `J3`, `J5`, `J7`, and `J9` using the accepted
   through-hole service. Hand-solder exact Wurth 692121030100 connectors at
   `J4/J6/J8/J10` and two Keystone 3568 clips at `F1`; fit a 7.5 A MINI fuse.
3. With no supply, measure no short between external 5 V and ground, each
   switched VBUS and ground, and upstream USB VBUS and the protected rail.
4. Verify Raspberry Pi header pin 1 and cable indexing. Leave all GPIOs low or
   inputs. Use a current-limited bench supply initially set to 5.20 V / 0.25 A.

## Safe-state and truth-table test

For every channel, test with the Pi absent, booting, halted and powered:

| PWR_EN | DATA_EN | Expected VBUS | Expected data path |
|---:|---:|---|---|
| 0 | 0 | off | disconnected |
| 0 | 1 | off | disconnected by hardware interlock |
| 1 | 0 | on | USB 2 and SuperSpeed disconnected |
| 1 | 1 | on | USB 2 and SuperSpeed connected |

Confirm channels are independent and no command changes another channel.
Confirm upstream Pi VBUS never energizes the external protected 5 V rail.

## Power-path qualification

1. Raise the source limit gradually after confirming normal quiescent current.
2. Load each output to 0.9 A individually, then all four simultaneously for
   at least 30 minutes at 5.15 V measured at the input terminal.
3. At thermal equilibrium, use four-wire measurements at each mated downstream
   test plug. Every output must remain at least 4.75 V and no point may exceed
   its component temperature rating. Record input current, each output voltage,
   TPS2557 temperature, input MOSFET temperature, fuse-holder temperature and
   TLV761 temperature.
4. Short each output through a controlled electronic-load fixture. Confirm
   current limiting, fault indication, recovery and absence of disturbance or
   backfeed on the other channels.
5. Sweep input power and repeat abrupt connect/disconnect cycles. Confirm the
   3.3 V rail stays in 3.242-3.358 V during qualified steady-state operation
   and that brownout/restart returns all data paths to the safe state.

## USB functional and signal-integrity qualification

Use short known-good USB 3 A-to-B upstream cables. For every channel and both a
Raspberry Pi 4 and Raspberry Pi 5:

1. Enumerate representative low-, full- and high-speed USB 2 devices. Run at
   least 1,000 power-only, full-off and reconnect cycles while checking kernel
   enumeration/errors and verifying that power-only does not promise charging
   behavior.
2. On both blue Pi host ports, enumerate a known-good USB 3 storage device,
   confirm SuperSpeed negotiation, then run sustained bidirectional transfer
   and integrity checks for at least 30 minutes per channel. Record link speed,
   throughput, retries/resets and file hashes.
3. Verify each data-off state prevents enumeration while VBUS remains within
   limits. Verify full-off removes VBUS and data. Check cross-channel crosstalk
   by transferring concurrently on all available host ports.
4. If available, measure the assembled path with TDR/VNA or an appropriate USB
   compliance fixture and compare discontinuities with the approved JLC
   90-ohm stackup calculation.

Any repeatable USB 3 failure blocks a USB 3 production claim. The design may
still be qualified and relabelled as USB 2-only only through a new documented
revision/release; it must not be silently ordered as the current claim.

## Acceptance record

Record board serial, assembly lot, JLC order number, stackup, via-process echo,
test equipment, cable identity, software/kernel versions, ambient temperature,
measurements and pass/fail for every step. Production payment/quantity remains
on hold until all safety, power and required USB tests pass on the agreed sample.
