subject: programmable-usb2-hub canonical schematic normalized-netlist 96fd7969f683
date: 2026-08-02
reviewer: fresh independent redteam-agent (GPT-5, topology/protection/ratings lens)
context-given: exact current schematic-phase sources, generated netlist, adopted rules, part dossiers, cited local evidence, and startup image; prior review conclusions and routed-board state excluded as authority
review_stage: pre-route
review_kind: topology
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
netlist_sha256: 96fd7969f6839c878ccee397edff26c1052e23b06178763177bd13cf406db1c9
parts_sha256: 2a498042bcf6166713dbbe90aacc63134cd30edf3ed4cd3094327b4e1af19854
design_rules_sha256: d732d22b90dbae6f31d9099d2c789ab06df32d96e2c43e207232c55faa24100e
raw_netlist_sha256: 3d5d4ef50c6192969d568fa31c0c3370a7aa44eea9b3a202f84c500850cb4670
schematic_sha256: 794bf7ef21fd886016990c14b07a92a693206d8805b55cbd6005b53375a00d97
circuit_json_sha256: ef8b92784881a561614181f0f2ea4357d5ed6a5a3e23bf6f4d25b07bd19e85aa
tsx_sha256: b81e15b50ffe887c1ae5eb2ae1b7bea0c3ca11c428619bce9213cf28608c05d4
manifest_sha256: 9d3be4b029ddd32cd871ecb209182c360a60e86c0a7077d03be3cc102ee31945
startup_c_sha256: 49bc5c87c907602e534c87199cd65b26f7f6ef2ef1322f87b7eb6c137ae492ad
startup_h_sha256: 14ac97967810672115ab866265ed04bffabbece72bb8be97ac245f1a67449805
startup_test_sha256: 05860f9d6f8b21329128f046bfc3d5b0ab0ee1de511292510b0ea30036b6ebaa

The `netlist_sha256` field is the checker-defined normalized electrical
digest of `06_build/netlists/programmable_usb2_hub.net`. Only KiCad's export
clock and UUID-shaped component-instance timestamps are normalized; component
identities, values, footprints, nets, nodes, pin numbers, and pin functions
remain byte-bound. The routed PCB and the noncanonical untracked
`04_kicad/programmable_usb2_hub.net` are outside this schematic-phase witness.

The preceding rules-only rebind inserted one `fresh_reload` pass immediately after
the second/final zone fill and before `unify_zone_priorities` and
`heal_islands`. Removing only that pass reproduces the previously reviewed
rules aggregate `312c3b785ee79e1c441717a760211c035054bb64274c16a5ca4dffd0b20adabb`.
It changes no component, value, net, footprint, board, or topology byte and
therefore does not reopen this review's electrical conclusions.

The final route-contract rebind removes superseded nonexistent `FB_B` from
the recovery group and signal rip list, and expands the switch prep group and
route wave from only `SW_3V3` to the authoritative `SWITCH_POWER` set:
`SW_A`, `SW_B`, `SENSE_A`, `SENSE_B`, `AUX_SW`, and `SW_3V3`. All six exist
on the exact board and retain the established F.Cu, 1.0 mm power geometry;
`FB_B` does not exist there. Reverting exactly those four declarative field
changes reproduces the prior rules aggregate
`41fbbdfa4c9871aa1dbe0e2a057ad28fd3b5fd2758d3007974a1755f544c23e4`.
The direct prep output enumerates all 16 resolved waves exactly. This corrects
route scheduling only and changes no reviewed electrical identity.

# Independent pre-route topology review

## Verdict

No P0/P1 topology, protection, rating, threshold, required-startup, or
source-to-netlist discrepancy remains in the exact hash-bound schematic state.
The design is SOUND to proceed to placement. It is not orderable: placement,
routing, exact-board pin/layout/render/RF reviews, DRC/parity, assembly and
live sourcing, target-firmware integration, first-article qualification, and
the release seal are downstream gates.

## Source and evidence identity re-gate

- The manifest, circuit JSON, KiCad schematic, configured netlist, and current
  schematic source each contain the same 211 design refdes. The configured
  netlist contains 211 components, 151 electrical nets, 708 connected nodes,
  and 57 explicit no-connects. S-COUNT is 4/4 over 211 refdes. E-INV is
  115/115 and E-ADR is 2/2 on this exact netlist.
- J1 is exact Phoenix Contact 1935161 / JLC C3819953. The SHA-selected local
  Phoenix PDF hashes to
  `760ff908523dd6eccff7d1c8accbd8bedce0bf8e57bc1cbe3cc2485c7b98e83a`,
  matching its dossier. It independently states 5.00 mm pitch, 1.0 mm pins,
  1.3 mm finished holes, 10 x 9 mm body, and 17.5 A IEC rating. The exact
  netlist selects `Phoenix_1935161_PT_1p5_2_5p0_H`; the TSX source uses 2.2 mm
  lands and 1.3 mm drills. The prior Kangnex evidence is no longer authority.
- L6 is exact TDK B82477G4333M000 / JLC C2045462. Its local B82477G4 PDF hashes
  to `237d4767bf558f38bdaeffda2cedf203aa5ce3e208bb5c708acf175002f25127`,
  exactly matching the dossier. The selected 33 uH +/-20%, 3.0 A thermal,
  3.5 A saturation, 53 mOhm maximum row and exact TDK footprint are coherent
  with the 0.8 A auxiliary rail.
- The R3 evidence-only update does not alter circuit identity. R3 remains
  exact Vishay TNPW06034K64BEEA / LCSC C2078999, 4.64 kOhm +/-0.1%, 25 ppm/C,
  0603. New local Vishay documents 28758 and 28950 hash exactly to their new
  structured dossier fields (`d4043c24...b3e3` and `9e2b145c...144e`). The
  28758 ordering code independently decodes 4K64/B/E/EA as 4.64 kOhm,
  +/-0.1%, 25 ppm/K and lead-free tape; its current 0.210 W / 100 V general
  ratings exceed the dossier's conservative supplier-listed 0.125 W / 75 V.
  The exact netlist still connects R3 between `OV_SENSE` and GND and E-INV
  still proves the fitted value/tolerance. The revised sourcing note records
  11,128 exact Mouser and 8,323 exact DigiKey units (plus 15 at LCSC) and
  forbids substitution without repeating the OV corner proof.
- The new C2078999 `FETCH-FAILED` twin adjudication is evidence-backed rather
  than an electrical waiver. LCSC's exact product page identifies the same
  MPN and has no EDA-model resource. Vishay 28758 gives a 1.55 x 0.85 mm body;
  Vishay 28950 brackets the installed 0.80 x 0.95 mm pads, 0.85 mm inner gap
  and 2.45 mm overall span between its IPC and IEC 0603 reflow patterns. The
  generic 0603 board model remains only a render witness and the adjudication
  requires JLC first-order placement-preview confirmation. No value, net,
  footprint or board byte changed.

## Input chain, polarity, surge, and thresholds

The exact netlist implements

`J1.1/VIN_RAW -> F1 -> VIN_FUSED -> Q1 -> FET_MID -> Q2 -> VIN_PROTECTED`.

Q1/Q2 are common-drain CSD18533Q5AT devices controlled by LM74810. D1 is the
unidirectional SMBJ24A with cathode/pad 1 on `VIN_PROTECTED` and anode/pad 2
on GND. This protected-side direction blocks reverse input without
forward-biasing the TVS. F1 is the exact 10 A / 32 V Littelfuse fuse in the
Keystone holder; the LM74810 is correctly treated as a reverse/OV disconnect,
not as the sustained-current limiter.

The former incomplete clamp claim is closed by an explicit admitted transient:
50.0 V maximum open-circuit, at least 1.6 ohm Thevenin impedance,
10/1000 us-or-shorter, at most 1 ms, at most 0.01% repetition duty, and 25 C
maximum initial temperature. From SMBJ24A's 26.7 V minimum breakdown, the
maximum source/TVS current is `(50.0-26.7)/1.6 = 14.5625 A`. Pairing that
conservative current with the independent 38.9 V maximum clamp gives 566.5 W,
below the 600 W 10/1000 us rating, subject to the required 5 x 5 mm connected
copper at each terminal.

The LM74810 maximum OV deglitch is 5.4 us. With 36 nC maximum Qg and 168 mA
minimum HGATE sink, discharge adds 0.215 us, so Q2 disconnect is bounded below
5.7 us. The rating domains are now honest: upstream Q1/Q2 see the admitted
50 V ceiling against 60 V ratings, U1 sees 50 V against 65 V, while protected
Q3-Q6/U2/U3 see the 38.9 V clamp against 60/60/65 V recommended maxima.
AP63203 is cascaded behind regulated AUX_6V. No automotive load-dump or
lightning capability is claimed.

The LM74810 divider is `SW/OV_TOP -> 90.9 kOhm -> OV_SENSE -> 4.64 kOhm ->
GND`, with VSNS on VIN_FUSED. Recomputed resistor, threshold, and leakage
corners give 24.345-26.390 V rising: the low corner is above the commissioned
absolute 24.0 V operating ceiling and the high corner is below SMBJ24A's
26.7 V minimum breakdown. The UV divider's documented 10.44-11.51 V rising
range is also compatible with the 12 V input floor.

## Conversion and load margin

- Both LTC3889 channels are 250 kHz synchronous bucks with one 6.8 uH +/-20%
  inductor and one 10 mOhm +/-1% shunt each. At 24 V and the 5.44 uH corner,
  ripple is 3.001 A peak-to-peak and the 4 A load peak is 5.501 A. The required
  15% peak is 6.326 A. The 68/75/82 mV threshold and shunt corners give
  6.733-8.283 A: the low corner clears the requirement and the high corner is
  below 15.2 A Isat; worst shunt dissipation is 0.686 W below its 1 W rating.
  E-SWDRV passes both channels at 28/64 mA gate-plus-bias budget.
- `VOUT_COMMAND=0x14DC` produces the declared 5.183925-5.246075 V bounded rail.
  Each port's complete mated-plug path is 45 mOhm eFuse + 10 mOhm PCB/vias/
  joints + 80 mOhm mated VBUS/GND contacts = 135 mOhm. At 2 A with 20% margin,
  the 324 mV allowance leaves 4.859925 V at the plug. E-MARGIN passes 4/4;
  the high rail corner remains below 5.25 V.
- U9-U12 are exact TPS259470ARPWR devices. Each 1.47 kOhm +/-1% RILM bounds
  current limit to approximately 2.021-2.519 A, guaranteeing 2.0 A while
  remaining below the exact USB1130-15-A connector's 3 A continuous rating.
  The 2.2 nF ITIMER, 3.3 nF DVDT, true reverse blocking, dedicated FLT,
  post-switch voltage sensing, and ILM-without-shunt-cap topology match the
  selected 470A device semantics.
- LMR36510 converts the protected 12-24 V rail to 5.87-6.13 V AUX_6V; AP63203
  then bucks AUX_6V to 3.27-3.33 V logic. E-TOPO passes 6/6 rails. E-OFF is
  correctly N-A because the board has no stored source; removing the external
  SELV feed is the de-energization path.

## Safe startup and control

Hardware defaults are restrictive: Q7/Q8 clamp both LTC RUN pins low until
the MCU releases them, R38-R41 hold all external port commands low, the data
switch controls default isolated, and HUB_RESET_N defaults asserted. The
LTC3889 private VDD33 is isolated and bypassed; ASEL0/ASEL1 are deliberately
open, not grounded.

The exact startup image writes `MFR_ADDRESS=0x4F` through global address 0x5A
before addressed access, writes and reads back 250 kHz, 0/180 degree phase,
`0x14DC`, `0xD280`, `0xCBC0`, forced-CCM/high-current mode, and latched-off
fault responses while RUN remains clamped. It releases RUN only after those
checks and requires both PGOOD inputs. It then releases USB2517 reset, writes
and reads the SMBus image with ports 6-7 disabled and port 5 retained, and
sets USB_ATTACH only last. Every failure reasserts the restrictive state.
The exact C11 host test compiles with `-Wall -Wextra -Werror` and prints
`phub_startup: PASS`.

## Measured gate evidence and remaining order blockers

- D-SPEC/E-PATH: 1/1; E-SWDRV: 2/2 channels; E-SURGE: 1/1 path.
- E-TOPO: 6/6; E-MARGIN: 4/4; E-OFF: N-A external source.
- E-INV: 115/115; E-ADR: 2/2; S-NETMERGE: 150/150 labels and 44/44 pin-map
  assertions on the configured exact netlist.
- This pre-route witness does not approve placement or copper. Routing may not
  begin until the exact placement-phase pin/layout/render/RF evidence is
  current and SOUND. Ordering additionally requires DRC 0/0/0, exact-board
  parity, JLC twin/assembly/BOM/CPL and live stock checks, approved consignment
  or manual-placement records for non-JLC-placeable parts, target HAL/USB
  integration, first-article resistance/thermal/load-step/current-limit/surge/
  USB testing, and the final release seal.

design_verdict: SOUND
order_verdict: DO-NOT-ORDER
