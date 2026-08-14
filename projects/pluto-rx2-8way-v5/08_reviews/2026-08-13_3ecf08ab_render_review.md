review_kind: render_review
subject: Pluto RX2 8-Way v5 final exact source and board 3ecf08ab
date: 2026-08-13
reviewer: Codex fresh independent final render/mechanical/copper reviewer
independence: independent-from-design-author
context-given: exact final source commit, native 3D models, fresh copper plots, exact assembly contract and current manufacturer evidence
source_commit: 3ecf08abe5f44c098144abfc8cea31fc89354c59
board_sha256: 39251c24d4b3cc878824f26c48178cbc4a4d418fa528045c6c13f2308e017acd
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Final fresh physical and render review

## Verdict and exact boundary

The exact source/board pair identified above is **SOUND** through render,
physical-fit, orientation, mating-access, mounting, copper-presentation and
assembly-visibility review. P0/P1/P2 design findings: **0/0/0**. Every view
and copper plot was regenerated after the final commit with KiCad 10.0.4 and
independently reopened at its original resolution; no earlier visual verdict
was reused.

The order verdict is **DO-NOT-ORDER**. This design review is permission to
advance into release/fabrication-package work, not evidence that the external
JLC order interface or an as-built article has passed.

## Fresh render and copper evidence

| Evidence | SHA-256 / result |
|---|---|
| top render | `f5587d24772bc78fae8fb47fe772527316df4b7736387e062e2291687e5824b1` |
| isometric render | `47750832c01f1518fca4246c049fa1617054b205b61d956a84b8be106428184a` |
| front render | `bf2752115da3dacdfed877ad7b69ea1c9407f26ad996e4cce7c4417364b410a8` |
| right render | `bed339756d726a95ced5155c98a50b119a63b2c8758c74d2293c03664cdc127d` |
| bottom render | `b1c6029fdf0fb4af8d69397073973e7de510e8724210190866de1f3a9cbfffeb` |
| F.Cu / B.Cu raster plots | `9c9125d0556d313f4ba66fba01e539646b1162d87361929a52f8a52ed048a008` / `1790f73030df31d7679a230635483bdbb69ccb695b6f04e6642158612b54f710` |
| In1.Cu / In2.Cu raster plots | `1b60f1cb287093fcaa61a487b00d1dbe7ffbbe1af90b89afd7211d0aa8c618d8` / `1b60f1cb287093fcaa61a487b00d1dbe7ffbbe1af90b89afd7211d0aa8c618d8` |
| fitted-model coverage | 29/29 renderer-resolvable bodies; zero missing |
| exact-board DRC | 0 violations / 0 unconnected / 0 schematic-parity discrepancies |

## Population, orientation and access

- All 29 fitted bodies are seated on their intended top-side lands. U1/U2
  pin-one cues and D1 polarity align with footprint marks. No component is
  visibly reversed, shifted, floating, on the wrong side or colliding.
- Five north-edge and two-per-side SMA connectors face outward. The 15 mm
  north pitch and 18 mm side pitch provide usable mating and coupling-nut
  access. Their manufacturer-pattern legs align with all plated holes; normal
  THT tails below the PCB require ordinary trimming and standoff/enclosure
  clearance.
- The south-edge USB-C insertion path is clear. J11 is a real keyed vertical
  2x5 Cortex-SWD connector with an unobstructed cable approach, not bare pads.
  All four 3.2 mm corner holes and three top fiducials remain accessible.
- `PLUTO RX`, `ANT1`-`ANT8`, `100MHz-5.9GHz`, `USB-C POWER ONLY`, and
  `KEYED SWD J11` remain readable, correctly associated and unhidden with the
  population fitted.

## Copper, fence and corrected process geometry

- Fresh F.Cu inspection shows nine continuous, via-free 0.295 mm RF arms with
  no crossover or unintended branch. B.Cu contains only short low-speed
  fragments. In1.Cu and In2.Cu each remain continuous GND reference planes
  without a signal route or split beneath the RF fanout.
- All 18 exact route-local RF fence flanks pass, with 1.3979 mm worst aperture
  against the 1.4000 mm limit. The dense fence reads as deliberate RF
  containment and does not block a connector or hide an operational marking.
- J11.3 remains free of the rejected ordinary via-in-pad. The only via-in-pad
  construction is U1's intended nine-site protected exposed-pad field. Fresh
  process grading reports nine filled/capped 0.45/0.25 mm sites and 629
  untreated ordinary 0.45/0.20 mm vias.

## Assembly ownership and evidence closure

`assembly.yaml` contains a machine-readable bought-THT process with exact
J2-J10 refs and dated evidence. A fresh 29-placement candidate CPL plus the
generated empty population manifest passes A-POP; all 29 position datums are
graded and the worst error is 0.00050 mm. Exact C429844 still requires the
real uploader's wave/manual-assembly echo. Refusal is a hard stop and requires
a separately generated hand-solder release with J2-J10 removed from its CPL.

The final findings ledger closes the source-document lifecycle issue against
the official local ST DS13866 Rev 5 digest and the retained Amphenol evidence.
That source/governance-only closure does not alter the board or any physical
observation above.

No physical-fit, orientation, connector-access, mounting, model, silk,
RF-fence or rendered-copper defect was found. Actual release renders, sourced
rotations, fabrication outputs, JLC previews and first-article inspection
remain later order/acceptance evidence.
