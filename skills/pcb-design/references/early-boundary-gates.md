# Early lifecycle boundary composition

This reference owns the composition of three prevention boundaries. It does
not own their underlying electrical, placement, routing, or JLC predicates.

## Contents

1. Shared evidence and applicability
2. S-PART-FREEZE
3. E-CLOSURE
4. P-FEASIBILITY
5. Promotion rule

## Shared evidence seam

Domain gates keep their detailed measurement JSON. The current
`scripts/pipeline_stage_evidence.py` adoption seam deliberately does not
promote those bytes:

```text
legacy domain measurement -> exact-subject typed INCOMPLETE StageResult
                          -> outputs: []
                          -> accepted bundle/pointer unchanged
```

Writing an accepted bundle and a separate stage result cannot be one atomic
filesystem transaction. Promotion therefore remains disabled until both share
one content-addressed, pointer-last commit and the domain predicates can be
independently regraded. Failed, incomplete, timed-out, stale, zero-denominator,
or even legacy-accepted measurements cannot replace the prior bundle through
this seam. The legacy driver remains execution authority until canary traces
agree.

Applicability is compiled before these compositors run. The pure compiler
consumes the capability profile plus closed fact envelopes labelled for the
architecture, integration, power, and assembly owners. It emits `APPLIES`,
`NOT_APPLICABLE`, or `INCOMPLETE` with the exact determining hashes. Missing or
nonpassing required facts are `INCOMPLETE`; file presence, prose inference,
router disclosure selection, and an authored N/A flag are not applicability
authority.

The current applicability receipt is explicitly `SHADOW`. Exact-input
recompilation proves only structural consistency: an arbitrary authority
string, self-declared PASS, and caller-supplied requirements do not authenticate
the facts. Promotion requires a closed domain-to-producer registry, reopened
accepted owner receipts bound to their canonical subjects, and a pinned
requirements registry. Until
those exist, an authoritative consumer returns `INCOMPLETE` even when the
structural compiler emits APPLIES or N/A.

## S-PART-FREEZE

Run after the complete preliminary BOM and build quantity exist, before
placement. `jlcpcb-fab/scripts/manufacturing_readiness.py --phase prelayout`
owns the predicates. Its legacy domain receipt may be `ACCEPTED`, but an
optional `S-PART-FREEZE` stage request writes only a typed `INCOMPLETE` result
with no output or accepted bundle.

It composes exact MPN/LCSC identity, one dossier per used MPN, source-value
identity, assembly disposition, quantity-expanded availability, and
procurement exposure. Public catalog evidence remains a pre-layout negative
filter; final allocation/uploader evidence is still mandatory. Do not add a
second hand-maintained part-freeze file.

The preliminary catalog probe must apply the project's named absolute stock
surplus after aggregating all references on each LCSC line (for example,
`build_quantity * per_board_qty + 200`). The receipt records required quantity,
threshold, observed surplus, and timestamp. This volatility filter neither
authorizes MOQ cash nor substitutes for the hash-bound `AVAILABLE` response.

## E-CLOSURE

Run after fresh netlist export and before schematic review or placement.
`kicad-pcb/scripts/electrical_closure.py` composes, without reimplementing:

- net-label survival;
- electrical invariants and ADR coverage;
- design/protection/switching/fault/corner models;
- converter topology, output margin, and off-control;
- pre-board component/reference census; and
- source-value identity.

Every specialist must pass. Those specialist scripts remain the sole owners
of equations and limits.

Legacy authority remains byte-for-byte compatible at this boundary: projects
without `03_src/rules/operating_states.yaml` run nine specialists, while a
project that already authored that file retains the former tenth
`operating_state_check.py` call, verdict contribution, and receipt inputs. The
new compiled-applicability shadow never removes or replaces that opt-in. It
writes only a sibling pending request and adds no extra checker invocation to
the closure hot path. If that separate request later resolves to applicable, a
missing, empty, malformed, or evidence-free contract is `INCOMPLETE`, not N-A.
A separately budgeted runner may use the generic specialist to compare authored
producer and consumer intervals and reopen every cited file at its declared
digest. Such a run proves citation bytes, not numeric values at a free-text
locator, so its diagnostic remains `SHADOW` with evidence authority
`UNVERIFIED`.

Authoritative operating-state evidence needs typed part/config/corner
extractor receipts that name a machine locator and tool identity, reopen the
owning bytes, re-extract the source/default/negotiated/startup/steady/off/fault
intervals, and compare them with the receipt. Do not hard-code a device table
inside the generic containment checker.

During migration, `shadow` records only the pending request and preserves the
legacy E-CLOSURE denominator and verdict. A separately budgeted diagnostic is
not admissible stage evidence. The present `authoritative` mode fails
`INCOMPLETE` until both producer-receipt and typed-extractor prerequisites above
exist; clean/N-A/known-bad canaries are then still required. `legacy` remains
an explicit compatibility mode, including the historical file-presence opt-in;
replacing that rule requires its own reviewed authority migration.
E-CLOSURE stage promotion is independently disabled by the shared evidence
seam and creates no accepted bundle.

## P-FEASIBILITY

Run on the exact placed board before route preparation. The existing
`placement_routability_preflight.py` compositor records a typed
`P-FEASIBILITY` shadow result. It combines physical placement, critical
inventory, route ownership, endpoint topology, layer eligibility, ordered
connector lanes, and explicit series power transitions.

```yaml
require_connector_lanes: true
connector_lanes:
  - ref: J_UP
    why: USB physical lane order
    lanes:
      - {pad: A6, net: USB_UP_P}
      - {pad: A7, net: USB_UP_N}

require_series_power_paths: true
series_power_paths:
  - id: protected_input
    why: input fuse cannot be bypassed
    transitions:
      - {kind: copper, from: J_PWR.1, to: F_IN.1}
      - {kind: component, from: F_IN.1, to: F_IN.2}
      - {kind: copper, from: F_IN.2, to: U_AGG.5}
```

`copper` endpoints must share one non-empty net. A `component` transition
must cross two different pads/nets of one footprint. Realized filled-copper
connectivity and ampacity remain post-route checks.

Switching-loop adjacency, zone ownership, and service-part reachability should
extend this compositor as domain predicates, not new lifecycle stages.

Functional-cell evidence remains shadow until it is built from independently
observed ref-to-MPN identities, real pad geometry, board obstacles, and fab
facts. The authored placement snapshot may declare intent but cannot prove its
own orientation, corridor, ground-egress, or resistance claims. Missing
independent observations make the separately budgeted shadow request
`INCOMPLETE` without changing the legacy placement-routability runtime,
receipt, verdict, or identity. The placement command writes this request beside
its authoritative legacy receipt; it does not execute the shadow compilers in
the hot path.

Receipt reopening currently proves byte freshness and a closed seven-row
shape, not that those seven predicates actually executed. Therefore the stage
result is deliberately `INCOMPLETE`, has no accepted output, and creates no
accepted bundle. Promotion requires independent predicate regrade from the
exact board, route, nets, and placement configuration.

## Promotion rule

Promote one boundary at a time only after focused known-bad tests plus USB Hub
v4, Pluto v4, and USB-controlled-debug-hub canaries show equivalent order,
applicability, denominators, blockers, and backtrack targets. Remove replaced
duplicate invocations in the same promotion change.
