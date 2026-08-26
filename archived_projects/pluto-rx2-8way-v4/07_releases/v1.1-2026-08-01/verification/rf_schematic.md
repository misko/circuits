review_kind: RF_SCHEMATIC
subject: pluto-rx2-8way-v4 04_kicad/pluto_rx2_8way_v4.kicad_sch
reviewer: Codex GPT-5 fresh RF-schematic reviewer
independence: independent-from-design-author
source_commit: bc1fb1003cd9b7f06c70b15d973c5c018d0ff458
artifact_sha256: 3e6627ab345b25f8a46042abceafa0a509b7c0a4dbd440fe54ed32ce0cfeae4f
design_verdict: SOUND

# Independent RF schematic review

requirement: RF-SCH-TOPOLOGY PASS
requirement: RF-SCH-RATINGS PASS
requirement: RF-SCH-BIAS PASS
requirement: RF-SCH-CLAIMS PASS

## Exact-artifact examination

The declared native schematic is byte-identical to the v1.1 immutable release
source schematic. I exported a fresh XML netlist from those bytes and compared
the RF-switch, module, SMA, and control nodes against the manufacturer-derived
pin maps. The exact board additionally agrees with all 100 high-risk schematic
nodes, so the circuit examined here is the circuit assigned to the release
footprints.

## Topology, states, and terminations

- ANT1..ANT7 connect directly to PE42482 RF1..RF7. J_ANT8 and J_RX1 form the
  `RX1_MAIN` through line; a series 220 ohm + 220 ohm branch feeds RF8. RFC
  connects directly to J_RX2. There is no missing, transposed, or shorted RF
  port in the fresh netlist.
- With LS grounded, the datasheet truth table maps V1..V3 binary states 000
  through 111 to RF1 through RF8 while V4 remains low. V4 high with the lower
  controls low invokes the all-ports-terminated mute state. External 10 kohm
  pull-downs establish the powered/reset default, and the absorptive switch
  terminates deselected RF ports while powered.
- The 440 ohm reference branch remains present for every state. With 50 ohm
  source/load terminations, its first-order branch ratio relative to a matched
  through path is about `50/(440+50)`, or -19.8 dB before the small main-node
  loading correction; the documented full model of approximately -20.3 dB is
  consistent and is correctly treated as characterization-dependent.
- No RF DC blocks are fitted. That is valid only inside the binding passive,
  receive-only, 0 VDC external-interface boundary: pSemi explicitly permits
  omission when every RF pin is at 0 VDC. Bias tees, active antennas,
  transmitters, and DC-offset sources are therefore outside the supported
  system, not latent compatible use cases.

## Ratings, linearity, loss, isolation, and protection

- PE42482 supports 10 MHz to 8 GHz, covering the declared 70 MHz to 6 GHz
  band. Its 2.3 to 5.5 V supply range covers filtered 3.3 V. The four digital
  inputs are limited to 3.6 V; the documented worst-case 3.366 V module rail,
  100 ohm series resistance, and 10 kohm load keep both the incident step and
  settled logic level inside absolute and logic limits.
- The +18 dBm interface ceiling is at or below the vendor's worst declared
  recommended terminated-port CW curve and has ample margin to the selected
  path CW and compression curves over 70 MHz to 6 GHz. Hot switching is
  restricted to 100 MHz and above, consistent with the vendor's 20 dBm hot-
  switch statement. The 70 MHz to below-100 MHz procedure removes RF during
  selection and settling.
- Vendor maximum insertion loss across the used paths is as high as 2.3 dB in
  the 4 to 6 GHz row, while minimum isolation can be as low as 29 dB for some
  paths in that band. Passive-switch noise figure is correspondingly bounded
  by path loss under matched conditions. The design does not misrepresent
  these as guaranteed system performance: path loss, return loss, reference
  SIR, isolation, and phase remain explicit first-article VNA deliverables.
- The device is only specified with VDD in its recommended range; useful
  match, selection, or isolation while USB power is absent is not established
  by the datasheet and is not accepted here as a design capability. Likewise,
  there are intentionally no shunt RF ESD clamps. Safe use therefore depends
  on the documented ESD-controlled bench boundary and de-energized cable
  handling. This is a declared use limitation, not an uncredited protection
  feature.

## Bias, control, and vendor-required support

- LS is tied to GND, which both selects the intended truth-table convention
  and satisfies the vendor note that RF performance depends on a good LS
  ground. V1..V4 each have a 10 kohm pull-down at the switch and a 100 ohm
  source resistor from GP0..GP3; none is left floating during reset.
- VDD is supplied through the BLM21SP601SN1D ferrite. The downstream side has
  4.7 uF, 1 uF, and 100 nF shunt capacitance. The fresh netlist puts all three
  on filtered `3V3`, not on the module side of the ferrite.
- PE42482 pin 20 may be grounded or left open; grounding it is explicitly
  allowed. All specified ground pins and the exposed pad are grounded.
- The 128-sample blank at 30 Msps is 4.267 us, exceeding the vendor's 1.4 us
  maximum settling time. Slow-slew, 2 mA GPIO configuration remains a firmware
  obligation, but the schematic introduces no control-level or timing defect.

## Claims and acceptance posture

All three declared performance claims have numeric acceptance and reproducible
evidence: 45 to 55 ohm solved CPWG impedance, at most 1.0 mm routed-copper
spread, and at most 1.1910 mm realized fence aperture. These are geometry and
field claims, not substitutes for assembled RF performance. The contract also
requires de-embedded TDR and VNA data and explicitly holds production until
system loss/isolation limits and physical results are approved.

The exact RF schematic is electrically coherent and compatible with the
declared restricted-use envelope. No schematic-level RF defect was found;
hardware RF characterization and the stated production hold remain in force.
