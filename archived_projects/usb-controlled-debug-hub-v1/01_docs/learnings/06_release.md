# Release-stage learnings — v0.1.2-2026-08-17

## Connector pin authority must be exact-code evidence

- what happened: the exact Kinghelm USB-A drawing fixed body geometry but did
  not number its four contacts, so an independent pin review could not close
  the risk from convention alone.
- root cause: mechanical drawing authority and electrical pin-number authority
  were treated as though one document necessarily supplied both.
- avoid next time: require an exact-MPN numbered drawing, exact-code catalog
  symbol/footprint pair, or a recorded physical continuity map before routing a
  connector whose manufacturer drawing omits contact numbers.
- candidate-canon: yes — extend connector pin review with a closed hierarchy of
  acceptable exact-code authorities and hash every supplemental artifact.

## Human orientation approval must bind the rendered subject

- what happened: machine edge/mouth geometry passed, but release still needed
  an explicit product-owner decision for cable approach and visible keying.
- root cause: numerical placement correctness cannot decide whether the chosen
  physical interface direction matches user intent.
- avoid next time: generate representative outboard/inside/top views at the
  placement gate, hash one orientation subject, request approval once, and
  invalidate that approval automatically on board or subject drift.
- candidate-canon: yes — this board exercised the new exact-subject connector
  review pattern successfully; make it the default for edge connectors.

## Dynamic schema access hides real consumers

- what happened: `candidate_grade`, `ownership_preflight`, and
  `exploration_guard` were genuinely consumed by the routing wrapper but the
  schema-reader audit reported them unread because their paths were assembled
  dynamically.
- root cause: the checker deliberately proves literal AST read paths and cannot
  authenticate an f-string key without weakening its method.
- avoid next time: call the shared normalizer with values obtained through
  explicit literal `get(cfg, "route.<key>")` reads; update contract rows and
  pinned governance denominators in the same change.
- candidate-canon: yes — explicit source-schema reads are now implemented and
  regression-tested; retain this as the pattern for future generic controls.

## First-article policy belongs in source before sealing

- what happened: the design had detailed bring-up prose but no machine card
  binding the complete population, exposed pads, probes, resistance windows,
  rail limits and bench current limit.
- root cause: fabrication verification and physical authorization were treated
  as one stage, leaving no executable boundary between a correct archive and a
  safe first power attempt.
- avoid next time: create `first_article.yaml` during power-tree review, verify
  exact installed-set equality against CPL plus manual parts, and allow a
  release to seal while the physical record remains explicitly INCOMPLETE.
- candidate-canon: yes — adopt the card at design stage for every powered board;
  never synthesize measurements or let an incomplete card authorize power.

## Design release and order authorization are separate verdicts

- what happened: all design reviews were SOUND while JLC-specific stackup,
  impedance, via-process and uploader previews necessarily remained unavailable
  locally.
- root cause: a single release/order verdict encourages either premature order
  approval or indefinite refusal to preserve a correct design artifact.
- avoid next time: seal `DESIGN: PASS` independently, retain `DO-NOT-ORDER` on
  the first screen, and enumerate every order-time evidence item with a STOP
  condition.
- candidate-canon: yes — keep the existing two-verdict release model and add a
  regression that a design-pass/order-hold archive remains freshness-valid.
