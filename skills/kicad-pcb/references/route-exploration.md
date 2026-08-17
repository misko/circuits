# Bounded route exploration and experiment retention

Routing retries buy information, not permission to churn files. Two small
modules separate those concerns:

```text
attempt -> semantic observation -> NOVEL_PROGRESS -> bounded retry
                              \--> STAGNATED/BUDGET_EXHAUSTED -> backtrack

candidate + receipt -> ACCEPTED | REJECTED | INCOMPLETE manifest
                              \--> content-addressed minimal retained evidence
```

`route_progress_guard.py` signs unresolved net identities, hard-finding
classes/owners, and semantic frontier ownership. Raw coordinates and output
hashes are excluded. The default bound stops the second identical semantic
frontier, the fifth total attempt, the fourth novel signature, or an 8x
operation expansion without denominator reduction.

`route_experiment_store.py` gives each experiment exactly one terminal state.
Its accepted pointer is exclusive; a second candidate cannot silently become
canonical. Rejected/incomplete runs retain only the files named by their
manifest. `prune-dry-run` reports unreferenced objects but never deletes them.

## Minimal acceptance tests

| Case | Expected |
| --- | --- |
| Same opens/findings, different X/Y and PCB hash | STAGNATED |
| Opens reduce | NOVEL_PROGRESS |
| New finding owner/type | one bounded diagnostic attempt |
| 8x queue/rip-up growth without reduced opens | STAGNATED |
| Two experiments attempt ACCEPTED pointer | second refuses |
| Store moved to another path | manifests still verify |
| Prune report sees referenced object | object is never listed |
