subject: usb-hub-3s-v4 exact routed r8 topology/protection/ratings review
date: 2026-08-12
reviewer: redteam-agent (topology/protection/ratings lens)
context-given: zero-context
source_commit: cc8368ffbb7b93cf8f4b567534e8537df792d638
board_sha256: 6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b
design_verdict: DEFECTIVE
order_verdict: DO-NOT-ORDER

# Scope and method

The review subject was `04_kicad/usb_hub_3s_v4.kicad_pcb`. Its SHA-256 was
verified at entry and again immediately before this file was created. The
promoted route `03_src/route/r8.kicad_pcb` independently matched the assigned
SHA-256 `8ea0f50681d48c34c6e5f300cc8842f144937cd92fb118cad6a546d19acf173f`.
`06_build/route/import_provenance.json` binds that route hash to the promoted
import, and the exact board has 95 footprints, 629 track/via objects, 54 zone
objects, and zero connectivity-reported unconnected items.

I used only the exact schematic/board/netlist, BRIEF/ARCHITECTURE/DETAIL_DESIGN
and ADRs, part dossiers and local primary datasheets, authored configuration,
tscircuit source/artifacts, and routed machine evidence. I did not read an
`08_reviews` conclusion or `STATUS`. I independently inspected the board
object model, component pin/net maps, filled layer zones, nearby power/ground
vias, current-class contracts, exact-hash via reports and the primary TI/GCT
limits cited below. Cheap gates re-run read-only were E-INV (91/91), E-ADR
(1/1), E-MARGIN, E-OFF and R-CRITESC; they passed. The exact-hash DRC report
has no violation, schematic-parity, or unconnected entry. These checks prove
connectivity/intent, not the unresolved electrical guarantees in the findings.

# Independent power and fault trace

The exact netlist implements the intended chain:

`J1.1 BAT_POS -> F1 -> VBAT_FUSED -> Q1 drains 5..8 -> Q1 sources 1..3 -> VIN`.
Q1 is a DMP3013SFV-7 P-channel device in the correct reverse-battery
orientation. D5 is cathode-at-VIN/anode-at-gate; R22+R23 form the 200 kohm
source-to-gate leg and R1 the 100 kohm gate-to-ground leg. D1 SMBJ15A and C1
100 uF/35 V are on protected VIN, so a reversed pack is not applied directly
to the unidirectional rail TVS. SW1 OFF grounds EN_BUS; the only ON pull-up is
R2=1 Mohm from VIN.

VIN independently feeds U1 TPSM63610 and U2 TPSM63604. The USB-A chain is
`U1 -> 5VA_RAW -> U9 TPS259827O -> 5VA -> U4/U5/U6 TPS2559 -> VBUSA1/2/3 ->
J2/J3/J4`. U9 is the `7O` no-OVLO circuit-breaker variant, with EN_UVLO tied
to input, RETRY_DLY and LDSTRT grounded, R26=210 ohm, C29=47 nF and C30=3.3 nF.
Each port switch has all parallel input/output lands connected and a 43.2 kohm
ILIM resistor. U7/U8 TPS2513A connect only local USB-A D+/D- charging-signature
nets; none reaches an upstream connector, PHY or hub controller. D2-D4 are
local USBLC6 clamps.

The Type-C chain is `U2 -> 5VC_RAW -> U3 TPS25810 -> VBUSC -> J5`. U3 IN1,
IN2, AUX, EN, CHG and CHG_HI are all on 5VC_RAW, selecting attach-controlled
fixed-5 V sourcing, 3 A Rp advertisement and the 3.16..3.64 A current-limit
band. R14 is the specified 100 kohm REF-to-REF_RTN resistor. CC1 and CC2 remain
separate through D6 and U3. J5 A6/A7/B6/B7 and both SBU contacts are explicit
no-connects. Thus this is power-only Type-C, not USB-PD and not USB data.

Reverse/fault behavior is bounded but not universal. Q1 blocks a reversed
pack. TPS2559 specifies at most 1 uA reverse leakage for an externally driven
USB-A output with its input at zero; TPS25810 specifies at most 3 uA through
85 C for OUT-to-IN reverse leakage. U9 itself is not a reverse-blocking eFuse,
but it is behind the three TPS2559 devices. A USB-A short current-limits and
can thermally cycle locally; three persistent faults make U9 latch off until
SW1 is cycled. A Type-C short is limited by U3 and may thermally cycle. No
sustained source-OVP or converter-fail-high cutoff exists, consistently with
the commissioned supervised-prototype boundary.

# Ratings and calculations checked

- At the declared divider high corners, continuous output power is
  `3*5.229*2 + 5.234*3 = 47.076 W`; at 9.0 V and 90% efficiency this is
  `5.812 A`. The coincident USB-A peak is
  `3*5.229*2.5 + 5.234*3 = 54.920 W`, or `6.780 A`. Both are below the 7.2 A
  VIN routing contract and 10 A fuse value.
- With Q1's guaranteed 17 mohm maximum at VGS=-4.5 V, dissipation is about
  `5.812^2*0.017 = 0.574 W` continuous and `6.780^2*0.017 = 0.782 W` peak,
  before hot RDS(on) rise. This remains a mandatory thermal qualification.
- The 200k:100k Q1 divider gives nominal `|VGS|=2/3*VIN`. With the dossier's
  full +/-10 uA gate leakage and resistor corners it retains at least 5.29 V
  drive at 9 V and stays below the 25 V VGS absolute rating at the declared
  29.28 V coordination corner. Q1 is 30 V, C1 is 35 V, U1/U2 are 36 V
  recommended/42 V absolute, while SMBJ15A is 15 V standoff and 24.4 V maximum
  clamp at its declared 10/1000-us point. The TVS is a transient clamp only.
- TPS2559 with each exact 43.2 kohm, 0.1%, 25 ppm/C resistor is declared and
  machine-derived at 2.554..2.849 A. This passes a 2.5 A short peak and stays
  below the USB1130 3.0 A contact rating. It is not a BC1.2 2.5 A compliance
  claim.
- U9 is derived at 6.160253..8.066419 A. It passes 6 A steady service by only
  0.160 A at its low corner, and trips below the `3*2.849=8.547 A` downstream
  worst-high sum by 0.481 A at its high corner. The fully charged C29 limits
  the overcurrent interval to 11.129..45.962 ms; this passes the declared
  <=10 ms, 7.5 A peak but makes every >8 A case a measured transient, not an
  8 A continuous claim.
- The effective ceramic banks compute to
  `6*22*0.90*0.80*0.85 = 80.784 uF` at U1 versus 75 uF required, and
  `3*22*0.90*0.80*0.85 = 40.392 uF` at U2 versus the conservative 30 uF
  requirement. C23 contributes `180*0.8*0.8 = 115.2 uF`; with the U2 ceramic
  bank, the TPS25810 cold-socket input has 155.592 uF versus 120 uF required.
  CFF is intentionally absent; U1's 100 uF polymer can put its ESR zero below
  the TPSM63610 200 kHz no-CFF boundary. Stability is not thereby proved.
- The exact board contains full-board GND zones on both In1.Cu and In2.Cu,
  plus F/B ground pours. The exact-hash via report counts a 14 x 0.30 mm-hole
  5VA collector bank (11.76 A credited) and 5-via input banks at each TPS2559
  (3.91 A credited each), all above their declared currents. J2-J4 power and
  return contacts are through-hole and directly enter the inner planes. J5's
  paired ground lands each have a ground via essentially at the pad. This is
  credible topology, but the report grades only those four 5VA crossings and
  does not close the complete current/resistance paths discussed below.

# Findings

## P0

None found in the reviewed scope.

## P1

1. **The Type-C production maximum-voltage corner is not guaranteed.** The
   U2 high setpoint calculation is 5.233026 V. Adding the project's assumed
   15 mV ripple/line/load reserve reaches 5.248026 V, leaving only 1.974 mV to
   the 5.250 V ceiling. Unlike U1, the TPSM63604 datasheet gives only a typical
   FB input-bias current; the rules substitute an engineering 50 nA bound.
   Only another `1.974 mV / 41.5 kohm = 47.6 nA` beyond that assumption would
   consume the remaining ceiling. A first-article measurement cannot turn an
   unspecified production/process/temperature maximum into a guaranteed
   population limit. Obtain a manufacturer-backed bound, increase setpoint
   margin, or explicitly relax the service ceiling before release.

2. **The 3 A Type-C load-plane IR guarantee does not close from component
   maxima.** The declared 88 mohm path is 55 mohm U3 + 4 mohm PCB + 15 mohm
   mated contacts + 14 mohm cable. The exact GCT USB4105 dossier gives 40 mohm
   maximum initial contact resistance. Even ideal four-way current sharing
   gives `2*(40/4)=20 mohm` for VBUS plus GND, already 5 mohm over the mated
   allocation before plug/termination aging or imbalance. Substituting only
   that component maximum gives 93 mohm; at 3 A with the stated 20% margin the
   drop is `3*0.093*1.2 = 334.8 mV`, versus
   `5.069841-4.750 = 319.841 mV` available (14.959 mV deficit). The 15 mohm
   mated-pair and 14 mohm hot-cable values are qualification targets, not
   guaranteed exact-part maxima. A nominated cable/plug/receptacle assembly
   must be resistance-qualified hot, or the rail/path budget must change.

3. **Exact-board copper ampacity and resistance are unclosed for most forced
   paths and all returns.** The exact-hash `via_ampacity.json` proves only the
   U9-to-distributor and three TPS2559 input banks. It does not grade BAT/F1/Q1
   to VIN, VIN to both modules, U1 raw input/output, TPS2559 output-to-J2/J3/J4,
   U2/U3/J5 VBUS, or the corresponding GND return current. The available rules
   audit rejects the nominal track floors under IPC-2221 (for example 5VA
   1.0 mm versus 5.288 mm at 8 A, VIN 1.0 mm versus 4.573 mm at 7.2 A), while
   the authored rules answer that the real paths are pour-fed and explicitly
   defer exact filled-copper extraction and thermal testing. Broad filled
   zones and two inner GND planes make success plausible, but connectivity,
   outline dimensions and via counts do not prove neck resistance, sharing,
   spreading or hot temperature. Produce exact filled-copper/neck extraction
   for outbound and return paths and verify it by loaded four-wire/thermal
   testing before fabrication approval.

4. **The battery catastrophic-short protection boundary is conditional and
   uncoordinated.** The named 0297010.WXNV fuse is 10 A/32 V with 1000 A
   interrupt rating, but it is user-installed, the actual protected pack and
   prospective fault current are unnamed, and no fuse time-current/I2t proof
   coordinates it to Q1, its holder, or either module. A 10 A fuse is therefore
   only a wiring/trunk fire boundary, not demonstrated semiconductor
   protection. Select the exact protected pack/BMS and wiring, prove available
   fault current below 1000 A, check fuse clearing versus conductor/holder/Q1
   withstand, and document the mandatory fuse fitment before release.

5. **Both converter control loops remain measurement-only closures.** U1's
   no-CFF choice correctly respects the possible polymer ESR zero below
   200 kHz; U2's no-CFF choice is reasonable because its ceramic bank exceeds
   minimum. Neither mixed ceramic/polymer network has a model or measured
   loop-gain/phase result, however. The documents explicitly defer frequency
   response and load-step/startup behavior. Because an unstable or marginal
   loop can violate both output limits and protection coordination, these are
   unresolved release findings, not optional characterization.

## P2

1. **Layer-use documentation is stale.** ARCHITECTURE says In2.Cu distributes
   VIN/regulated power. The exact routed board instead has full-board GND
   zones on both In1.Cu and In2.Cu; power distribution is on F.Cu/B.Cu pours.
   The exact implementation is favorable for return current, but manufacturing
   and review documentation must describe the board actually being ordered.

2. **The inspected JLC BOM is still a pre-route artifact.** Exact board fields,
   tscircuit source and the pre-route BOM agree on the reviewed safety-critical
   MPNs/values, but there is no sealed exact-routed release BOM/CPL/fab package
   tied to board hash 6da6560d... . This blocks orderability even apart from the
   electrical findings. The blade fuse must be called out as user-installed,
   and the advanced Type-VII fill/cap process must be present in the final JLC
   order remarks.

# Limitations

No physical first article exists, so I could not measure hot resistance,
current sharing, temperature, switching ripple, loop gain, transient waveforms,
ESD, connector retention or the real battery-lead hot-plug waveform. I did not
derive copper resistance from zone outline alone because that would falsely
credit islands/necks and parallel paths. The cited pre-route rules audit is
older than the exact board and is used only to show that nominal trace floors
do not constitute an ampacity proof; it is not treated as an exact-board fail.
Stock, JLC assembly feasibility and uploader interpretation are volatile and
were not refreshed. No claim is made for a bare/unprotected 3S pack, sustained
source above 12.6 V, automotive surge, converter fail-high protection, USB-PD,
USB data, or USB-IF compliance above BC1.2's current boundary.

# Mandatory loaded first-article obligations

These are release-blocking tests, not suggestions:

1. Use the exact nominated protected 3S pack/BMS, lead and 10 A fuse. Verify
   polarity marking/operator view, OFF current at 9.0 and 12.6 V over hot/cold,
   reverse-battery current, pack/BMS >=9.0 V disconnect, prospective short
   current, fuse clearing, holder/Q1 temperature and safe post-fault state.
2. Capture VIN at J1/Q1/U1/U2 during plug-in and lead disconnect at both pack
   limits with the production lead. Demonstrate the SMBJ15A/C1/Q1 waveform
   stays inside component pulse/absolute limits; do not use this test to imply
   sustained-OVP protection.
3. Four-wire every complete loaded path hot: BAT-to-U1/U2, U1-to-U9-to-each
   USB-A receptacle and its GND return, and U2-to-U3-to-J5-to-the nominated Pi
   cable/load return. Confirm <=20 mohm USB-A PCB allocation, <=4 mohm Type-C
   PCB allocation, <=15 mohm mated Type-C contacts and <=14 mohm hot cable, or
   re-budget the guaranteed rail floor. Correlate to exact copper extraction.
4. Thermally soak at 9.0 V input with all ports simultaneous: USB-A 2 A each
   and Type-C 3 A. Measure fuse, holder, J1, Q1, U1/U2/U9/U3/U4-U6, all via
   banks, connector contacts and the hottest copper neck. Repeat 2.5 A on each
   USB-A port for the declared <=10 ms coincident peak and a hot <=50 ms
   aggregate overload; show U9 interrupts/latches and SW1 resets it.
5. Test each USB-A output short, overload and external 5 V backfeed with the
   board ON and OFF. Confirm 2.554..2.849 A limiting, no damaging reverse feed,
   local thermal behavior, FAULT behavior and no cross-port collapse outside
   the aggregate contract.
6. Test Type-C attach/detach in both orientations with compliant Rd and e-marked
   cable cases: no VBUS before attach, 3 A Rp advertisement, 3 A continuous
   delivery, 3.16..3.64 A short-current band, detach discharge, hot/cold
   reverse-backfeed leakage and connector temperature. Verify all USB2/SBU
   contacts remain electrically open to the board and USB-A D+/D- terminate
   only in the local charging-signature cells.
7. Across 9.0/12.6 V, hot/cold and no-load/full-load, measure both rails with a
   calibrated high-bandwidth setup. Steady state must remain <=5.25 V and the
   declared load-plane floors must hold; startup/load-step excursions must
   remain <=5.5 V. Explicitly cover line/load ripple beyond the computed
   divider corner.
8. Measure loop gain/phase and startup/load-step response of both converters
   with the exact fitted ceramic/polymer banks across input, load and
   temperature. Record acceptance criteria and margin; no visual waveform-only
   stability inference is sufficient.
9. On assembled coupons/first articles, confirm 0.20 mm-hole via-in-pad fields
   are filled/capped and ordinary 0.30 mm-hole vias remain the specified
   process family; cross-section or X-ray the critical U1/U2/U3/U9/U4-U6 fields
   and inspect solder voiding. Re-run exact-board DRC, parity, via-process,
   via-ampacity, BOM/CPL and release-hash gates on the sealed fabrication set.

# Exit integrity

Immediately before this append-only review was written, the exact board hash
was again `6da6560dd325ef8d9f21ef0dcc99f238e1cb2dd1ec60a76bd4db000ec8c3355b`
and promoted r8 was again
`8ea0f50681d48c34c6e5f300cc8842f144937cd92fb118cad6a546d19acf173f`.
The unresolved P1 findings require `design_verdict: DEFECTIVE`; no fabrication
or assembly order is authorized.
