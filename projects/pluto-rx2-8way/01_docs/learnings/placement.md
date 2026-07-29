# learnings — pluto-rx2-8way stage 5 (footprints + placement)

## A claim written where the measurement belongs reads exactly like the measurement
- what happened: `03_src/floorplan.yaml` stated "The NINE stock KiCad lands this
  board also uses were re-verified against their vendor land drawings at stage 5
  (independent re-measure, not a re-read of the dossiers): 2 exact MATCH, 3
  MATCH-WITH-IPC-EXPANSION, 3 with no vendor land published at all, and ONE
  mismatch ... and the numbers are in 02_parts/README.md". **The record did not
  exist in 02_parts/README.md or anywhere else.** When the comparison was
  actually performed the tally was 2 / **5** / 3 / 1 over **ELEVEN** lands, and
  the one mismatch had a fourth delta the claim omitted (SOT-223 displaces the
  pad row centre C 6.10 -> 6.30) which falsifies the claim's own conclusion that
  "every delta adds copper".
- root cause: the claim was written in the same commit as the intent to measure,
  in a file that no gate reads for truth. Every downstream reader — including
  the next agent on the same board — treats a specific-looking number in a
  source comment as evidence. Nothing distinguishes "measured 2 exact MATCH"
  from "expect 2 exact MATCH". The pointer to another file made it worse, not
  better: it looked like a citation.
- avoid next time: a comment may cite a record but may never BE the record. If a
  comment says "the numbers are in X", X must contain them at the moment the
  comment is written, in the same commit. Concretely: the footprint-land
  comparison has no gate, so the only durable home is a numbered deviation in
  `02_parts/README.md` with per-part pitch/span/size, and the floorplan comment
  should be a one-line pointer with no tally in it at all.
- candidate-canon: yes — a check that greps `03_src/*.yaml` comments for
  "the numbers are in <path>" / "recorded in <path>" and fails if the path does
  not exist or does not mention the subject. Cheap, and it catches the whole
  class (this board also carried "0.485 mm mouth overhang" against a gate that
  prints 0.535).

## A waiver can be MORE wrong than the gate it waives, and nothing re-checks it
- what happened: `policy_waivers.yaml` recorded RP2040's `DVDD_1V1` keep_short
  budget as "fixed rather than waived ... MEASURED 8.84 mm on the placed board
  (U_MCU.23 to C_MCU8.1)" and therefore PASSING. Re-measured off the board, the
  net has SIX pads (`C_VREG_OUT.1` was omitted) and the worst pair is
  U_MCU.23 -> C_VREG_OUT.1 = **13.167 mm** against a 10 mm budget. P-ADJ had
  been reporting it as EXCEEDED the whole time; the waiver, not the gate, was
  wrong — and because P-ADJ was already WAIVED for two other budgets, the third
  exceedance was invisible in the summary line.
- root cause: two mechanisms compounding. (1) The waiver author measured a pad
  pair they CHOSE instead of reproducing the pair the gate measures — a
  hand-measurement of a different quantity, reported as if it were the gate's.
  (2) `policy_audit` collapses a whole check to one WAIVED row, so a waiver
  written against two findings silently absorbs a third that appears later.
- avoid next time: a waiver that quotes a number must quote the number the GATE
  printed, verbatim, including its units and which pads it names — and if the
  waiver's own reasoning needs a different measurement, both go in, labelled.
  Never write "now graded and PASSING" inside a waiver: if it passes it does not
  need a waiver, and that sentence is the tell.
- candidate-canon: yes — `waiver_provenance` should additionally check that every
  waiver's `why` mentions each finding string the gate currently reports for that
  check ID, and FAIL when the gate reports a finding the waiver does not name.
  That converts "waiver absorbs future findings" from a silent hazard into a red.

## An unsatisfiable declared floor and a formula that cannot reach the satisfiable one
- what happened: `fab_tiers.yaml` moved `min_silk_stroke` 0.15 -> 0.1125 on
  2026-07-29 because KiCad clamps stroke to <= 0.25 x height, so the previously
  declared pair (0.45 height, 0.15 stroke) was unsatisfiable — and it declared
  the corollary that reaching 0.15 needs >= 0.60 mm text. On this board 0.60 mm
  text measured **0.13**, not 0.15, because `generate_board_generic` computes
  stroke as `max(min_silk_stroke, 0.13, 0.16 * size)`: 0.16 x 0.60 = 0.096, so
  the 0.13 hardcode wins. 0.15 needs `size >= 0.9375`.
- root cause: the tier file and the generator each carry half of the same rule
  and neither knows the other's half. The tier states a floor; the generator
  states a taper. G-SELFCON now checks the tier against ITSELF (height vs
  stroke) but nothing checks the tier's corollary against the code that has to
  deliver it.
- avoid next time: when a fab floor is stated as "X requires Y", find the line of
  code that produces Y and evaluate it at X before writing the corollary down.
  Locally: the ten port labels are 0.95 mm / 0.152 mm and that number was read
  off the generated board, not derived from the tier file.
- candidate-canon: yes — extend G-SELFCON to evaluate the generator's actual
  stroke expression at the tier's `min_silk_text_height` and fail if the result
  is below `min_silk_stroke`, or if the tier's declared corollary height does not
  in fact reach it.

## The obstacle term a by-hand silk check always omits is the part BODY
- what happened: seven captions were placed by hand "verified against the placed
  courtyards" and all seven came back as `crowded` WARNs. With `caption_nudge:
  false` the generator keeps a crowded caption where it is and only warns, so the
  board carried overlapping silk that DRC does not grade (silk-over-silk is not a
  DRC rule; only silk-over-copper and silk-over-edge are).
- root cause: the generator's obstacle model is pads + footprint silk + refdes
  boxes **plus `fp.GetBoundingBox()` inflated 0.05 for every non-hole footprint**
  — "silk under a body is invisible on the assembled board". A human checking
  against courtyards checks a smaller set, and on a board whose jacks are rotated
  15/45/75 degrees the axis-aligned body bbox is much larger than the courtyard.
  The port contract was hitting J_ANT5's body bbox, 5.3 mm from a jack centre
  whose courtyard half-width is 3.75.
- avoid next time: do not hand-place captions on a dense board. Reproduce the
  generator's `_obstacles()` offline (it is ~20 lines) and SEARCH — for radial
  layouts, search along each label's own radius, which delivers ownership for
  free. Verify by re-running the generator and requiring **0 crowded**, not by
  reading the positions.
- candidate-canon: yes — `caption_nudge: false` should be an ERROR when any
  caption ends up crowded, not a WARN. A "keep the best offset anyway" fallback
  on a board that has explicitly disabled nudging is the worst of both: the
  author believes the positions are theirs and the generator believes it is
  allowed to ship an overlap.

## Ownership, not presence, is what a connector label has to satisfy
- what happened: `P-SILK-FN` was FAILING on only three refs (J_ANT3, J_ANT6,
  F_IN), so seven of ten SMA jacks were "labelled" — by captions belonging to
  other things that happened to fall within the search radius. Measuring
  distances instead of counting labels found "RX2 -> PLUTO RX2" at 7.29 mm from
  J_ANT1 and 7.85 mm from J_RX2: nearer the antenna jack than the SDR output it
  named.
- root cause: P-SILK-FN asks "is there any silk text within (8 mm + half the
  part's diagonal) of this part". That is a PRESENCE test. It cannot distinguish
  a label from a neighbour's label, and on a ring of ten identical parts every
  label is inside several parts' radii at once.
- avoid next time: for any group of interchangeable connectors, measure each
  label against EVERY member of the group and require its own part to be
  strictly nearest, with a stated margin. On this board the margin is 2.2-3.9 mm
  and it is a CHECKLIST-D line with the numbers in it.
- candidate-canon: yes — P-SILK-FN should grade OWNERSHIP where two or more
  matched refs share a prefix family: the nearest matched footprint to a
  functional caption must be the one whose label it is. Presence-only is the
  `jlc_twin`-exited-0 shape named in the repo CLAUDE.md — this instance is a gate
  that reported 7-of-10 labelled while one label named the wrong connector.

## "Structural pre-routing FAIL" is a category that hides authoring defects
- what happened: `R-DRC 24 violations / 100 unconnected / 12 parity` was recorded
  in `policy_waivers.yaml` as a structural consequence of stopping before
  routing. Only the 100 unconnected was. The other three classes were authoring
  defects: 12 parity from `Datasheet`/`Description` properties in the authored
  footprints that the converter's symbols do not carry; 7 `text_thickness` from a
  board generated one day before the tier's stroke floor changed (fixed by
  REGENERATION alone, source untouched); 2 `silk_edge_clearance` from footprint
  silk drawn 0.71 mm off the board edge.
- root cause: naming a fail "structural, closes at stage 6" tells the next reader
  not to look inside it. The aggregate count is the only thing carried forward,
  and an aggregate cannot distinguish 100 unconnected from 100 unconnected plus
  24 real findings.
- avoid next time: a pre-routing R-DRC fail must be recorded CLASSIFIED, never as
  a total — the violation-type histogram, with a sentence per class saying why it
  is or is not structural. `classified_drc.py` already prints exactly that
  histogram; the waiver just did not use it.
- candidate-canon: yes — policy_audit's R-DRC detail line should carry the
  violation-type histogram (`{starved_thermal: 4}`) rather than only the three
  totals, so a waiver cannot be written against an opaque number.

## nothing else
Everything else this stage touched behaved as the canon predicted: the generic
backend needed no board-specific Python, the `pad_overrides` primitive already
existed for exactly the connector-GND-starvation case it was used for
(crow-array-pod J1, cook-hub relay bank), and `tier_preflight --explain` named
its one WARN with the fleet measurement behind it.
