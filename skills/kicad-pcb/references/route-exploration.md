# Bounded route exploration and experiment retention

Routing retries buy information, not permission to churn geometry. Separate
candidate admission, progress, and retention so a new file or coordinate does
not reset the budget.

## Contents

1. Semantic progress state
2. Pareto stop-loss
3. Typed backtrack
4. Experiment retention
5. Acceptance and promotion tests

## Semantic progress state

```text
candidate transaction -> authoritative/shadow checks -> observation
                                                        |
                       +--------------------------------+
                       v
  COMPLETE | NOVEL_PROGRESS | CONTINUE_DIAGNOSTIC
             STAGNATED | BUDGET_EXHAUSTED
```

`route_progress_guard.py` signs exactly three semantic frontier dimensions:

- unresolved net identities;
- hard-finding types and owners;
- semantic frontier ownership.

Raw coordinates, output hashes, UUIDs and numeric coordinate drift are
excluded. The state is scoped to a stable subject identity such as prepared-r0
hash plus wave. A different subject starts a different state; renaming a file
does not.

Defaults stop on the first applicable condition:

| Bound | Default |
|---|---:|
| Same semantic signature | second consecutive observation |
| Total attempts | fifth attempt |
| Novel semantic signatures | fourth signature exceeds the budget of three |
| Operation expansion | queued or ripped work reaches 8x requested work without fewer opens |

Reducing the unresolved denominator or discovering a new semantic owner/type
can buy one bounded diagnostic attempt. Coordinate-only variation cannot.
An empty unresolved/hard-finding set is `COMPLETE`.

## Pareto stop-loss

When a transaction supplies shared acceptance checks or an explicit objective,
compare the complete minimization vector rather than only open-net count. The
known dimensions include incomplete checks, DRC/parity/opens,
undeclared/unowned mutations, endpoint and power regressions, power-zone
splits, and optional via/length/bend cost.

```text
all active axes <= previous and at least one < previous -> IMPROVEMENT
some better and some worse                          -> TRADEOFF
all equal                                           -> EQUIVALENT
any worse and none better                           -> REGRESSION
missing/incomparable active evidence                 -> INCOMPLETE
```

The first objective is compared with itself so an empty, incomplete or
nonnumeric vector cannot seed a baseline and buy an extra attempt. After a
baseline exists, two consecutive non-improving comparisons stop exploration.
Only `IMPROVEMENT` resets that counter. A tradeoff is a design decision, not
automatic progress.

Use this guard after grading each immutable candidate and before launching the
next router attempt. Never run it only after an expensive retry has already
started.

## Typed backtrack

A stop result contains one `route-backtrack-recommendation-v1`. It maps the
observed finding class to an owning boundary and action:

| Finding class | Backtrack action |
|---|---|
| Missing/stale/vacuous DRC or check evidence | regenerate evidence; do not mutate copper |
| Unowned or undeclared mutation | restore copper or declare route ownership |
| Wrong/unknown endpoint layer | repair endpoint escape |
| Lost/split power zone or endpoint | repair power fill/topology |
| Requested-net open | rip only owned requested nets and reroute from the last receipt |
| Rule/sidecar authority | restore prepared rule authority |
| Clearance/short/no corridor/placement | backtrack placement |
| Final nonzero DRC or Pareto regression/tradeoff | revert the transaction |

Do not translate a typed evidence backtrack into “try routing again.” Retry the
same candidate only when the recommendation explicitly marks evidence
regeneration as safe.

## Experiment retention

`route_experiment_store.py` gives every experiment exactly one terminal state:
`ACCEPTED`, `REJECTED`, or `INCOMPLETE`. Its accepted pointer is exclusive; a
second candidate cannot silently become canonical. Retained manifests name
the minimal content-addressed evidence for rejected/incomplete attempts.
`prune-dry-run` may list unreferenced objects but never deletes them.

Preserve the last accepted chain and the compact semantic state. Do not retain
unbounded duplicate board images, router logs, or context transcripts merely
because an attempt ran. The receipt, typed findings, objective and referenced
artifacts are the resumable evidence.

## Acceptance and promotion tests

| Case | Expected |
|---|---|
| Same opens/findings with different X/Y and PCB hash | `STAGNATED` |
| Opens reduce with no other regression | `NOVEL_PROGRESS` |
| One new finding owner/type | one bounded diagnostic attempt |
| Incomplete first objective | immediate stop; no baseline seeded |
| Two equivalent/tradeoff/regressing objective comparisons | `STAGNATED` plus typed backtrack |
| 8x queue/rip-up growth without fewer opens | `STAGNATED` |
| Fifth attempt or fourth novel signature | `BUDGET_EXHAUSTED` |
| Two experiments attempt the accepted pointer | second refuses |
| Store moves to another path | manifests still verify |
| Prune report sees referenced object | object is never listed |

Before changing default limits or promoting a new objective dimension, replay
USB Hub v4, Pluto RX2 8-way v4 and USB-controlled-debug-hub route histories.
Compare stop location, denominator, accepted pointer, and typed backtrack with
the existing trace. Never “fix” a canary by allowing more attempts without a
new semantic measurement.
