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

## Driver-map findings

- USB reuse has a modern sequence, but several direct Python/KiCad commands
  still have no stage-level outer deadline or heartbeat.  Failure is visible;
  a genuinely quiet long child would still look stuck until the shell exits.
- Pluto reuse calls every stage directly from Bash without a shared runtime
  budget or heartbeat.  Its current early failure is useful evidence, not proof
  that later stages cannot become silent.
- Pluto full rebuild imports with the default `auto` source.  A stale
  `06_build/route/FINAL` can therefore outrank the promoted committed route;
  reuse deletes that marker first and chooses the promoted route.  The two
  entry points do not currently make the same source-selection guarantee.
- Pluto full-rebuild comments still describe a schematic-only state, although
  the script now runs board generation, board audit, route import/stitch, DRC
  and postcheck.  Comments cannot be used as the executable stage map.
- Pluto full rebuild performs one parity check before regenerating the board,
  so it can grade prior build output.  Any migration must bind observations to
  the exact producer subject rather than infer freshness from path names.

## Safe migration rule

The project catalogs are exact-driver-hash-bound data.  The observer and xtrace
adapter only report what the legacy driver did; they cannot execute, retry,
delete, promote or publish.  A catalog mismatch, unmapped executable command,
truncated trace, subject drift or legacy failure is an incomplete/failed
canary, never a pass.

Next evidence should close the two present blockers, capture complete reuse
traces, compare ordered applicability/identity/output/result observations, and
then repeat on the sealed USB Hub 3S v4 and Pluto RX2 8-way v4 canaries.  Bounds
and heartbeats for live driver stages are a separate, regression-tested
migration after observation agrees.
