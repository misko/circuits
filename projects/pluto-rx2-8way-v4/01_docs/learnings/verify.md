# Learnings — verification and v1.0 seal

## A design-intent fence check is not evidence about the realized board

- what happened: the first final adversarial layout review found two RF fence
  apertures over the 1.1910 mm bound even though the authored route contract
  was believed compliant. The realized board measured 22 sides and two failed.
- root cause: the requirement and nominal via pattern lived in source, while
  no blocking gate measured the saved board geometry that fabrication uses.
- avoid next time: run `fence_pitch.py` on the saved board after refill and
  before field solving or fabrication export. Require complete configured-side
  coverage as well as a passing maximum pitch.
- candidate-canon: no — promoted during this project into the shared PCB skill,
  both rebuild drivers, and a red/green regression fixture (26/26 tests pass).

## A repaired artifact needs every final lens rebound to exact hashes

- what happened: the fence repair changed only two GND vias, but the prior
  final-review verdicts named the pre-repair source commit. Treating them as
  current would have made the evidence ambiguous even though pin-bearing and
  topology artifacts were unchanged.
- root cause: a verdict is about a subject, and a semantic “small change” does
  not itself bind that verdict to the new subject.
- avoid next time: after any P0 repair, run a semantic delta proof plus targeted
  exact-hash rebinds for topology, layout/RF, pin, and render lenses before the
  source/review commit.
- candidate-canon: no — this is already the release contract's fix-pass rule.

## Module-first selection removed an avoidable implementation tree

- what happened: the initial component-level path would have required bare
  RP2040 escape, flash, clock, regulator, carrier USB, and their validation.
  The RP2040-Zero module retained the required control function while moving
  those risks behind a vendor-tested module boundary.
- root cause: component selection had not treated integration complexity as a
  first-class cost when a suitable module existed.
- avoid next time: unless constraints require a discrete implementation,
  prefer an existing module that removes circuitry, layout, firmware bring-up,
  or certification work; still verify its mechanical and power boundary.
- candidate-canon: no — the shared PCB design skill and ADR template were
  already updated during this project.
