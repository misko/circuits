# Parts and architecture learnings

## Assembly-catalog stock is not a two-source gate

- what happened: The first candidate set passed the JLC/LCSC probe 15/15 but only 9/15 exact MPNs were confirmed at the first independent authorized distributor. Six parts had to be replaced before selection could close.
- root cause: The source checks were run sequentially and the first report's all-green headline was easy to mistake for the complete sourcing decision.
- avoid next time: Make selection atomic: one command should join the JLC assembly identity, exact manufacturer MPN and a composed independent authorized-distributor pool before it can print PASS.
- candidate-canon: yes — D-SOURCE-JOIN, with no success verdict until both sides of every exact-MPN row pass.

## Generic base MPNs can conflate manufacturers

- what happened: A generic `BZT52C12` catalog identity appeared usable, but it did not establish the same manufacturer and full orderable suffix at the independent source. It was replaced by Diodes Incorporated `BZT52C12-7-F`.
- root cause: Matching normalized search text is weaker than matching manufacturer identity plus full orderable MPN.
- avoid next time: Treat `(manufacturer, full MPN)` as the sourcing key and fail ambiguous catalog rows instead of accepting family/base-part matches.
- candidate-canon: yes — Q-MFR-IDENT, an exact manufacturer-and-orderable-part assertion in every dossier and source report.

## Exposed-pin inventory must survive scope simplification

- what happened: Removing USB data and PD correctly removed many circuits, but CC1 and CC2 remain exposed connector pins and initially lacked an explicit ESD disposition. The final architecture added `TPD2EUSB30DRTR`.
- root cause: The interface review was organized by product feature (“power-only USB”) rather than by every externally accessible conductor.
- avoid next time: Generate a connector surface table from every external pin and require one of protected, intentionally unprotected with rationale, chassis/shield, or NC-with-no-exposure before part freeze.
- candidate-canon: yes — D-EXPOSED-PIN, applied before D-SPEC closes.

## Per-distributor shopping verdicts do not prove a composed pool

- what happened: The shopping helper correctly showed Mouser at 15/16, but its overall non-zero exit implied failure even though DigiKey independently stocked the one remaining exact part. A separate composed qualification document was needed.
- root cause: The helper asks whether each single distributor covers the whole BOM; the policy asks whether an approved independent distributor pool covers every row.
- avoid next time: Add pool semantics and row-level provenance to the helper, retaining a stricter optional single-source convenience report as a separate verdict.
- candidate-canon: yes — Q-2SOURCE-JOIN, which reports both composed-pool coverage and single-distributor coverage without conflating them.

## Network time was not the lock-up

- what happened: Stage 1 took about 65 minutes, while the live JLC and distributor probes completed in seconds. Most time went to datasheet comparison, ambiguous identity resolution, architecture backtracking and writing auditable evidence.
- root cause: The pipeline exposes process presence but not phase-level progress or a time ledger, so high-value research appears indistinguishable from a hung generator.
- avoid next time: Emit a stage heartbeat containing current item, completed/total rows, last external response time and next bounded action; record subprocess duration separately from research/adjudication time.
- candidate-canon: yes — M-PROGRESS-LEDGER with bounded-call timing and an explicit `research/adjudication` state.

## Board-dependent audits need stage applicability

- what happened: `rules_audit.py` reported a missing `.kicad_pro` during Stage 1, even though schematic generation is intentionally forbidden until the parts checkpoint is accepted.
- root cause: The audit reports a board artifact prerequisite as an undifferentiated failure instead of `not-applicable-before-schematic`.
- avoid next time: Give every audit an earliest stage and emit SKIP/NA with the missing future artifact when invoked earlier.
- candidate-canon: yes — M-STAGE-ENTRY applicability metadata for audit commands.

## One tier field cannot represent two different manufacturing facts

- what happened: The final `escape_check.py` pass rejected four dossiers. Three used `escape.tier_required` for an advanced filled/capped thermal-via process even though their 0.65 mm signal geometry computes to standard four-layer; the reverse FET made the opposite error and claimed two-layer geometry.
- root cause: Package escape feasibility and exposed-pad thermal-process intent were compressed into the same field despite having different evidence and checkers.
- avoid next time: Keep `escape.tier_required` strictly equal to the geometric computation, and add a separately graded process requirement for via-in-pad fill/cap, paste treatment and inspection.
- candidate-canon: yes — P-PROCESS, a per-part manufacturing-process block joined to board tier and order instructions without overloading P-ESC.
