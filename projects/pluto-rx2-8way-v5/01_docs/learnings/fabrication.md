# Fabrication-stage learnings

## Strict rotation failure was useful, not a pipeline lock
- what happened: the first strict export stopped immediately on six missing
  exact-code rotation authorities instead of producing plausible-looking CPL
  data. Independent measurements closed all six and the 99-row table passed.
- root cause: this was an intentionally incomplete authority denominator, not
  a slow or hung producer. The fail-closed exporter made the worklist explicit.
- avoid next time: preserve the strict default and measure rotations when exact
  parts are frozen, before the first fabrication export. Keep the numbering-free
  polarity channel and JLC human-preview denominator separate.
- candidate-canon: no — A-ROT/M-PROV already implement the correct behavior;
  this run is positive validation of the existing canon.

## Repeated physical pads cannot be represented by a merged label centroid
- what happened: C429844 has five physically coincident project/JLC holes, but
  JLC calls four shell posts pad 2 while the project preserves pins 2/3/4/5.
  The twin's centroid comparison reported false 1.796/3.59-mm geometry errors.
- root cause: the comparison collapsed repeated pad labels before attempting
  physical multiset matching; the scalar alias schema cannot express one JLC
  label mapping to four project identities.
- avoid next time: compare complete physical pad multisets independently of
  pin naming, while keeping electrical pin-map agreement as a separate result.
- candidate-canon: yes — IMP-093 specifies the matcher and known-bad fixtures.

## Exact-artifact names and commit IDs must not travel as prose
- what happened: rf.yaml used a hyphen where the exporter emitted an
  underscore, and the coordinator later hand-expanded a short commit into a
  nonexistent SHA. Both were caught before review finalization.
- root cause: producer output identity was restated manually in two channels
  rather than passed through a generated artifact/review dispatch record.
- avoid next time: emit a role-indexed artifact manifest and a machine-written
  review envelope containing exact paths, hashes, commit, dirty scope and
  requirement/header schema; make the reviewer validate it before work.
- candidate-canon: yes — IMP-094 and IMP-095.

## Time-box evidence-complete independent review tails
- what happened: the first RF-fab reviewer had completed all decisive
  measurements but continued a quiet visual tail across repeated bounded wait
  windows without writing the contracted result. It was interrupted and a
  bounded reviewer finalized from the measured evidence.
- root cause: the review task had a clear evidence threshold but no enforced
  transition from exploration to verdict once that threshold was met.
- avoid next time: dispatch an explicit evidence denominator and deadline;
  once complete, unresolved optional inspection becomes a named finding or
  order-time duty rather than more hidden work. Use status heartbeats and
  interrupt/reassign when the verdict artifact remains absent.
- candidate-canon: no new item — this is another instance of IMP-026 and
  IMP-049; the run demonstrates the intended recovery behavior.

## Release PDFs need semantic page selection
- what happened: a mechanically valid generic export made a seven-page
  assembly packet with four blank/near-blank pages and one crowded value-heavy
  page. A top-side, purpose-derived export produced three useful pages and a
  cleaner seven-page PCB packet.
- root cause: the command listed possible layers rather than asking which
  populated sides and document roles existed on this board.
- avoid next time: derive pages from populated sides/nonempty content, make the
  edge common, suppress values on locator pages, raster-check every page and
  name the page denominator in the evidence.
- candidate-canon: yes — IMP-096.
