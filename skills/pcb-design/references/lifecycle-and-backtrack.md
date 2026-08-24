# Lifecycle, handoff, and backtrack procedure

Use this procedure to execute stages, bound long-running work, recover from a
red gate, and resume safely from repository state.

## Contents

1. Stage state machine
2. Evidence and journals
3. Planned handoffs
4. Bounded work and visibility
5. D-BACK diagnosis
6. Backtrack destinations
7. Writer and promotion discipline

Policy IDs owned by this procedure: `D-BACK`, `M-BEACON`, `M-JRNL`, and
`M-LEARN`.

## 1. Stage state machine

Treat the pipeline as a loop, not a one-way checklist:

```text
enter(stage)
  -> validate required inputs and subject identity
  -> perform bounded work
  -> measure the owning gate
     PASS             -> commit evidence; finish journal; advance
     FAIL improving   -> iterate current source/config; remeasure
     FAIL plateau     -> diagnose; backtrack; regenerate downstream
     WAIT human       -> persist commission; pause visibly
     ERROR/TIMEOUT    -> preserve prior accepted bundle; diagnose
```

A repeated red gate with no new hypothesis is the prohibited state. A red gate
that names its owner and backtrack destination is normal pipeline behavior.

Use the typed `StageSpec` and `StageResult` interfaces in
`pipeline-stage-contract.md` for orchestration changes. Commands, paths, and
domain limits stay outside semantic stage identity. The current project driver
remains execution authority until its shadow trace agrees with the typed plan.

## 2. Evidence and journals

Maintain three distinct records:

- `01_docs/journal/<stage>.md`: append start, iteration, stuck, handoff, and
  finish events with measured result and next implication;
- `01_docs/learnings/<stage>.md`: root cause and reusable prevention proposal,
  marked as candidate canon or project-local;
- `01_docs/STATUS[-<board>].md`: overwrite the live seven-field beacon at each
  transition and immediately before/after a long operation.

Do not reconstruct journals at release time. A journal's existence is not
stage coverage; every executed stage needs its own events. The beacon is live
state, not history. Run the beacon checker after a seal and reject duplicated,
stale, or superseded-release claims.

Every load-bearing claim in a handoff or report must be marked `MEASURED` with
method or `INHERITED` with source and unverified status. Never instruct a
successor not to rederive an inherited number.

## 3. Planned handoffs

Require fresh handoffs after adopted schematic review, after accepted
placement/pilot feasibility before global routing, immediately on D-BACK, and
after layout seal. When the host exposes comparable live context telemetry,
warn at 60 percent and require a handoff at 70 percent before beginning more
expensive work. Semantic boundaries remain mandatory when telemetry is
unavailable. At a boundary:

1. Commit the green state.
2. Append a handoff journal entry with current stage, next command, open
   hypotheses, and measured gates.
3. Refresh the status beacon.
4. Generate and validate the compact content-addressed handoff through the
   KiCad flow helper.
5. Generate a strict `TaskEnvelope` naming `context_mode: FRESH`, the exact
   packet, deadline, role ceiling, replacement limit and writer scope.
6. End the current session; do not let it continue mechanical work past a
   mandatory boundary.

A successor reads only the verified handoff, beacon, tail of the current-stage
journal, and exact files named by those records. Do not preload the transcript,
whole journal/learnings directories, or an earlier reviewer's reasoning.

## 4. Bounded work and visibility

Classify execution time before running it:

- local/cheap mechanical checks;
- bounded CPU work;
- network work with retry/backoff;
- independent review wait;
- operator wait.

Separately declare the agent role as `mechanical`, `authoring`, or `judgment`.
`execution_class` attributes time; `agent_role` sets the logical compute
ceiling. Do not reuse one vocabulary for the other. The companion contracts in
`pipeline_execution.py` bind these facts without changing `StageSpec`.

Give executable stages a positive deadline. Stream heartbeats or durable
progress for work whose normal runtime can appear silent. A timeout terminates
the process group, produces a non-pass result, and preserves the previous
accepted artifact bundle.

Use the cheapest capable compute tier. Scripts own deterministic loops;
low-cost agents may apply table-known config changes; high-judgment work is
reserved for causal diagnosis and upstream backtracking. Do not repeatedly
resume a context-heavy agent for mechanical iterations.

Human review is not a polling accident. Persist an immutable commission and
pause with `INCOMPLETE`; never manufacture a witness or infer acceptance from
silence. The coordinator, not review prose, enforces the deadline: interrupt a
late reviewer, materialize every unfinished checklist row as unresolved, and
allow at most one fresh replacement on the same exact subject. User approval
advances only the stage explicitly under review.

## 5. D-BACK diagnosis

Stop local iteration after three consecutive attempts with no measured
improvement, when the same finding IDs recur, or when the current configuration
cannot express a remedy.

Before moving upstream:

1. Group findings by cause; do not treat a heterogeneous count as one problem.
2. Reopen the exact artifact and verify the causal hypothesis.
3. Name the upstream decision that produced the finding.
4. Commit the failed attempt as evidence.
5. Append a `stuck` journal event with plateau and hypothesis.
6. Write the learning while the evidence is live.

Cheap independent finding groups should be resolved before escalating the
surviving hard group.

## 6. Backtrack destinations

| Symptom | Reopen | Change |
|---|---|---|
| Local clearance/via tail | Placement | Adjacency, orientation, corridor |
| Congestion across regions | Placement, then architecture | Floorplan area, bank split, outline |
| Width/via/hole floor impossible | Fab tier or part | `D-TIER` or `D-ESC` |
| Package cannot escape | Part selection | Package/part |
| No compliant sourceable part | Architecture, then specification | Topology or `D-SPEC` |
| Schematic/parity churn | Dossier/source | Pin map, aliases, source model |
| Critical route omitted | Route contract | Net inventory, engine, layer/via policy |
| Repeated 3D registration error | Model/adjudication producer | Frame, anchor, source model—not render pixels |
| Architecture difficulty caused by ambiguous requirement | Brief/specification | Ask user or record simplest conservative reading |

Fix the owning source—brief, ADR, dossier, TSX, floorplan, rules, or promoted
route. Regenerate every downstream artifact. Never patch `04_kicad`, CSVs, or
a staged release by hand.

The same stage may be re-entered three times on genuinely different upstream
hypotheses. A fourth arrival requires escalation one stage farther upstream or
an honest-stop ADR naming the exhausted hypothesis space.

## 7. Writer and promotion discipline

Only one writer/process edits a board's live source tree. Parallel work is
limited to independent research, calculation, or read-only review of exact
artifacts. Speculative downstream work belongs in an isolated permanent
worktree and cannot be promoted while an upstream gate is red.

Every producer follows a transaction:

1. write to a fresh sibling staging directory;
2. reject undeclared, missing, empty, stale, or unparsable outputs;
3. reopen outputs and cross-check key fields;
4. write the bundle manifest last;
5. atomically promote only a passing bundle;
6. preserve the previous accepted bundle on failure.

Promote the final route chain into committed source. Keep generated build data
disposable unless a contract names it as release or resume evidence. Commit at
green gates so Git remains the geometry undo and handoff boundary.
