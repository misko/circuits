# SUPERSEDED by v1.0.2-2026-07-16

Do not use this release's twin renders: the Q1 model nudge was applied in
the wrong frame (footprint-local model_dx on a 90deg-rotated part moved
the model NORTH, not east), so twin_top.png still shows Q1 ~0.9mm off its
pads while the MANIFEST claims it seated. Fab files (gerbers/bom/cpl/pdf)
are byte-identical to v1.0 and v1.0.2 and remain valid.

Evidence and the corrected nudge: 03_src/rules/twin_adjudications.yaml
(C400894 entries) and 07_releases/v1.0.2-2026-07-16/.
