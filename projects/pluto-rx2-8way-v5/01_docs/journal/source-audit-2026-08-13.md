# Pre-schematic source audit — 2026-08-13

## Boundary

This receipt grades authored requirements, rules, exact-part dossiers and dated
sourcing evidence only. It does not claim that a schematic, PCB, firmware,
fabrication package or physical article exists. No TSX or KiCad generator was
run while producing it.

## Canonical gate receipt

| Gate | Subject | Result | Warm time |
|---|---|---:|---:|
| YAML parse | all project `*.yaml` | PASS 24/24 | 0.07 s |
| E-INV-SCHEMA | `03_src/rules/electrical_invariants.yaml` | PASS 17/17 | 0.04 s |
| S-NETMERGE-SCHEMA | `label_survival` | PASS 11 rows, 0 exemptions | 0.03 s |
| CONTROL-PROTOCOL | `control_protocol.yaml` | PASS 8/8 states and 8/8 windows; marker 505 ms; cycle 2160 ms; capture 4320 ms | 0.03 s |
| RF-CONTRACT | `rf.yaml` | PASS 2 ports, 1 pending-solver cross-section, 4 claims | 0.03 s |
| A-POP projection | `assembly.yaml` | PASS; TP1-TP5 declared not assembled | 0.03 s |
| P-MOD | `integration.yaml` | PASS 1/1 | 0.07 s |
| E-TOPO | `power_tree.yaml` + TPS7A dossier | PASS 1/1; 45 mW operating estimate below 238 mW board-dependent design ceiling | 0.06 s |
| EARLY-DESIGN | protection and effective-capacitance rules | PASS 4/4 | 0.10 s |
| A-SOURCE | `nets.yaml` | PASS 6/6 classes | 0.03 s |
| P-LAYOUT / P-PREC | six hard-part dossiers | PASS 2 policy rows; precedents graded 6/6 | 0.54 s |
| Q-2SOURCE | exact candidate BOM + dated JLC/Mouser/DigiKey evidence | PASS 12/12 exact rows at two authorized pools | 0.09 s cached |
| G-ORPHAN | repository schema/reader contract | PASS 604/604 declared keys; 508 proven; 0 orphan/unread | 1.83 s |
| M-BOUND | ADR numeric-bound provenance | PASS 13/13 declared blocks; fleet floor retained | 0.69 s |
| M-STATE | `01_docs/findings.yaml` | PASS; derived `DRAFT` | 0.03 s |
| CHECKPOINT | exact source/evidence identity | PASS 50/50 files pinned and verified | 0.4 s |

The current JLC catalog evidence independently reports stock coverage PASS for
12/12 exact codes. It is a dated selection-time observation, not proof of JLC
assembly allocation on order day.

## Repair trace

```text
pre_schematic_audit()
├─ parse_all_yaml() -> PASS 24/24
├─ invoke_each_canonical_reader()
│  ├─ electrical invariants -> FAIL prose-only shape
│  ├─ RF contract -> FAIL noncanonical ports/cross-section
│  ├─ assembly projection -> ERROR scalar row traceback
│  ├─ label survival -> false PASS at 0 intended rows
│  └─ precedent ladder -> FAIL 6 unclosed ceilings
├─ run_schema_governance() -> FAIL 29 orphan v5 fields
│  ├─ remove duplicate prose homes and manual completion flags
│  ├─ remove pre-PCB sentinel floorplan/route files
│  ├─ govern assembly, control-protocol and RF schemas
│  └─ raise measured family/proven/precedent ratchets
├─ repair_source_contracts_and_generic_error_handling()
├─ qualify_exact_sources()
│  ├─ live Q-2SOURCE -> FAIL 10/13
│  ├─ remove rejected 10-V capacitor dossier
│  ├─ consolidate three capacitors on qualified 16-V code
│  ├─ record current exact DigiKey pages for connector and LDO
│  └─ Q-2SOURCE -> PASS 12/12
├─ rerun_applicable_source_battery() -> PASS
├─ derive_project_state() -> DRAFT
├─ pin_exact_source_checkpoint() -> PASS 50/50
└─ assert(no_generated_schematic_or_pcb()) -> PASS
```

## Residual holds

- Schematic, firmware, placement and routing gates remain pending.
- The provisional right-angle female SMA choice must be confirmed or revised
  before footprint freeze.
- The exact current Amphenol drawing and current ST Rev-5 data sheet must be
  captured locally at their stated future boundaries.
- PCB work remains blocked on mechanics, edge order, exact connector review and
  the official JLC impedance solution.
- First-article ordering remains blocked on final reviews, a same-day stock and
  JLC uploader population/allocation echo, and a sealed release package.
- First-article acceptance requires VNA, control timing/reset and thermal/power
  measurements; no physical evidence exists yet.

## Reflection

The correction spent more time reconciling schemas and evidence than running
checks. Once evidence was warm, the complete source battery—including the
repository-wide schema and ADR-bound ratchets—completed in under four seconds.
The reusable lesson is to make the stage boundary an executable
registry of source readers, minimum coverage and fresh receipts. It should run
before TSX, fail boundedly, and keep volatile supplier evidence separate from
stable part facts.
