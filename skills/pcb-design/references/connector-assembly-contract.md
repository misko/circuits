# Connector assembly contract

Use this procedure whenever a board connector must be mated, fastened,
unfastened, cabled, or serviced. A footprint, courtyard, bare-body model, or
clear sightline proves none of those operations.

## Contents

1. Authority and timing
2. Complete connector cell
3. Evidence grades
4. Authored schema
5. Coordinate and envelope meanings
6. Operations and simultaneous states
7. Tolerances and allowances
8. Compiler and receipt
9. PCB and enclosure consumption
10. Physical qualification

## 1. Authority and timing

The project owns one authored contract:

```text
03_src/rules/connector_assemblies.yaml
```

`pcb-design` owns its schema and compiler. Part dossiers own reusable
manufacturer facts, the PCB source owns realized placement, and enclosure
source owns case geometry. Evidence files are referenced; their dimensions are
not copied into parallel PCB and enclosure configurations.

Create connector profiles during commission and part selection. Resolve them
before placement approval and routing. A connector contract does not add a
lifecycle stage; it is a mandatory placement predicate whenever connectors are
present. If a board intentionally has no externally serviced connector, the
project may use the typed N-A branch below. Empty populations alone fail, and
the compiler's N-A is only an evidence-backed applicability decision: it is not
a PCB-geometry census, placement gate, enclosure check, or service PASS.

## 2. Complete connector cell

Each profile covers the complete operated system:

```text
fixed receptacle + supported mate + grip/coupling + fastening
  + final tool + reaction load path + termination/cable
  + operation sequence + populated neighbors + enclosure obstacles
```

Bind exact supported mating hardware. “SMA cable,” “USB plug,” or “XT60 lead”
is not an identity. Distinct plugs, overmolds, boots, tools, cables, or service
states need distinct profiles unless one evidenced conservative profile fully
contains the others.

Bare bodies clearing each other is insufficient. The relevant object is the
complete static and moving service envelope, including the hand-start region,
tool head, tool repositioning or rotational sweep, optional counter-tool,
strain relief, straight cable run, bend, and every required neighboring mate.

## 3. Evidence grades

Every connector section, operation, and tolerance carries exactly one grade:

| Grade | Meaning | Admission |
|---|---|---|
| `exact` | Exact selected hardware/process fact from cited ordinary files | May support exact checks within the cited scope |
| `conservative` | Deliberately containing bound derived from cited evidence, with its rationale | May pass while capping the receipt ceiling at `CONSERVATIVE` |
| `unknown` | The fact is represented but not known | Receipt is `INCOMPLETE`; exit 2 |

`exact` and `conservative` require at least one source ID. A conservative
envelope must state what it contains and include its declared allowances; the
compiler never inflates a number. A physical photograph may reject a fit, but
does not create a millimetre value. Render appearance is not access evidence.

Evidence sources are project-relative ordinary files. The compiler rejects
missing files, symlinks, duplicate YAML keys, undeclared or unused sources, and
unknown schema fields. Each used file is bound by SHA-256 and byte size.

Artifact roles are typed rather than inferred from a filename or prose. A
`model_source_id` accepts only `manufacturer-3d-model`, `native-3d-model`,
`measured-3d-model`, or `qualified-tool-3d-model`. A drawing may evidence an
explicit body/head envelope, but it cannot masquerade as a 3D model when that
envelope is null. An `orientation_source_id` accepts only
`placement-contract`, `connector-orientation-receipt`, or
`realized-orientation-measurement`. Other evidence kinds remain legitimate for
their stated facts; they simply cannot fill these typed roles.

## 4. Authored schema

Start from
[`templates/03_src/rules/connector_assemblies.yaml`](../templates/03_src/rules/connector_assemblies.yaml).
The exact top level is:

```yaml
schema: 1
contract_id: <stable-id>
evidence_sources:
  - {id: <id>, kind: <stable-kind>, path: <project-relative-file>}
applicability: # optional only for operated=true schema-1 compatibility
  operated: <true-or-false>
  evidence: {grade: <grade>, source_ids: [<id>], rationale: <why>}
assemblies: [<connector-profile>, ...]
simultaneous_groups: [<required-population-state>, ...]
```

Existing schema-1 contracts that omit `applicability` mean `operated: true`
and retain the non-empty rules below. The only zero-population path is explicit
`operated: false`: its evidence grade must be `exact`, it must cite at least one
ordinary project file declared with kind `connector-applicability-record`, and
its rationale must state the reviewed scope. Both `assemblies` and
`simultaneous_groups` must then be empty. Missing, stale, untyped,
conservative, or unknown evidence fails; it is never `0/0 PASS`.

For example, when the exact commissioned brief contains the reviewed connector
census:

```yaml
evidence_sources:
  - id: connector-census
    kind: connector-applicability-record
    path: 01_docs/BRIEF.md
applicability:
  operated: false
  evidence:
    grade: exact
    source_ids: [connector-census]
    rationale: The commissioned design has no connector intended for mating, fastening, cabling, or service.
assemblies: []
simultaneous_groups: []
```

`operated: false` means no connector in the reviewed design is intended to be
mated, fastened, cabled, or serviced. It does not prove that a realized PCB has
zero connector footprints. Phase one deliberately adds no PCB geometry N-A
gate or PASS; downstream census work remains independent.

Each assembly has one stable `id`, one or more board `instances`, and every
required section: `receptacle`, `mate`, `interface`, `grip`, `fastening`,
`tool`, `torque`, `reaction`, `cable`, `operations`, and `tolerances`.

An instance binds an exact ref, board-coordinate mating-axis unit vector, and
one or more simultaneous-group IDs. A known `interface` must bind that axis to
a typed `orientation_source_id` included in the interface evidence. An unknown
interface may retain an authored candidate axis for planning, but its receipt
remains `INCOMPLETE`; the vector alone is not realized-orientation evidence. A
ref belongs to exactly one profile.
Group membership is declared on both sides and must agree exactly; this makes a
misspelled or omitted neighbor a schema failure rather than a smaller test.

Use null only with `unknown` evidence, or for a field whose known method makes
it inapplicable—for example, no torque range when `required: false`. A known
tool, receptacle, or mate needs an exact model source or an evidenced body/head
envelope. A known grip needs its axial length and either diameter or flats.
Threaded or torque-required fastening needs a known non-`none` tool and a
known reaction method. Represent an unselected tool or reaction as `unknown`;
do not encode the word `unknown` as an exact method.

## 5. Coordinate and envelope meanings

`mating_axis_board` is a unit vector in board coordinates pointing outward
through the mating mouth. Envelope fields use connector-local axes:

- `x`: axial, along the positive mating axis;
- `y`: lateral across the connector bank;
- `z`: PCB-normal/vertical.

`mating_plane_offset_mm` starts at the footprint origin and follows the mating
axis. `minimum_exposure_mm` is the required installed mating-plane exposure
outside the final PCB edge. `exposure_setback_allowance_mm` is the explicit
one-sided worst-case loss of exposure from the selected tolerance stack.

A future realized-board PCB consumer must therefore grade, without an implicit
margin:

```text
nominal exposure - exposure_setback_allowance_mm >= minimum_exposure_mm
```

`minimum_service_clearance_mm` applies outside the complete declared service
envelopes. Zero is legal only when selected evidence and the required operation
justify it; the compiler supplies no default.

## 6. Operations and simultaneous states

Operations carry stable ID, unique positive sequence, closed kind, start/end
states, whether the operation is required, whether neighbors remain populated,
and evidence. Model all applicable actions, including:

- mate and unmate;
- hand-start, latch, tighten, loosen, or release;
- counter-hold or anti-rotation action through the reaction section;
- cable installation, straight run, and bend;
- enclosure installation/removal with the declared cable state;
- final service/removal.

The tool `approach` and cable `exit` are explicitly axial in schema 1:
`along_mating_axis`, `opposite_mating_axis`, or `none`. Do not encode an angled
operation as an axial one. Keep it `unknown` until a later schema represents
and checks that motion exactly.

Each simultaneous group declares its required state, all members, and the
members that must remain serviceable. Use the most demanding real state, such
as every neighboring cable connected while any one coupling nut is loosened.
Testing ports only one at a time is not evidence for an all-connected group.

Schema 1 is one linear operation graph per profile: sequences are contiguous
from 1, each end state equals the next start state, and a fully known graph has
at least one required operation. For a required `all_connected` or `all_mated`
group, every serviceable member's profile must have a required operation with
`with_neighbors_populated: true`. Operations are profile-wide; if two refs
need different service procedures, split them into distinct profiles. An
unknown operation may defer this coverage only by keeping the receipt
`INCOMPLETE`.

## 7. Tolerances and allowances

Every profile has a non-empty `tolerances` list. Each row names the exact
feature or process it affects, one closed `effect`, non-negative minus/plus
bounds, evidence, and its source. Effects are executable—not descriptive:

| Effect | Consumer meaning |
|---|---|
| `exposure_setback` | Add `max(minus_mm, plus_mm)` to the one-sided mating-plane setback stack |
| `service_radial_growth` | Add `max(minus_mm, plus_mm)` to grip/tool/cable service radii |
| `service_axial_growth` | Add `max(minus_mm, plus_mm)` to inward service reach and axial tool approach |
| `other` | Preserve a traced tolerance that makes no geometry claim in schema 1 |

Every assembly requires at least one `exposure_setback` row; `other` cannot
substitute for it. The compiler sums the worst side of every known exposure
row and rejects an `exposure_setback_allowance_mm` below that total. An unknown
row keeps the receipt `INCOMPLETE`, so its missing bound is never treated as
zero. No current PCB geometry gate is allowed to turn these rows into a
placement pass. The future PCB placement consumer and enclosure operation-solid
verifier must apply the radial and axial effects before either may advance
beyond the current `INCOMPLETE` boundary; neither may count `other` as
clearance.

Include every applicable contributor:

- receptacle drawing and installed seating;
- mating part, grip, boot, and tool;
- PCB outline, drill, placement, thickness, and mounting registration;
- board-to-enclosure registration;
- enclosure process and printed opening variation;
- cable/termination and assembly process.

Do not merge unrelated quantities into a global “connector tolerance.” Do not
reuse a radial print allowance as tool clearance. The one-sided setback and
any conservative service envelope must be derived from these selected sources,
with the derivation recorded in evidence. The compiler validates representation
and provenance only. Realized-board and enclosure arithmetic remains an
explicitly tracked implementation requirement.

## 8. Compiler and receipt

Run from the repository root:

```bash
python3 skills/pcb-design/scripts/connector_assembly_contract.py \
  --project projects/<name>
```

The default output is:

```text
06_build/verification/connector_assembly_contract.json
```

Exit/status meanings are fixed:

- exit 0 / `PASS`: non-vacuous schema with no unknown evidence;
- exit 0 / `N-A`: exact typed no-operated-connectors evidence and empty
  assembly/group populations;
- exit 2 / `INCOMPLETE`: represented unknown evidence remains;
- exit 1 / `FAIL`: schema, path, identity, or cross-reference failure.

The receipt kind is `connector-assembly-contract-receipt`, schema 1. It carries
normalized assemblies/groups, exact denominators, unknown findings, evidence
ceiling, and bindings for the contract, compiler, and every evidence file.

Hashes use canonical JSON encoded as UTF-8, keys sorted, no insignificant
whitespace, and no NaN/Infinity:

```text
semantic_sha256 = sha256(canonical({schema, contract_id,
  applicability, evidence_sources, assemblies, simultaneous_groups}))

subject_sha256 = sha256(canonical({semantic_sha256, inputs}))
```

Contract and evidence paths are project-relative. The compiler path is
repository-relative identity and is not a project artifact. Consumers import
`validate_receipt(receipt, project)`, which accepts only the canonical
`03_src/rules/connector_assemblies.yaml`, recompiles current inputs, and
requires exact deterministic receipt equality. The optional
`expected_contract_path` argument exists for explicitly non-governing fixtures
or migrations; a receipt cannot select its own authority path. Receipt
publication protects every input, including the compiler, and uses a held
no-follow directory plus dirfd-relative atomic replacement. Before returning
success, the publisher freshly recompiles the expected contract and evidence,
reopens the named output through that held directory, and requires exact
receipt-byte equality; drift removes the just-published receipt and fails.
Receipt validity is separate from readiness: a fresh `INCOMPLETE` receipt is
still not placement authority, while `N-A` is applicability only and must not
be relabeled as a geometry or service PASS.

## 9. PCB and enclosure consumption

The phase-one landing compiles the project contract in both canonical rebuild
drivers and stops on represented unknowns. It does **not** yet publish a PCB
placement-geometry PASS. A future PCB consumer must independently bind the
exact saved board, complete footprint/model identity, realized orientation,
board outline, installed Z datum, every non-connector obstacle, and each
operation state before checking exposure, neighbors, tool/cable sweeps,
tolerance growth, and reaction-load feasibility. Existing orientation review
remains separate: a connector can point correctly and still be impossible to
tighten. Until that consumer and its real producer chain land, a compiled
receipt is a fact-lock boundary, not placement authority.

An `N-A` receipt has no profiles to map. An enclosure declaring a serviced
opening cannot use it as interface authority; likewise a future exact-board
connector census must independently reject a false N-A. The compiler does not
make either downstream claim in phase one.

The enclosure owns walls, openings, fasteners, lids, and assembly sweeps. The
current schema-v2 adapter reopens the shared receipt, binds profile/ref/group
census, and caps mapped connector scopes at `INCOMPLETE` when shared evidence
is incomplete. Its bound schema-v1 CAD input still carries duplicate inline
`plug_envelope_mm` and `clearance_mm` candidates: those values are not derived
from this receipt and are not shared connector-service authority. The current
enclosure verifier also does not yet instantiate complete plug/tool/cable
solids or execute the operation graph against generated case geometry. Until
that composition lands, neither the adapter nor a bare-opening check proves
grip, tool, cable, counter-hold, or populated-neighbor access.

Changing any contract/evidence/compiler byte invalidates compilation and the
current enclosure consumer. A future PCB consumer must reopen the same exact
subject rather than trusting receipt JSON.

## 10. Physical qualification

Before routing a dense or novel bank, build a connector coupon using the exact
PCB thickness, footprint, edge registration, mates, cables, and chosen tools.
Exercise every required operation and simultaneous group. Record:

- initial engagement without cross-threading or latch damage;
- final fastening using the selected method and reaction path;
- service of every required member with neighbors populated;
- cable straight run, bend, strain relief, and enclosure state;
- PCB flex, connector rotation, solder-joint loading, and repeated cycles;
- measured exposure and process variation.

Store reusable, evidence-graded results in `docs/connector-assembly-registry.md`.
Project first-article records remain the authority for one fabricated subject.
Do not promote a registry prior into a qualified hardware combination without
the stated coupon or first-article evidence.
