review_kind: render_review
subject: Pluto RX2 8-Way v5 corrected exact routed final board dae8320d
date: 2026-08-13
reviewer: Codex fresh independent final render/mechanical/copper reviewer
independence: independent-from-design-author
context-given: exact corrected board, native 3D models, copper plots, and current manufacturing rules
source_commit: dae8320d3a5bab507a5846c7886ea719dc05ef61
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Corrected exact-artifact final render review

## Verdict and independence

The exact corrected board identified above is **SOUND** through the physical,
render, model, connector-access, mounting, copper-presentation and assembly-
visibility lenses. I regenerated all views from the saved board with KiCad
10.0.4 and did not reuse the earlier `44aad7a7` visual verdict. P0/P1/P2
design findings: **0/0/0**.

The order verdict is **DO-NOT-ORDER**. This render review is not a fabrication-
package, sourcing, assembly-contract or order-uploader acceptance. In
particular, the current prose identifies J2-J10 as wave-or-controlled-hand-
solder items, but the bought through-hole process still needs the pipeline's
machine-readable declaration and evidence before release.

## Fresh evidence binding

| Fresh evidence | SHA-256 / result |
|---|---|
| top render | `4440273f0b8314fee9e075d4836a24eeb20a77d1bfcbcdd58655782c32268f74` |
| isometric render | `c10d114bde205f9370fcec9c031ef2913ac2c0a8dd126f4e67f5fda9ee73f6f7` |
| front render | `cd56434e6e03ccc3a2439099514ee4c67a85320e5d8ef496f23d6e00e07fde9a` |
| right render | `aa0d760674649d0d93b3657e3a3fb1640e5a2eb6079c9637e52fdf5ea2420c30` |
| bottom render | `bab6643b9168c1d132dbfb5628725f489e5ea4ff23791cea91acd7058344b38c` |
| F.Cu / B.Cu raster plots | `29d93b431170f2604e1f571f59434c02a56ea8cc3e15519f6ce22e831d613756` / `efcaeed71973e19002af003b6580b723dac5e89e9d123e805cc321496fbb6f90` |
| In1.Cu / In2.Cu raster plots | `2af0b9d88a082c185b58f234f7403a8498a69657a383fef9e66a1bfbff48039b` / `2af0b9d88a082c185b58f234f7403a8498a69657a383fef9e66a1bfbff48039b` |
| fitted-model coverage | 29/29 renderer-resolvable bodies; zero missing |
| exact-board KiCad DRC | 0 violations / 0 unconnected / 0 schematic-parity discrepancies |

## Population, orientation and physical access

- All 29 fitted bodies are present and seated on their footprints. U1-U4,
  D1, F1, R1-R6, C1-C6, J1-J11 and the nine SMA bodies show no visible
  reversal, shift, float, board-side error or body-to-body collision. U1 and
  U2 pin-one marks, D1 polarity, and the fine-pitch lands are visibly
  registered.
- The five north-edge SMAs and two connectors on each side face outward. The
  15 mm north pitch and 18 mm side pitch provide clear barrel, mating and
  coupling-nut access. Their manufacturer-pattern legs align with the plated
  holes. Normal through-hole tails remain below the PCB, so the enclosure or
  standoffs must allow post-solder lead clearance.
- J1 is centered at the south edge with an unobstructed USB-C insertion path.
  J11 is a real keyed vertical 2x5 Cortex-SWD connector rather than exposed
  pads; its mating volume, pin-one side and cable approach remain open.
- The 90 x 65 mm outline and all four 3.2 mm corner mounting holes are clear.
  Screw/head and driver access are not hidden by an SMA body. Three global top
  fiducials are visible and unobstructed.

## Copper, return fence and presentation

- Fresh F.Cu inspection shows all nine intended 0.295 mm direct RF routes as
  continuous, via-free, non-crossing arms. The B.Cu fragments are confined to
  low-speed control/debug routing. In1.Cu and In2.Cu each plot as a continuous
  GND plane without a signal route or split beneath an RF arm.
- A fresh route-aware fence audit, excluding accidental credit from the coarse
  board-wide stitch lattice, passes all 18 RF flanks. The worst along-route
  aperture is 1.3979 mm against the 1.4000 mm limit. The dense fence reads as
  deliberate RF containment and neither blocks an opening nor conceals an
  operational marking.
- `PLUTO RX`, `ANT1`-`ANT8`, `100MHz-5.9GHz`, `USB-C POWER ONLY`, and
  `KEYED SWD J11` remain readable and truthful with bodies fitted. No user-
  facing port identity or polarity cue is lost.
- The corrected J11.3 area contains only its deliberate dogbone/plane drop;
  no ordinary stitch via remains inside the SMD land. The only visible via-in-
  pad construction is the deliberate 3x3 U1 exposed-pad field.

No physical-fit, component-orientation, connector-access, mounting/tool-space,
model-coverage, operational-silk, RF-fence or rendered-copper defect was
found. Any change to the board, model transforms, connector part choice or
via process invalidates this hash-bound review.
