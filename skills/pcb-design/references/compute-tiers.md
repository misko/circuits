# Compute tiers — the model an agent runs on, as a DECLARED cost ceiling

The D-TIER symmetry, applied to tokens: a board's fab tier is a COST CEILING
declared at commission (D-TIER) — you never discover it at the DRC gate.
Compute is the same resource with the same failure mode, denominated in tokens
instead of dollars: with no declared ceiling, every spawned agent silently
defaults to the most expensive model, and mechanical work (poll loops,
rebuilds, exports) burns frontier tokens producing output a cheap model
reproduces exactly. This file is the tier table; the governing rules live in
SKILL.md "Compute discipline".

Provenance: generalizes the routing-grind tier ladder already proven in
SKILL.md stages 4-6 (Tier 0 script / Tier 1 cheap operator / Tier 2 frontier
on D-BACK escalation only); subsumes task #17 ("routing cost-tiering").

## Work classes

| Class | The work | Tier (ceiling) |
|---|---|---|
| mechanical | rebuild/poll loops, fab export, PDF/artifact regen, twin runs, packaging, DRC re-runs, sweeps — every gate is machine-MEASURED; judgment adds nothing to the loop | cheap model (haiku-class), low effort |
| authoring | schematic/tsx edits, floorplan/route config, part.yaml writing — bounded creation against a schema; the gates catch the errors | default model |
| judgment | red-team lenses, D-BACK diagnosis, seal-verify adjudication, user-facing decisions — the output IS the judgment; a cheap model here fails silently | default model, full effort |

## The rule

- Every spawned agent DECLARES its work class in the spawn prompt
  (`work-class: mechanical`). The class names the tier; the tier is the
  ceiling.
- Escalating ABOVE the class tier requires a stated reason in the same spawn
  prompt — the D-TIER shape: why the cheaper tier fails, not that the costlier
  one is nicer.
- Mechanical work is SAFE at the cheap tier for the same reasons the routing
  grind is: gates are machine-measured (`kicad-cli drc` cannot be talked into
  0/0/0), canon M3 forbids hand-editing outputs, and loop bounds live in the
  scripts, not in model judgment. A cheap agent that hits a wall escalates
  (D-BACK) — it does not improvise.
