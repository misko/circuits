# Agent roles and compute ceilings

The D-TIER symmetry, applied to tokens: a board's fab tier is a COST CEILING
declared at commission (D-TIER) — you never discover it at the DRC gate.
Compute is the same resource with the same failure mode, denominated in tokens
instead of dollars. Mechanical loops must not silently inherit the cost and
context of judgment work. This file owns the logical agent-role ceiling;
`pipeline-stage-contract.md` owns execution classes such as `local`, `network`
and `review_wait`. The two axes are deliberately different.

Provenance: generalizes the routing-grind ladder: deterministic script,
mechanical operator, then judgment only on a measured D-BACK.

## Agent roles

| Role | The work | Logical ceiling |
|---|---|---|
| mechanical | rebuild/poll loops, fab export, PDF/artifact regen, twin runs, packaging, DRC re-runs, sweeps — every gate is machine-MEASURED; judgment adds nothing to the loop | economy / low effort |
| authoring | schematic/tsx edits, floorplan/route config, part.yaml writing — bounded creation against a schema; the gates catch the errors | standard |
| judgment | red-team lenses, D-BACK diagnosis, seal-verify adjudication, user-facing decisions — the output IS the judgment; a low-cost role here fails silently | standard / full effort |

## The rule

- Every spawned agent declares `agent-role: mechanical|authoring|judgment`.
  A generated `TaskEnvelope` records the recommended role, actual role and
  any escalation reason; model names do not belong in project authority.
- Escalating above the recommended role requires a stated reason: why the
  lower role cannot produce the required evidence, not that a higher tier is
  preferable.
- Mechanical work is SAFE at the cheap tier for the same reasons the routing
  grind is: gates are machine-measured (`kicad-cli drc` cannot be talked into
  0/0/0), canon M3 forbids hand-editing outputs, and loop bounds live in the
  scripts, not in model judgment. A cheap agent that hits a wall escalates
  (D-BACK) — it does not improvise.
- `execution_class` remains the elapsed-time attribution axis. Never store an
  agent role in `StageSpec.work_class`, and never infer an agent role from a
  subprocess timing row.
