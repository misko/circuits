# Pipeline shadow canaries

This record separates observation of the existing PCB drivers from migration
of their authority.  The legacy drivers, gates, accepted artifacts and release
paths remain authoritative.

## 2026-08-12 disposable reuse-driver observation

Both observations ran from a detached disposable worktree at source commit
`2b192208`.  Each driver used a dedicated Bash xtrace file descriptor and an
outer 900-second `timeout` with a 15-second TERM-to-KILL grace period.  The
worktree was removed afterward; no accepted project or sealed release bytes in
the main worktree were changed.

| Project and driver | Elapsed | Exit | Last command boundary reached | Result |
|---|---:|---:|---|---|
| USB Hub 3S v4 `03_src/rebuild_reuse.sh` | about 11.4 s | 1 | pre-route placement/readability review | Failed diagnostically: regenerated inputs invalidated review hashes and the disposable build lacked `twin_overlay.md`; eight PR-REVIEW findings were reported. |
| Pluto RX2 8-way `03_src/rebuild_reuse.sh` | about 2.0 s | 2 | board generation | Failed diagnostically: seven pairs of anchored courtyards overlap, so P-COLLIDE refused the generated board. |

The observations produced 41 USB trace records and 20 Pluto trace records.
Neither run was silent or locked: both stopped quickly at a real current
blocker.  They do **not** establish shadow equivalence, and they do not make a
new engine authoritative.

A second disposable run used absolute driver identities so the new strict
mapper could consume the trace directly.  USB again stopped at the same review
gate after about 14.3 seconds; all 36 top-level dedicated records mapped to an
exact 23-stage catalog prefix with no unmapped executable record.  Pluto again
stopped at board generation after about 1.3 seconds; all 15 top-level records
mapped to an exact three-stage prefix with no unmapped executable record.
Nested `++`/`+++` shell-expansion diagnostics are deliberately outside the
single-`+PIPELINE_TRACE` command channel.

The Pluto observation above is the legacy `pluto-rx2-8way` project requested
for comparison.  It is not the separate `pluto-rx2-8way-v4` sealed canary
required by ADR-0008 before orchestration authority may move.

## 2026-08-12 legacy Pluto blocker correction

The seven legacy Pluto `P-COLLIDE` findings were axis-aligned-bounding-box
false positives, not placement defects.  KiCad's transformed courtyard
polygons are disjoint (about 1.140 mm for the six radial SMA pairs and
0.350 mm for `R_T2`/`R_T1`), and KiCad DRC reports no courtyard violation.
The shared generator now uses bounding boxes only to shortlist pairs and
confirms a failure with the native polygon collision predicate.  True-overlap
negative controls still fail; no RF anchor was moved.

With that exact checker correction applied in a disposable worktree, the
legacy reuse driver exercised all 12 catalog stages in 7.29 seconds.  The
largest observed stages were stitch/fill (3.798 s), board generation (1.151 s)
and KiCad DRC (1.044 s); no stage was silent or locked.  The first honest stop
moved to the final routing-count verdict: 45 violations, 15 unconnected and
zero parity findings.  The DRC process correctly writes its report and the
separate postcheck owns the failing verdict.  This is a complete mapped legacy
trace, not a green design canary and not orchestration equivalence.

## 2026-08-12 distinct canary progression

USB Hub 3S v4 now has an explicit bounded preparation stage between route prep
and the unchanged placement-review authority.  When evidence is stale it
atomically publishes exact-subject top/isometric renders plus an `INCOMPLETE`
commission; when evidence is current it writes an `ALREADY_ADMISSIBLE` pointer.
It never writes a human witness or acceptance token.  First preparation took
19.77--21.15 seconds and an unchanged semantic rerun 1.06--1.07 seconds.  The
gate still failed closed with the eight existing stale findings, so this makes
the pause observable and actionable without manufacturing a pass.

The distinct `pluto-rx2-8way-v4` full and deterministic-reuse catalogs contain
46 and 22 stages respectively.  Disposable reuse first caught missing explicit
applicability for its single-ended RF arms, then caught anonymous ownership on
26 non-pin seed-via banks.  After those source contracts were stated without
changing geometry, all 22 reuse stages completed green in 139.91 seconds:
KiCad DRC was 0 violations / 0 unconnected / 0 parity, the fence audit graded
22/22 configured arm-sides and RF length audit graded 8/8 paths.

That run also reproduced the original operator experience in a controlled way.
Stitch/fill printed its passes while processing 3,405 grid vias, but the CPWG
field solver used about 24 CPU cores without output for 35.724 seconds.  The
result was productive, not stuck; the missing heartbeat was nevertheless a
pipeline defect.  The v4 driver now runs that stage through the bounded runner
with a measured 45-second budget and a 60-second process-group deadline.  A
final disposable run then completed all 22 mapped stages green in 94.94 seconds
with zero unmapped commands; the solver recorded 6.579 seconds, budget/timeout
45/60, and a durable terminal state.  The runtime variation is why the budget
comes from the slower 35.724-second observation rather than the final fast run.

## Driver-map findings

- USB reuse has a modern sequence, but several direct Python/KiCad commands
  still have no stage-level outer deadline or heartbeat.  Failure is visible;
  a genuinely quiet long child would still look stuck until the shell exits.
- Legacy Pluto reuse calls every stage directly from Bash without a shared runtime
  budget or heartbeat.  Its current early failure is useful evidence, not proof
  that later stages cannot become silent.
- Legacy Pluto full rebuild imports with the default `auto` source.  A stale
  `06_build/route/FINAL` can therefore outrank the promoted committed route;
  reuse deletes that marker first and chooses the promoted route.  The two
  entry points do not currently make the same source-selection guarantee.
- Legacy Pluto full-rebuild comments still describe a schematic-only state, although
  the script now runs board generation, board audit, route import/stitch, DRC
  and postcheck.  Comments cannot be used as the executable stage map.
- Legacy Pluto full rebuild performs one parity check before regenerating the board,
  so it can grade prior build output.  Any migration must bind observations to
  the exact producer subject rather than infer freshness from path names.

## Safe migration rule

The project catalogs are exact-driver-hash-bound data.  The observer and xtrace
adapter only report what the legacy driver did; they cannot execute, retry,
delete, promote or publish.  A catalog mismatch, unmapped executable command,
truncated trace, subject drift or legacy failure is an incomplete/failed
canary, never a pass.

Next evidence should complete the commissioned USB human reviews, correct the
legacy Pluto routed-design violations separately from the collision checker,
and compare ordered applicability/identity/output/result observations against
both complete canary catalogs.  The legacy drivers remain authoritative until
that comparison passes and an ADR amendment explicitly moves authority.

## 2026-08-15 progressive-disclosure compatibility layer

The skill refactor did not migrate execution authority. The project rebuild
drivers, script predicates, review pauses, accepted artifacts, seal rules, and
publication gate remain authoritative exactly as before. The new
`skill_reference_router.py` is a pure composition/coverage tool: it cannot run
a stage, retry work, promote an artifact, write a review, seal a release, or
publish a branch.

The compatibility audit freezes source commit
`a8659927c98baf22c51dd4db733b901911098d3f` as its legacy denominator. It
accounts for 109/109 policy and gate IDs, assigns 14 domains to one owner each,
and requires all 19 selected references to be directly reachable from the
small core. The PCB core is 260 lines / 1,819 words, inside its enforced
250--400 line and 5,000-word budget.

Four capability fixtures pin the normalized composition trace:

| Fixture | Target | Typed stages | Conditional behavior |
|---|---|---:|---|
| Simple ordinary board | layout seal | 7 | no RF, mating, JLC, release, or firmware procedure |
| USB Hub 3S v4 | release seal | 11 | JLC path selected; existing fail-closed review semantics retained |
| Raspberry Pi USB switch | release seal | 15 | conditional SI context/source/realized/fab evidence selected; geometry may defer to placement |
| Pluto RX2 8-way | release seal | 15 | RF context/source/realized/fab stages selected; no firmware stage |

The focused progressive-disclosure suite passed 9/9, including known-bad
fixtures for duplicate authority and an unregistered assembly adapter plus
executable declarations of both new tools' semantic limits. The
existing USB catalog canary passed 9/9 and the distinct Pluto v4 catalog canary
passed 7/7. Stage-contract, registry, rebuild-template, and rotation-authority
suites also remained green. This proves reference-selection and governance
compatibility; it does not convert a static catalog check into board execution
equivalence and does not authorize a driver migration.
