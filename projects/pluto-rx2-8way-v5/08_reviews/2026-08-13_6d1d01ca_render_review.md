review_kind: render_review
subject: Pluto RX2 8-Way v5 assembly-contract renewal at 6d1d01ca
date: 2026-08-13
reviewer: Codex fresh independent final render/mechanical/copper reviewer
independence: independent-from-design-author
context-given: exact commit board, native 3D models, fresh copper plots, and exact assembly source
source_commit: 6d1d01cabb06301646136c6f729a027d8235160e
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0
review_status: historical-superseded-before-seal

# Fresh physical and render renewal

## Verdict and exact boundary

The exact board bound above is **SOUND** through the render, physical-fit,
orientation, mating-access, mounting, copper-presentation and assembly-
visibility lenses. P0/P1/P2 design findings: **0/0/0**. I regenerated every
view from the saved board with KiCad 10.0.4 and independently reopened them at
their original resolution. The board is byte-unchanged from the corrected
`dae8320d` artifact, but this review did not inherit its earlier visual
verdict.

This review is historical rather than seal-final because a later evidence-
only source commit was planned before seal. The order verdict is
**DO-NOT-ORDER**: no sealed release, order-uploader echo or exact fabrication-
package acceptance exists at this commit.

## Fresh render and copper evidence

| Evidence | SHA-256 / result |
|---|---|
| top render | `f188547ad525ab230bec4805c222e50c74f64f780139e31d24b4af1925f5bd17` |
| isometric render | `83b34536dc56ebd8c8a5c5efc4c5e95cdacd3b908e0fec383fb33a7536814791` |
| front render | `6d447624ed9e95a4a9a6c0947839cc482a983a573db6789d057364b8db0d8337` |
| right render | `c0985c5fceacef7236085cd0893e81dae7e4b63d4efc7b63693b7911847d7470` |
| bottom render | `1ea62a9b3c93680320abeaa6ef579d31317edb1ee1b49c1bb1f45e100c498d8b` |
| F.Cu / B.Cu raster plots | `9c9125d0556d313f4ba66fba01e539646b1162d87361929a52f8a52ed048a008` / `1790f73030df31d7679a230635483bdbb69ccb695b6f04e6642158612b54f710` |
| In1.Cu / In2.Cu raster plots | `1b60f1cb287093fcaa61a487b00d1dbe7ffbbe1af90b89afd7211d0aa8c618d8` / `1b60f1cb287093fcaa61a487b00d1dbe7ffbbe1af90b89afd7211d0aa8c618d8` |
| renderer-resolvable population | 29/29 fitted bodies; zero missing |
| exact-board DRC | 0 violations / 0 unconnected / 0 schematic-parity discrepancies |

## Population, orientation and access

- U1-U4, D1, F1, R1-R6, C1-C6, J1-J11 and all nine SMA bodies are present,
  seated on their lands and on the intended top side. No body is reversed,
  shifted, floating or visibly colliding. U1/U2 pin-one and D1 polarity marks
  register with their footprint cues.
- Five north-edge and two-per-side SMA connectors face outward. Their 15 mm
  north pitch and 18 mm side pitch leave practical barrel, mating and coupling-
  nut access. All five manufacturer-pattern legs register with their drilled
  lands; the ordinary tails visible below the board require normal post-solder
  trimming and enclosure/standoff clearance.
- The south-edge USB-C opening is unobstructed. J11 is a real keyed vertical
  2x5 Cortex-SWD connector with clear cable approach, not exposed programming
  pads. The 90 x 65 mm outline, four 3.2 mm corner holes and three top
  fiducials remain clear of bodies and tool approaches.
- Operational silk remains readable and truthful with components fitted:
  `PLUTO RX`, `ANT1`-`ANT8`, `100MHz-5.9GHz`, `USB-C POWER ONLY`, and
  `KEYED SWD J11` are not hidden or assigned to the wrong port.

## Copper presentation and corrected process geometry

- F.Cu shows nine continuous, via-free 0.295 mm RF arms with no crossover or
  unintended branch. B.Cu contains only short low-speed fragments. In1.Cu and
  In2.Cu each remain continuous GND planes with no signal route or return-plane
  split beneath the RF fanout.
- All 18 route-local fence flanks pass the exact audit; worst aperture is
  1.3979 mm against the 1.4000 mm bound. The fence reads as deliberate RF
  containment and neither blocks a connector nor hides a functional label.
- J11.3 remains free of the rejected ordinary via-in-pad. The only via-in-pad
  geometry is U1's deliberate 3x3 protected exposed-pad field. Fresh process
  grading finds nine 0.45/0.25 mm filled/capped vias and 629 ordinary
  0.45/0.20 mm untreated vias.

## J2-J10 assembly ownership renewal

The prior source omission is closed at this commit. `assembly.yaml` now has a
machine-readable `through_hole:` block with a substantive purchased JLCPCB
wave/manual process, the exact denominator J2-J10, and dated catalog/process
evidence. A fresh 29-placement candidate CPL plus the generated empty
`not_assembled:` manifest passes A-POP with all 29 placement datums graded and
0.00050 mm worst error. There are zero THT-placeability findings.

That declaration intentionally does not manufacture evidence that only the
real uploader can provide. Exact C429844 must be echoed as accepted wave/manual
assembly for all nine refs. Refusal is a hard stop for this release and requires
a distinct hand-solder release with J2-J10 removed from its CPL; silently
dropping the connectors is forbidden.

No physical-fit, orientation, access, mounting, model, silk, RF-fence or
rendered-copper defect was found. Before ordering, regenerate and review the
actual release renders/package and confirm the connector process, rotations,
controlled-impedance stack and selective via process in the JLC interface.
