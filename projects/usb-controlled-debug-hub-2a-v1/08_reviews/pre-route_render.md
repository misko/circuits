# Pre-route render review

review_stage: pre-route
review_kind: render
reviewer: Codex primary agent, exact manufacturing-twin readability lens
context_given: full project context; this is not a fresh-context independent review
reviewed_on: 2026-08-20
board_sha256: d3e032a75148cc7dc2139052c029def5a81bab6926680ea8f3c1b1458ee59da4
design_rules_sha256: fcf6878c8b9f0f078e829788ab3a408dbdf7ac25844ac0e1b78a57707b22e497
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

## Exact evidence

- twin report SHA-256:
  `2d08ea23b3ae73e8c072c27952afa835971c06c38047bbb49739944b808514a3`
- connector datum receipt SHA-256:
  `4afb049bb7b99548ad874e9c4fc50c85871c2d7a42941705fc539068fdf30562`
- native model-registration report SHA-256:
  `6f0b5b2ce95cc756cd83622b603d9db2c754b1f96e8c05c791f8e8209b6222ca`
- top A-RENDER report SHA-256:
  `c6ef9027045b27df98877059f03d58142be488877266e144a67e5951ee3dbc80`
- bottom A-RENDER report SHA-256:
  `7a6f7cdf0ac5121f13b9b582d66695d73c5b0db95909cc13f57dba1ccbd7f6cc`

## Scope and result

The exact placement subject was regenerated after source-owned thermal and
ground-dogbone changes.  They do not alter body placement or model transforms;
the model-registration and connector-orientation subjects remain unchanged.
The A-RENDER report is nevertheless regenerated and hash-bound below rather
than inheriting its earlier board digest.

The exact top, bottom, isometric, edge, bare-board, and courtyard-overlay
views were inspected. Every fitted body is present: 183/183 model coverage.
The top populated-minus-bare comparison passes with 42/174 expected top-side
bodies pixel-measurable, all remaining 132 explicitly below the render's
resolution floor, zero resolvable bodies missed, and zero expected bodies
without a model. The bottom comparison passes 9/9. No measured body exceeds
the 1.00 mm centre/outward tolerance.

All four manual GCT USB-A connectors are now inside the A-RENDER denominator,
not silently omitted. Their measured centre deltas are 0.148..0.217 mm and
their outward excursions are 0.080 mm. J_DATA and J_POWER use the exact
native HRO model, and measure 0.167 mm and 0.128 mm centre delta respectively.
This closes the known failure mode where an electrically correct connector
can be shown with a displaced catalog body.

The two MWSA0804S inductors intentionally use Sunlord's exact recommended
land rather than JLC's narrower/shifted library land. The manufacturer-backed
PAD-MISMATCH and PAD-GEOM dispositions are explicit; the JLC body remains a
visual aid and is not authority for fabricated copper. Repeated exposed-pad
PAD-MULTIPLICITY notes for U_HUB, U_PWR_CTRL, and D_PD_TVS are numbering
representation differences, not missing copper.

The rendered functional organization is judgeable: four output mouths along
the north edge; upstream data and PD power on the west edge; the south power
row is visibly separated from the hub/control island. No body overlaps a
foreign courtyard in the overlay. Silkscreen is intentionally preliminary;
final route, zone, polarity, assembly, and functional-silkscreen reviews are
still required on the routed candidate.

## Findings and boundary

- P0: none.
- P1: none.
- P2: many 0402/0603 bodies are below the current full-board pixel-resolution
  floor. They are named as unmeasurable rather than credited; final assembly
  review must use CPL/component-level evidence for rotation and polarity.
- P2: the review was performed by the active primary agent. Fresh-context
  final render/layout review remains mandatory before release.
- Human connector orientation is a separate hash-bound gate and remains
  pending; this render verdict does not stand in for that approval.
