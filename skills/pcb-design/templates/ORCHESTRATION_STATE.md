# ORCHESTRATION STATE — <campaign>

<!-- The multi-board coordinator's own state journal — the orchestrator analog
of a board's STATUS beacon. Copy from skills/pcb-design/templates/ at campaign
start; lives at the orchestration root (repo/worktree root), never inside a
project. OVERWRITE sections in place: this is the live head, not append-only
history — hard analysis still goes to each board's journal (canon M9). -->

## Commit ledger
<!-- one row per commit relayed or verified; "verified-by" = the measurement
YOU re-ran, not the agent's claim (reports are claims, artifacts are proof) -->

| sha | board | what | verified-by |
|---|---|---|---|

## Per-board state
<!-- mirrors pcb_status.py output — POLL beacons, don't wake agents to ask -->

| board | agent | stage | state | last measure | next |
|---|---|---|---|---|---|

## Seal-verify protocol (run per seal — the orchestrator RE-MEASURES)
- [ ] DRC 0/0/0 — `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`, re-run yourself
- [ ] MANIFEST sha256 self-check — every listed hash re-computed and equal
- [ ] `git check-ignore` sweep — no release/source input gitignored (canon M3/M-REPRO)
- [ ] freshness gate — `release_freshness_check.py 07_releases/<ver>` exits 0
- [ ] semantic M-BOM — `bom_source_check.py FAB_BOM CIRCUIT_JSON`: per-refdes LCSC equals source (canon M6)

## Standing hazards / gotchas
<!-- campaign-scoped traps already paid for — one line each, with the incident -->

## Active watch-relays
<!-- background monitors running now: what watched, wake condition, pid -->

## Economy mode
<!-- the compute ceiling in force (SKILL.md "Compute discipline") -->
- tiers: agents declare work class at spawn per `skills/pcb-design/references/compute-tiers.md`
- comms: poll beacons via `pcb_status.py`; push only at gates/decisions/walls; BATCH relays to heavy agents
- fresh-over-resume: agent past ~300k tokens → planned handoff at next gate, fresh successor from the tree (never resume-the-giant)
