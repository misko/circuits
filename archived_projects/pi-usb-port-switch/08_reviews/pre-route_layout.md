subject: pi-usb-port-switch exact pre-route placed board
date: 2026-08-15
reviewer: Codex layout/power/SI feasibility review
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: 168838f8e57b16581a8f54cdd4b75a85d1d5dbb1698428d281a7c07dccf14101
design_rules_sha256: 8bd0fe7492a4ae67bf266d9840e25c14eee8f1bda228593f36cebd87fcf97b71
floorplan_sha256: eb365ba89b7be910e624099b775d13c76e5d5785f4d570f5222c306e19112cd0
route_yaml_sha256: e7c5f2f8d67783669216edd6c8790ea5153658cb7f4fa30b2a2a084d291f99d8
prepared_r0_sha256: d53053d1621657d5abee6a2dd835c8f6f450c177e6bc8ddcc1cb2277cefa785d
placement_drc_sha256: 3897e4e3a61f8d7cf4d3a08fc702efc0d1a8f0abeda0c85f62df1096ef4122e6
model_coverage_sha256: dadcfb7128349912e1831cf6f4af02b76bbc138055ca310aa29231871e60340b

# Pre-route layout and feasibility review

## Verdict

No P0 or P1 placement, access, land-escape, package-clearance, power-flow, or
critical-corridor defect was found on the exact board. The placement is
**SOUND to proceed to routing**, subject to the explicit preservation
conditions below. This board is still unrouted and is not orderable.

## Functional floorplan

- The 150 x 120 mm board reads as four repeated west-to-east channels. Four
  upstream USB 3 Type-B receptacles face outward on the west edge and four
  downstream USB 3 Type-A receptacles face outward on the east edge. Their
  cable approaches do not cross the component field or mounting-hole access.
- Each channel places connector-side ESD protection next to its receptacle,
  the TUSB522 in the broad central pair corridor, the TS3USB221E and hardware
  interlock in the control corridor, and the TPS2557 plus output bulk capacitor
  next to the downstream VBUS destination. The four rows are separated enough
  to route and inspect independently.
- The separate 5 V terminal, removable mini-blade fuse holder, reverse-polarity
  MOSFET, input bulk capacitor, 3V3 regulator, and GPIO header remain accessible
  from above. The fuse extraction envelope and terminal screwdriver approach
  are unobstructed.
- The four upstream Type-B receptacles J3/J5/J7/J9 use exact catalog code
  C5334230 and remain in the CPL for JLC through-hole assembly. The four
  downstream Type-A receptacles J4/J6/J8/J10 and the two-clip fuse holder remain
  mechanically fitted but deliberately outside JLC's CPL. Their native
  exclusion flags agree with `assembly.yaml`; they are installed and inspected
  after PCBA rather than represented by an invented catalog code or an invalid
  shared centroid.

## Placement and manufacturing gates

- P-OUT/P-CAP/P-BODYCLR: **PASS** with 0 failures and 0 warnings. Tightest
  pad-to-outline margin is 0.69 mm. The worst corridor cut demands 40 nets
  against an estimated 484 two-layer tracks. All 190 assembled envelopes have
  no overlap/close pair and no envelope-to-foreign-pad finding at the 0.10 mm
  search floor.
- P-PADSEP: **PASS** at the 0.09 mm JLC four-layer advanced floor: 800 copper
  pads on 197 footprints, 313,042 inter-footprint pad pairs, and 490,231
  paste-to-foreign-copper comparisons graded without failure.
- Placement policy: **PASS=5**. All 9/9 measurable keep-short budgets, 16/16
  adjacency budgets, and 25/25 declared budgets resolve and pass. Local
  redriver bypass, USB-switch bypass, logic bypass, current-limit resistors,
  and connector-side ESD placement are therefore machine-bounded rather than
  inferred from appearance.
- P-LAND: **PASS**, 485 width-constrained lands graded, including 232 supplied
  by a same-net pour, with zero unreachable or failing lands.
- Tier preflight: **PASS**, 0 failures and 0 warnings for
  `jlc_4layer_advanced`.
- Model coverage: **PASS**, all 190/190 fitted electrical footprints resolve a
  nonempty 3D body in the declared headless render environment.

## Power and signal-integrity feasibility

- The authored input copper follows J1 -> F1 -> Q1 -> protected 5 V. A broad
  B.Cu protected-5-V trunk and four local port islands reserve the all-ports
  0.9 A distribution path. The two pre-route `isolated_copper` reports are
  intentionally unbonded B.Cu protected-5-V pours; deterministic power
  vias/taps must connect them during routing. They are allowed only at this
  checkpoint.
- U1's filled/capped output-tab vias terminate in a local B.Cu 3V3 heat
  spreader; this removed the two earlier dangling-via findings without a
  waiver. The exact refilled pre-route DRC classifies 2/2 remaining findings as
  the two allowed protected-5-V isolated copper zones, observes 353 expected
  unrouted connections and zero
  schematic-parity findings. No clearance, short, hole, edge, or library
  violation is being waived.
- All 56 differential pairs have explicit allowed-layer and via contracts.
  Core, TX, and USB2 paths remain F.Cu/zero-via. The eight connector RX pairs
  alone use short, matched B.Cu crossovers between paired signal transitions,
  with nearby GND return vias. The selected JLC04161H-7628 local field solve
  gives 89.53 ohm differential for 0.25 mm width / 0.18 mm gap. This is a
  design input, not order credit: the JLC impedance calculator/stackup echo
  and production preview must confirm it.
- In1.Cu must remain continuous GND below all F.Cu USB routing, and In2.Cu
  must remain continuous GND above the contracted B.Cu RX crossovers. Every
  signal-layer transition must retain its explicit nearby GND return via.
  Pair geometry must preserve P/N order, coupled length, phase matching,
  spacing from other pairs and copper, and no stubs. USB 3 remains a
  first-article qualification target rather than a USB-IF compliance claim.

## Routing obligations

The routed board must connect the protected-5-V trunk with current-capable via
banks, complete each TPS2557 output/VBUS path, close all signal/control nets,
and leave zero unrouted or isolated copper. The 56 critical pairs must pass the
connected-route, impedance, length/mismatch, uncoupled-length, return-plane,
and contracted layer/via-policy checks. Final DRC/parity, thermal/current, JLC upload, assembly,
rotation, digital-twin, and first-article evidence are all still required.
