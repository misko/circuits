# Early lifecycle boundary composition

This reference owns the composition of three prevention boundaries. It does
not own their underlying electrical, placement, routing, or JLC predicates.

## Shared evidence seam

Domain gates keep their detailed measurement JSON. A passing measurement may
be published through `scripts/pipeline_stage_evidence.py` as:

```text
measurement -> fresh sibling bundle -> reopen/validate -> atomic promote
            -> exact-subject StageResult
```

Failed, incomplete, timed-out, stale, or zero-denominator evidence cannot
replace the prior accepted bundle. The legacy driver remains execution
authority until canary traces agree.

## S-PART-FREEZE

Run after the complete preliminary BOM and build quantity exist, before
placement. `jlcpcb-fab/scripts/manufacturing_readiness.py --phase prelayout`
owns the predicates and optionally publishes `S-PART-FREEZE`.

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

## P-FEASIBILITY

Run on the exact placed board before route preparation. The existing
`placement_routability_preflight.py` compositor optionally publishes
`P-FEASIBILITY`. It combines physical placement, critical inventory, route
ownership, endpoint topology, layer eligibility, ordered connector lanes, and
explicit series power transitions.

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

## Promotion rule

Promote one boundary at a time only after focused known-bad tests plus USB Hub
v4, Pluto v4, and USB-controlled-debug-hub canaries show equivalent order,
applicability, denominators, blockers, and backtrack targets. Remove replaced
duplicate invocations in the same promotion change.
