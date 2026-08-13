# Schematic-stage learnings

## Current-stage ownership cannot name future files
- what happened: the first full-driver run stopped before generation because route ownership included a deliberately absent future floorplan.
- root cause: the copied flow convention treated the eventual routing source set as if every member existed at schematic entry.
- avoid next time: initialize `flow.owner.files` from the files that actually exist at the current stage and add later-stage sources transactionally when their stage begins.
- candidate-canon: yes — fold into IMP-069's stage-derived ownership/receipt work.

## Producer transport names need an explicit canonical round trip
- what happened: tscircuit rejected `net.3V3` after 5.257 seconds because its identifier grammar disallows leading digits.
- root cause: the project contract and KiCad use `3V3`, while the foreign producer requires a lexical transport alias.
- avoid next time: encode the alias in one source helper (`N3V3`) and require post-conversion label-survival assertions to prove the canonical `3V3` result; never rename the design contract merely to satisfy an intermediate parser.
- candidate-canon: no — the shared converter and established N-prefix convention already own this behavior; this run confirms it remains effective.

## Connectivity parity does not prove human pin-function truth
- what happened: 129/129 physical pin/net assertions, 30/30 invariants and zero-error ERC passed while the first PDF misnamed several unused STM32 pins.
- root cause: existing gates compare physical pin numbers and nets. They do not compare the visible symbol function text with the exact dossier, especially on intentional no-connects.
- avoid next time: add a pre-render symbol-function/dossier comparison covering every physical pin, with explicit reviewed aliases for role suffixes and alternate-function abbreviations; keep the human PDF review because presentation cannot be reduced to string equality.
- candidate-canon: yes — IMP-073 records the generic checker and fixtures.

## Versioned generated consumers remove timing-copy drift
- what happened: the fast 20 ms-class request affected firmware constants and downstream decoding windows together; hand-copying eight dwells plus derived frame numbers would create two or three authorities.
- root cause: the original schema validated one YAML schedule but had no exact consumer-generation contract.
- avoid next time: keep profile identity/revision and both project-confined outputs in the control schema; generate the firmware header and decoder JSON from the same validated source and fail pre-TSX when either is stale.
- candidate-canon: yes — this extends implementing IMP-071; actual firmware/decoder behavior still requires end-to-end tests.

## Bounded execution made failure visibly cheap
- what happened: the only foreign-producer failure completed in 5.257 seconds; successful tscircuit builds took 3.3 seconds and the whole electrical/checkpoint pass took about 9-10 seconds.
- root cause: the stage used the generic process-group timeout/heartbeat wrapper and cheap schema checks before generation.
- avoid next time: retain explicit per-stage budgets, timeouts and heartbeat output; record actual durations in the journal and adjust only from measured runs.
- candidate-canon: no — IMP-051 and IMP-065 already own this implemented behavior; v5 is supporting evidence.

## Prose-derived ADR applicability can hide a zero denominator
- what happened: E-ADR printed `0/0` although all three accepted v5 ADRs make topology/control/protection decisions and 30 invariants cite them.
- root cause: the checker infers applicability from keywords in titles or optional tags; the descriptive v5 titles do not match its regular expression.
- avoid next time: type the assertion domains in ADR front matter and require an explicit `none` rationale rather than treating a title heuristic as the denominator.
- candidate-canon: yes — IMP-074 records the schema migration and regression cases.
