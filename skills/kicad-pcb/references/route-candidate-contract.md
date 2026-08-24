# Authoritative route-candidate transactions

A route verdict is a function of the PCB bytes and the exact prepared rule
authority. Candidate-adjacent project/rule files are output evidence; they
never grade their own candidate.

## Contents

1. Transaction boundary
2. Candidate grading
3. Native DRC provenance
4. Shared semantic checks and profiles
5. Verification and promotion

## Transaction boundary

```text
prepared r0 PCB -----> baseline.kicad_pcb --+
prepared r0 PRO/DRU -> baseline + subject ---+--> fresh grade workspace
candidate PCB -------> subject.kicad_pcb ----+      |
candidate PRO/DRU ---X                              v
                                           reports + receipt.json
                                      ACCEPTED | REJECTED | INCOMPLETE
```

One candidate attempt gets one previously absent workspace. The grader refuses
to append to or overwrite an old attempt. It copies the prepared board and the
prepared `.kicad_pro`/`.kicad_dru` under both baseline and subject basenames,
then copies only candidate PCB bytes as the subject. A prepared sibling
`fp-lib-table` may be copied for reproducible lookup; it is not rule authority.

An explicit target-board override is transaction-local, project-relative,
an independent file with one hard-link, non-symlinked, and contained beneath
the configured `project.build_dir`. An absolute path, parent traversal,
hard-link alias, or symlink-resolved escape is an input error. The old
live-board target remains a named compatibility mode; it must not be confused
with an isolated transaction.

This is the unit of rollback. A rejected, incomplete, timed-out, or late
transaction cannot replace the last accepted chain. A new attempt uses a new
workspace and a new receipt; it does not repair an old receipt in place.

## Candidate grading

```bash
python3 skills/kicad-pcb/scripts/route_candidate_workspace.py grade \
  --prepared PROJECT/06_build/route/r0.kicad_pcb \
  --candidate PROJECT/06_build/route/r7.kicad_pcb \
  --workspace PROJECT/06_build/route/grades/r7-SHA \
  --required-net I2C_SCL --required-net I2C_SDA \
  --touched-net I2C_SCL --touched-net I2C_SDA

python3 skills/kicad-pcb/scripts/route_candidate_workspace.py verify \
  PROJECT/06_build/route/grades/r7-SHA/receipt.json
```

The current compatibility-safe admission remains the established candidate
predicate:

- exact promoted-route inheritance from prepared r0;
- no newly prohibited via-in-pad use;
- no hard physical DRC type under the prepared rules;
- every declared required net connected, or explicit `N-A` when none was
  declared;
- any missing report, abnormal tool exit, or unparsable evidence is
  `INCOMPLETE`, never clean.

Run authoritative grading first. Semantic copper shadowing does not execute in
the authoritative candidate transaction because its full-board adapter exceeds
the canary resource budget. Candidate grade flags record only a pending request
in `shadow_receipt.json`; they do not execute native DRC or copper inventory in
the authoritative process. A separately budgeted canary runner may invoke those
standalone tools, but its crash, timeout or report churn cannot skip candidate
DRC, change the receipt binding, or invalidate an accepted pointer. Candidate
grading performs no shadow engineering command; it does synchronously write
one small pending request after the authoritative receipt, so that write has
ordinary output-filesystem latency. The memory-heavy adapter must use one
bounded disposable process and one reused before/after inventory; an
in-process `try/except` is not containment.

The workspace receipt binds the original prepared/candidate identities and
every authoritative local artifact. The later `shadow_receipt.json` is outside
that artifact census and binding. `ACCEPTED` is not route promotion by itself.
Content-addressed accepted bundles are currently an
explicit experimental seam, not a live-driver invariant: until their
independent regrading and import canaries are promoted, the existing driver
remains authority and must not claim that its mutable `FINAL` is such a bundle.

## Native DRC provenance

The established candidate check keeps its original invocation during the
compatibility rollout. `--shadow-native-drc` records a request only; a
separately budgeted full semantic baseline/subject dual-run must use the same
immutable prepared sidecars and
the exact native options:

```text
--severity-all --refill-zones --schematic-parity --format json
```

Those flags define the shared semantic comparison and final evidence. During
shadow rollout, do not silently change the established hard-type invocation;
preserve its exact command and run the full semantic command separately until
canaries prove equivalence.

A usable report must satisfy all of these:

1. the tool exits normally;
2. the report was produced after the invocation and is not an unchanged old
   file;
3. JSON contains the three arrays `violations`, `unconnected_items`, and
   `schematic_parity` plus generator/provenance evidence;
4. the receipt records report size and SHA-256;
5. final-mode execution fingerprints the board before and after DRC and refuses
   a changed or disappeared subject;
6. final verification reopens both the report and board identity.

Profiles mean different claims:

| Profile | Admissible claim |
|---|---|
| `wave` | Semantic non-regression against a complete baseline report |
| `pilot` | Same non-regression rule for a bounded pilot transaction |
| `final` | Absolute fresh `0 violations / 0 unconnected / 0 parity` |

A nonzero wave baseline needs semantic finding signatures, not counts alone.
Counts-only comparison can replace one defect with a different defect while
appearing unchanged and is therefore `INCOMPLETE`. Final admission cannot omit
or forge native DRC by supplying a PASS label or an empty required-check list.

## Shared semantic checks and profiles

When separately invoked, `route_acceptance_core.py` derives applicable checks
from a transaction's declared touched semantics. Candidate-grade shadow flags
do not invoke it. Depending on nets, endpoints, zones and power, the shared core
can require semantic copper delta, connectivity regression, endpoint-layer
closure, power-graph delta, native DRC, and a route objective. Missing
applicable evidence is `INCOMPLETE`.

During compatibility rollout these results do not replace established
admission:

- candidate semantic DRC pending request is
  `shadow_receipt.json:checks.native_drc_delta`;
- candidate before/after copper pending request is
  `shadow_receipt.json:checks.copper_delta`;
- a full/quick shared-composition **request** is written beside the final-route
  receipt as `*.shadow.json`; the hot path does not run shared admission, and
  the request is not a field in or verifier requirement of the authoritative
  receipt.

A separately budgeted runner writes its canary result to a distinct artifact;
it must not overwrite the pending request or join authoritative receipt
identity.

The real-board copper graph currently approximates some pad/hole connectivity.
It may expose a possible unowned mutation, lost endpoint, split power zone, or
missing declared zone, but it cannot be the sole promotion authority until
measured adapters prove those geometries. A shadow PASS never weakens a legacy
FAIL or INCOMPLETE, and a shadow rejection cannot tighten a legacy acceptance.
A disagreement preserves the previous accepted chain and opens an
investigation.

`required_nets` is authoritative connectivity coverage, not mutation
ownership. `--touched-net` and `--mutation-baseline` are stored only in the
separate shadow request; they do not change the authoritative receipt identity.
A separately budgeted copper canary must grade actual changed nets against that
scope. A pending request is not evidence, and copper delta cannot promote until
the real-board geometry/connectivity adapter passes the documented canaries.

The shared objective is a minimization vector over every observed applicable
dimension: incomplete checks, DRC/parity/open counts, undeclared/unowned
mutations, endpoint/power regressions, zone splits, and optional vias, copper
length and bends. Missing or incomparable active dimensions make the relation
`INCOMPLETE`; tradeoffs and regressions are not Pareto improvement.

## Verification and promotion

Receipt verification is relocatable: artifact paths are workspace-relative,
but every byte hash must still match. Verification fails if an artifact is
missing or changed, a path escapes the workspace, an accepted receipt contains
a nonpassing authoritative check, a native report no longer matches, or the
native subject differs from the receipt board. Every path component is checked;
an intermediate symlink is an escape even when the final path is a regular
file.

An unkeyed self-digest detects accidental edits only; it does not authenticate
the producer. Do not trust mutable verdict/check fields merely because a caller
recomputed that digest. Authoritative promotion must require the closed check
inventory, reopen exact baseline/subject/sidecars, independently rederive every
check and verdict, and receive the expected prepared-authority identity from
its caller. If any predicate cannot be reproduced, promotion is unavailable;
the experimental bundle code stays shadow-only.

### Minimal acceptance tests

| Case | Expected |
|---|---|
| Candidate sidecar relaxes USB clearance | ignored; prepared rule authority rejects |
| Prepared sidecar or tool output missing | `INCOMPLETE`, never clean |
| Workspace already exists | refuse; do not append or overwrite |
| Workspace sidecar changes after receipt | verification fails |
| Receipt verdict/check statuses are rewritten without changing artifacts | verification fails after re-derivation |
| Receipt is rebound after inventing PASS checks | promotion refuses missing/rederived authority |
| Artifact parent is a symlink outside workspace | verification refuses the escape |
| Entire accepted workspace is relocated | receipt still verifies |
| Required net remains open | `REJECTED` |
| Counts-only nonzero DRC baseline in a separately run canary | shadow semantic result `INCOMPLETE` |
| Final native report is 0/1/0 but labeled PASS | final admission rejects |
| Board changes while native DRC runs | `INCOMPLETE` |
| Separately run shadow checker passes a legacy hard violation | legacy rejection wins |
| Separately run shadow baseline is malformed or times out | shadow `INCOMPLETE`; authoritative candidate receipt remains available |
| Separately run full-board copper canary exceeds its deadline/resource budget | shadow `INCOMPLETE`; authoritative receipt remains available |

Promote one shared predicate only after focused known-bads plus USB Hub v4,
Pluto RX2 8-way v4, and USB-controlled-debug-hub canaries agree on
applicability, denominator, subject, verdict, blocker and backtrack target.
Remove its replaced legacy predicate in that same promotion change. Until
then, retain one authoritative receipt plus separate pending requests or
independently produced canary evidence. A pending request is not evidence, and
there remains exactly one execution authority.
