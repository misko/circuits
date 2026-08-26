# Pre-route topology review — Pi USB port switch

review_stage: pre-route
review_kind: topology
design_verdict: SOUND
netlist_sha256: 529988394f74bcb6a8f292e0a16d610ff8140f240ce9c0122af9966d4a1e0992
parts_sha256: 9f07c5382cde77e74e0f5f0c7c8396b62a9678f2a1e090422b2ac5f3d0379683
design_rules_sha256: 8bd0fe7492a4ae67bf266d9840e25c14eee8f1bda228593f36cebd87fcf97b71

## Review basis

This review used the exported KiCad netlist as the electrical source, with the
brief, ADRs, part dossiers, power tree, protection paths, requirements, and
electrical-invariant contract as independent interpretation aids.  The TSX
presentation was not used as the authority for connectivity.

Coverage reviewed:

- 190/190 manifest components represented in the circuit model, KiCad
  schematic, and exported netlist;
- 316/316 declared pin mappings and 163/163 protected labels survive
  into the netlist;
- 282/282 executable electrical assertions pass;
- all four inline channels are one-to-one paths; there is no hub or shared USB
  data fabric.

## Findings

- Upstream Type-B VBUS pins are deliberately unconnected, so the board cannot
  back-power the Raspberry Pi through a USB cable.  Connector grounds and
  shields join the board reference as documented.
- External 5 V enters through the fused, reverse-polarity-protected input path,
  then feeds the four independent TPS2557 current-limited VBUS switches.  Each
  downstream Type-A VBUS is controlled by its own power-enable signal.
- Each channel implements the required hardware interlock:
  `DATA_OK[n] = PWR_EN[n] AND DATA_EN[n]`.  `DATA_OK[n]` enables the TUSB522
  redriver and controls the TS3USB221 USB 2 disconnect path.  The TS3USB221
  select input is fixed to the intended path; its normally-high OE is pulled
  low only by the corresponding interlock FET.
- USB 2 D+/D- remain a matched logical pair through each TS3USB221.  Each
  SuperSpeed channel contains four directionally correct lanes, connector-side
  ESD, 2.2-ohm series damping, explicit AC coupling, and one TUSB522 redriver.
  The 100 nF TX-side and 330 nF RX-side capacitor assignments and the 220 kohm
  RX2 bias straps match the declared topology.
- Each upstream and downstream connector has its own TPD6E05U06 ESD array at
  the connector boundary.  No cross-channel data net or unintended shared
  switched-VBUS node was found.
- The six TPD6E05U06 signal clamps are independent, equivalent channels. Their
  protected I/O pins follow each connector's physical lane order. TI SLVSBO7O
  Table 4-3 identifies pins 1--4, 6 and 7 as internally NC but explicitly
  usable for optional straight-through routing; Figure 7-11 shows the PCB
  copper continuing through those lands. Each opposite NC land is therefore
  assigned to the same external net as its protected I/O partner. The exported
  netlist proves all 48 I/O/NC flow-through pairs, all named P/N endpoints, and
  no end-to-end polarity swap or cross-channel join. Leaving these lands on
  generated unconnected nets would contradict TI's intended flow-through
  layout and would force avoidable ESD stubs or package detours.
- The physical-layout dossiers were re-bound after refining only placement
  semantics: connector-to-redriver distance is correctly treated as a routed
  multi-segment constraint across series parts, and the six-line ESD array's
  connector adjacency is now a measurable geometry allocation.  Neither
  refinement changes the reviewed component, pin, or net topology.
- The regenerated netlist has 220 electrical nets after the 48 formerly
  generated TPD6 NC nets were deliberately merged into their corresponding
  protected signal nets. Component count remains 190; 316 pin-map assertions,
  163 label-survival checks, and all 282 invariants pass.
- The commissioned routing contract inventories 48 SuperSpeed and eight USB 2
  differential segments independently (56 physical pairs, 112 nets). Every
  row binds P/N polarity, differential-wave membership, allowed layers, via
  policy, and realized pair matching. Core and TX paths remain F.Cu/zero-via;
  connector RX paths may use a short matched B.Cu crossover between paired
  transitions because the connector and TUSB522 lane groups have opposite
  physical order. Both outer layers have an adjacent continuous ground plane
  in the symmetric stackup. The retained coated
  finite-difference solve for JLC04161H-7628 gives 89.53 ohm at 0.25 mm width
  and 0.18 mm gap (0.004 mm grid); JLC's order calculator and process echo
  remain required before payment.
- RF-module applicability is explicitly false because this board has no RF
  port, phase-coherent network, antenna path, or single-ended via-fenced
  transmission line.  USB is instead governed by the dedicated differential
  pair contract above; treating those pairs as the RF module's single-ended
  route banks would be false evidence, not an additional safety check.
- The 40-pin Raspberry Pi header uses direct 3.3 V GPIO controls and common
  ground.  No firmware artifact is part of this hardware release.
- Assembly intent does not alter topology. Live JLC requalification found the
  exact upstream Wurth 692221030100 as C5334230; its numbering-free pad-cloud
  fit agrees with the manufacturer land to 0.0039 mm. J3/J5/J7/J9 therefore
  remain in the bought JLC through-hole process alongside J1/J2. The four
  Type-A outputs J4/J6/J8/J10 remain hand-soldered because no exact JLC line
  was found, and F1 remains hand-soldered because one centroid cannot represent
  its two separate Keystone clips. None of these population choices changes a
  pin, net, or electrical invariant.
- The current regenerated artifact was rechecked after tightening component
  adjacency limits, thermal-via requirements, and schematic pin spacing. Those
  changes preserve the normalized 220-net electrical graph: 282/282
  invariants, 163/163 protected labels, 316/316 pin mappings, and all five
  power-rail topology checks still pass, with zero ERC errors.

## Boundaries carried forward

`SOUND` means the source topology is internally consistent and suitable for
placement and controlled layer-transition routing. It does not claim USB-IF compliance or a production-qualified
5 Gbit/s link.  Exact JLC04161H-7628 impedance geometry, connector-to-ESD
placement, differential-pair skew, discontinuities, return paths, and the full
power-current geometry must be proved on the realized PCB.  The first article
must be electrically and link-qualified before this fixture is trusted for
USB 3 debugging.  The 89.53-ohm local solve is source evidence, not a claim
that JLC has accepted the selected stackup or that the realized routes pass.
