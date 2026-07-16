# contract: 01_docs/

**Purpose** — everything a human must know that cannot be regenerated from
anything else. This is the most valuable folder in the project and the only
one that is unrecoverable if lost.

**Mutability** — hand-edited, except `decisions/` (append-only).

## Allowed

| File | What | Rule |
|---|---|---|
| `ARCHITECTURE.md` | the high-level concepts: power tree, net domains, stackup, ground strategy, critical geometries | prose + diagrams; the "why". Machine-readable net facts belong in `03_src/rules/nets.yaml`, not here — link to it |
| `DETAIL_DESIGN.md` | the math: ripple, compensation, ampacity, thermal, tolerance | every number that a component value depends on, with its equation |
| `CHANGELOG.md` | one entry per revision | see structure below |
| `CHECKLIST.md` | the gate a revision must pass before release | |
| `decisions/` | one file per decision | see `decisions/contracts.md` |
| `contracts.md` | this file | |

## Forbidden

- Part datasheets or PDFs → `02_parts/<MPN>/`.
- Stock, price, availability → volatile; `06_build/cache/`, never committed as truth.
- Generated renders → `06_build/renders/`. Committed images are allowed ONLY if
  hand-drawn (block diagrams) and their source is in `03_src/`.
- Decisions inline in `ARCHITECTURE.md` — link to `decisions/NNNN-*.md` instead.
  Architecture says WHAT IS; decisions say WHY IT IS.

## Structure: `ARCHITECTURE.md`

Required sections:
- `## Power tree` — every rail: source → conversion → load, with current.
  Name the nets exactly as they appear in `03_src/rules/nets.yaml`.
- `## Net domains` — the classes and what makes each one special. Link each
  to its `nets.yaml` entry. Do not restate widths here; they drift.
- `## Stackup` — layer count and what each layer is FOR.
- `## Ground strategy` — planes, splits, stitching, return-path intent.
- `## Critical geometries` — hot loops, Kelvin senses, differential pairs,
  keep-out intent. The things a router will destroy if it does not know.

## Structure: `CHANGELOG.md`

Reverse-chronological. One entry per revision:

```
## v4.10 — 2026-07-14  [tag: v4.10]
- Current-tiered netclasses + enforced ampacity floors (DRC now gates width).
- HO_A rerouted around the SW_A pour; SW_B islands bridged on B.Cu.
Released: no
```

`Released:` is `no`, or the `07_releases/` dir name. It is the only link between
a revision and a fab order.

## Validate

- every net named in `ARCHITECTURE.md` exists in `03_src/rules/nets.yaml`
- every `CHANGELOG.md` entry has a git tag that exists
- every `Released:` value that is not `no` names an existing `07_releases/` dir
- no `decisions/` content duplicated into `ARCHITECTURE.md`
- `DETAIL_DESIGN.md` numbers match the values in `03_src/` (spot-check on review)

## Repair

- Net named in prose but absent from `nets.yaml` → the prose is stale OR the
  net is undeclared. Check the netlist to decide which, then fix that one.
- Rationale found inside `ARCHITECTURE.md` → extract to a new ADR, replace
  with a link.
