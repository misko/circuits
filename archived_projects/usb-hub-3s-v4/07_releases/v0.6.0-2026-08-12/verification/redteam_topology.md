subject: USB Hub 3S v4 final routed board
date: 2026-08-12
reviewer: redteam-agent (topology/protection/ratings lens)
context-given: exact-board/full-tree
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Final routed topology/protection/ratings reseal

## Exact subject and method

The assigned SHA-256 was verified against the canonical routed board at
`04_kicad/usb_hub_3s_v4.kicad_pcb`. The originally supplied `03_src/...`
pathname did not exist and was corrected by the commissioning agent; no other
board was substituted. The source commit is the checked-out HEAD and the
working tree was clean at entry.

This bounded adversarial pass inspected the exact board and netlist, current
power/protection/rating rules, part dossiers and vendored manufacturer PDFs,
ADRs, exact DRC, via-process and via-ampacity evidence, and prior findings only
to verify their dispositions. Fresh read-only checks returned E-INV 91/91,
E-TOPO 4/4, E-MARGIN 12/12, E-OFF PASS and R-PAIRMAP/R-CRITESC PASS. The exact
DRC has zero violations, zero opens and zero schematic-parity findings. The
board census is 95 footprints, 446 routed segments, 183 vias and 54 zones.
Those results corroborate the review; they do not replace the first-article
tests below.

## Power, protection and interface trace

- Input power is `J1.1 BAT_POS -> F1 -> VBAT_FUSED -> Q1 drain 5..8 -> Q1
  source 1..3 -> VIN`. Q1 is oriented for reverse-battery blocking. D5 clamps
  Q1 gate-to-source and D1 SMBJ15A clamps protected VIN to GND. The TVS is
  intentionally after Q1, so a reversed battery does not forward-bias it.
  SW1 OFF hard-grounds `EN_BUS`; ON enables both buck modules through R2.
- USB-A power is `VIN -> U1 TPSM63610 -> 5VA_RAW -> U9 TPS259827O -> 5VA ->
  U4/U5/U6 TPS2559 -> VBUSA1/2/3 -> J2/J3/J4`. U9 is the no-OVLO,
  circuit-breaker `7O` option. Its split pad 25 is `5VA_RAW`, pad 26 is GND,
  RETRY_DLY and LDSTRT are grounded, and the aggregate fault response latches
  until SW1 removes input power. Each USB-A port has its own TPS2559 current
  limiter and USBLC6 clamp. U7/U8 generate only local charging signatures.
- Type-C power is `VIN -> U2 TPSM63604 -> 5VC_RAW -> U3 TPS25810 -> VBUSC ->
  J5`. IN1/IN2/AUX/EN/CHG/CHG_HI are on `5VC_RAW`, selecting a fixed-5 V,
  attach-controlled source with 3 A Type-C advertisement. CC1 and CC2 remain
  separate through D6. J5's four VBUS contacts are `VBUSC`; its four GND
  contacts and shell are GND. D+/D- and SBU contacts are explicit no-connects.
- There is no USB data path, upstream USB connector, hub controller or PHY.
  There is no USB-PD controller or voltage negotiation. The USB-A 2 A
  continuous/2.5 A for <=10 ms service is a proprietary charge-only boundary,
  not a claim of BC1.2 current compliance. The Type-C port is source-only: a
  C-to-C source/source connection does not present Rd and must not attach.
  TPS2559 and TPS25810 reverse-leakage limits make external-output backfeed
  bounded but still require the explicit ON/OFF tests below.
- There is deliberately no active sustained-overvoltage or converter-fail-high
  cutoff. SMBJ15A is a hot-plug/wiring transient clamp, not active OVP. The
  commissioned source is a protected 3S pack limited to 9.0-12.6 V, with an
  external BMS/disconnect at or above 9.0 V. A bare pack, charger/bench source
  above 12.6 V, automotive surge and unsupervised deployment are outside the
  design boundary.

## Ratings and corrected corner closures

- The three USB-A ports require 6 A continuous and may reach 7.5 A for <=10
  ms. U1 is rated 8 A continuous/10 A peak. R26 programs U9 to
  6.160253..8.066419 A, while C29 bounds the modeled aggregate overcurrent
  interval to 11.129..45.962 ms. Each 43.2 kohm TPS2559 setting derives to
  2.554..2.849 A, above the 2.5 A short peak and below each USB1130's 3 A
  contact rating. One port fault is handled locally; simultaneous persistent
  faults are also bounded by U9's upstream latch.
- The exact Type-C feedback network is now R11=4.12 kohm, R24=24.3 ohm and
  R12=1 kohm. With the full reference/tolerance/TCR corners and a deliberately
  conservative 0..500 nA analytical FB-current screen, the computed regulator
  window is 5.064237..5.227226 V. Adding the 15 mV steady-state variation
  reserve remains below 5.25 V. This closes the earlier high-corner design
  defect on paper, but the 500 nA value is an engineering screen rather than a
  TPSM63604 guaranteed maximum; exact voltage remains a release measurement.
- U3 advertises 3 A and has a 3.16..3.64 A short-current band. Its 55 mOhm hot
  maximum, the 4 mOhm exact-board allocation and the now-explicit <=39 mOhm
  complete-interconnect acceptance limit total 98 mOhm. With 5% residual
  margin, the 5.064237 V worst-low setpoint retains about 5.5 mV above 4.75 V
  at the Pi load plane. The 39 mOhm term includes both mated interfaces, plug
  paddle cards/terminations, the nominated Amphenol 10165794-Z0030YBLF 0.3 m
  cable and the Pi receptacle/entry path. It is correctly recorded as a hot
  four-wire qualification target, not inferred from GCT's one-mated-contact
  limit. USB Type-C Release 2.0 section 3.7.8.1 explicitly excludes internal
  paddle cards/substrates from that one-contact LLCR figure.
- Effective output/cold-socket capacitance is 80.784 uF at U1 versus 75 uF
  required, 40.392 uF at U2 versus 30 uF required, and 155.592 uF combined at
  U3 versus 120 uF required after the declared tolerance, DC-bias,
  temperature and lifecycle deratings. The mixed ceramic/polymer banks still
  require physical loop/transient validation.
- The exact via-process report grades all 183 vias: 65 protected 0.50/0.20 mm
  filled/capped sites and 118 ordinary 0.30 mm-drill sites, with no partial or
  ambiguous process family. Exact via-ampacity evidence passes the forced U9
  output transfer at 11.76 A credited versus 8 A required and each TPS2559
  input transfer at 3.91 A versus 2.849 A. These checks do not prove every
  broad-pour neck or full ground-return resistance.

# Findings

## P0

None found.

## P1 — order-blocking evidence and qualification gaps, not observed design defects

1. **Complete routed power-path resistance and temperature are not yet
   qualified.** A-VIA closes four forced vertical boundaries, but does not by
   itself close the full BAT/F1/Q1/VIN paths, both converter input/output
   paths, each connector path, every outer-pour neck, solder joint, or the
   corresponding GND returns. Broad pours, two internal ground planes, zero
   opens and DRC-clean copper make the topology credible; exact filled-copper
   extraction plus hot four-wire and thermal tests are still mandatory.
2. **The <=39 mOhm Type-C complete interconnect is an acceptance condition,
   not existing evidence.** No manufacturer guarantees the combined two
   mated pairs, cable internals and Pi entry path at that value. The exact
   nominated cable/Pi combination must pass hot four-wire measurement before
   any 3 A/4.75 V load-plane claim or order release.
3. **Both regulator closures remain dependent on loaded first-article data.**
   Verify the U2 engineering FB-current/15 mV variation bounds and measure
   startup, steady state, ripple, load steps and loop gain/phase for both exact
   ceramic/polymer populations across 9.0-12.6 V, load and temperature. The
   analytical changes remove the prior paper defect; they do not manufacture
   a population guarantee or a stability measurement.
4. **The input catastrophic-fault boundary is conditional on external items.**
   The exact protected pack/BMS, leads and mandatory user-fitted 10 A/32 V
   fuse have not been accepted as a coordinated system. Prospective fault
   current, the fuse's 1000 A interrupt rating, clearing time/I2t, holder and
   Q1 thermal withstand, BMS low-voltage disconnect and post-fault state must
   be verified for the selected pack. The board must never be represented as
   protecting a bare 3S pack.
5. **Fabrication execution is not proved by CAD flags.** JLC must explicitly
   accept the 1.2 mm four-layer stack and Type-VII fill/cap instruction for all
   0.20 mm-drill via-in-pad sites. Cross-section/X-ray and solder-void
   inspection of U1/U2/U3/U4-U6/U9 and C23 remain order/release gates.

## P2 — preserved interface and release boundaries

1. Labeling and release documentation must preserve: `POWER ONLY - NO USB
   DATA`, Type-C `5 V / 3 A / NO PD`, the proprietary USB-A current boundary,
   `FIT 10A MINI FUSE`, protected-pack/BMS requirement, and `NO ACTIVE OVP`.
   These are intentional scope limits, not latent capabilities.
2. Backfeed, attach/detach and fault recovery have credible component-level
   limits but no exact assembled-board evidence. Exercise each USB-A output
   and J5 with the board ON and OFF, including externally applied 5 V, both
   Type-C orientations, source/source and source/sink cases, short circuit,
   thermal cycling, detach discharge and SW1 reset of a U9 latch.
3. Final release still needs an exact-board BOM/CPL/fabrication seal, current
   stock/approved substitutions, assembly polarity/rotation evidence and a
   populated mechanical twin. These are not topology defects, but they remain
   incompatible with an order verdict of PASS.

## Mandatory controlled-first-article acceptance

Before changing `order_verdict`, perform and record:

1. Exact-board DRC/parity, via-process/ampacity and fabrication-hash replay on
   the uploaded JLC payload; obtain explicit advanced-via process acceptance.
2. Reverse battery, OFF current, hot-plug/disconnect transient and fuse/BMS
   fault tests with the nominated protected pack, leads and fitted fuse.
3. Hot four-wire extraction/measurement of every complete outbound and return
   path, including <=20 mOhm USB-A PCB allocation, <=4 mOhm Type-C PCB
   allocation and <=39 mOhm J5-to-Pi complete interconnect.
4. Simultaneous 6 A USB-A plus 3 A Type-C thermal soak at 9.0 V input; measure
   J1/F1/Q1/U1/U2/U9/U3/U4-U6, via banks, connectors and hottest copper neck.
   Exercise the <=10 ms 7.5 A USB-A peak and persistent aggregate overload,
   confirming U9 interruption/latch/reset within the modeled envelope.
5. Per-port current-limit, short, thermal-retry, backfeed and cross-port tests;
   Type-C Rd attach/detach in both orientations, 3 A advertisement/delivery,
   output discharge, source/source non-attach and 3.16..3.64 A limiting.
6. Rail voltage, ripple, startup/load-step and loop-gain/phase tests across
   input, load and temperature. Steady state must remain 4.75-5.25 V at each
   specified measurement plane and transients below the declared 5.5 V cap.

# Verdict boundary

`SOUND` means no remaining topology, protection or component-rating defect was
found for the explicitly bounded, supervised, power-only prototype. In
particular, the previous Type-C divider defect has been corrected and the
complete-interconnect resistance is now honestly represented as a measurable
acceptance requirement. `SOUND` does not assert USB-IF certification, USB-PD,
USB data, sustained-OVP tolerance, bare-pack safety, production population
qualification or successful fabrication. The P1 evidence gaps and mandatory
first-article tests require `DO-NOT-ORDER`.
