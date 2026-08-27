# Configuration schema v2

Schema v2 is additive. Existing schema-v1 configurations, generators, and
receipts retain their original meaning. New derived work should use
`schema: 2`, `kind: pcb-enclosure-config-v2`, and validate through
`scripts/enclosure_v2.py` before a CAD adapter runs.

The loader rejects duplicate keys, missing or unknown fields, non-normalized
identifiers, unsafe paths, symlinks, stale hashes/sizes, zero denominators, and
cross-document contradictions.

## Contents

1. [Top level](#top-level)
2. [Subject and release authority](#subject-and-release-authority)
3. [External subjects and authority](#external-subjects-and-authority)
4. [Verification scopes and installed parts](#verification-scopes-and-installed-parts)
5. [Fastener groups](#fastener-groups)
6. [Clearance cases](#clearance-cases)
7. [Extensible physical tests](#extensible-physical-tests)
8. [Commands](#commands)

## Top level

The exact fields are:

- `schema`, `kind`, `name`, and `mode`;
- `subject` and `external_subjects`;
- `verification_scopes` and `installed_parts`;
- `fastener_policy` and `fastener_groups`;
- `clearance_cases` and `physical_tests`.

Identifiers are lower-case and may use `.`, `_`, or `-` separators. Paths are
relative to an explicit root and bind ordinary files by normalized path,
lowercase SHA-256, and positive byte size.

## Subject and release authority

`subject` has exactly `release`, `release_manifest`, `pcb`, `step`,
`interface`, `mechanical_intent`, and `cad_design`.

- `pcb`, `step`, `interface`, and `mechanical_intent` are exact file bindings.
- `cad_design` exactly binds the schema-v1 `enclosure.yaml` consumed by the
  existing generator or authored-SCAD adapter. The v2 validator reopens it
  through the v1 loader, validates all of its subjects and interface, and
  requires identical config name, mode, release identifier, release manifest,
  PCB, STEP, and interface bindings. Thus commissioning and generated geometry
  cannot silently describe different boards or design bytes.
- `mode: derived` requires an exact `release_manifest` binding. The manifest
  must contain the configured PCB and STEP hashes, proving the enclosure is
  based on the named immutable PCB release.
- `mode: co_design` uses `release_manifest: null`; it cannot masquerade as a
  derived sealed-input workflow.
- The bound intent must validate as
  `pcb-enclosure-mechanical-intent-v2`, and its name must equal the config name.

An enclosure revision may bind the same unchanged PCB release manifest as an
earlier enclosure revision. It does not reseal or rewrite the PCB release.

Schema v2 wraps rather than clones the stable v1 geometry contract. Generation
continues to consume the exact bound `cad_design`; v2 supplies the additional
mechanical intent, authority, state/motion, scope, and evidence contracts.

## External subjects and authority

Every external subject has `id`, `role`, an exact `source` binding, and an
`authority` mapping with `grade`, `basis`, and `excluded_claims`.

| Grade | Meaning | Mandatory exclusions |
|---|---|---|
| `vendor_authoritative` | exact vendor-controlled geometry or dimensions | `physical_fit` |
| `measured_unit` | traceable measurement of the actual physical unit | `physical_fit` |
| `derived_measurement` | geometry derived from another bounded source | `physical_fit` |
| `conservative_candidate` | intentionally bounding candidate envelope | `exact_geometry`, `physical_fit` |
| `inspiration_only` | topology/reference only | `exact_geometry`, `clearance`, `physical_fit`, `manufacturing_dimensions` |

Installed parts may reference an external subject, but the authority grade
sets a conservative scope ceiling. Inspiration-only installed geometry caps
every affected scope at `INCOMPLETE`; derived or conservative geometry cannot
rise above `CAD_READY` without physical qualification.

## Verification scopes and installed parts

Each scope declares `id`, description, whether it is required, and dependency
scope IDs. Dependencies must exist and be acyclic. Typical scopes are `shell`,
`board_retention`, `antenna_accessory`, and `thermal`.

Every installed part declares:

- `id`;
- `role: pcb|base|lid|panel|accessory|hardware`;
- `source: {kind: subject|generated|external_subject, id: ...}`;
- one or more scopes.

Exactly one PCB, base, and lid are required. The PCB is `subject:pcb`.
Coupons, gauges, collision meshes, and render-only models are not installed
parts. Keeping them outside this census prevents them from being mistaken for
assembly collision subjects.

## Fastener groups

`fastener_policy` declares a positive axis-disjoint tolerance and
`pcb_retained_with_lid_removed: true`. Schema v2 requires that invariant; it
must agree with mechanical intent.

Each `fastener_groups` row declares `id`, role, one or more 3-D axes, retained
part IDs, and exact screw-stack minimums. V2 requires both:

- `board_retention`: retains PCB plus base, never lid;
- `case_closure`: retains base plus lid, never PCB.

Board and closure axes may not be collinear within the declared tolerance.
Accessory groups are optional; each must retain an accessory plus a structural
base or lid part. See `fasteners-and-inserts.md` for dimensional qualification.

## Clearance cases

There is exactly one clearance case per intent operation. Each case declares:

- scope and operation;
- named opening;
- moving parts and obstacle parts;
- `envelope_basis: full_part|conservative_body|cable_only`;
- `method: linear_sweep_exact|linear_sweep_envelope`;
- nonnegative minimum clearance.

Moving parts must match the operation, cannot also be obstacles, and all IDs
must be installed parts. A no-threading cabled part requires `full_part`; a
cable-only opening is a schema error, even if the final installed pose is clear.

## Extensible physical tests

`physical_tests` is an authored list, not a fixed global census. Each row has
`id`, `type`, scope, `required_for`, and subject parts. Built-in types cover
coupons, board drop-in, board-support/load-path clearance, interface mating,
thermal soak, lid-off retention, closure independence, accessory
insertion/removal, retention/rattle, and cable strain/clearance. Extensions
use `custom.<owner>.<test>` so misspelled built-ins do not silently become new
types.

Add `board_support_clearance` whenever bosses, rails, walls, panels, connector
openings, or closure posts could form an alternate PCB bearing path. The test
must show that the assembled board seats simultaneously on every intended
support and bears on no component body, solder tail, edge connector, wall,
panel, or closure post. A zero-volume CAD intersection does not establish this
load-path fact.

`required_for` is `PRINT_VERIFIED` or `THERMALLY_VERIFIED`. The evidence file
must repeat the exact configured ID/type/scope census and bind the semantic
config hash.

When lid-off PCB retention is required, the configured print tests must cover
both `lid_off_pcb_retention` and `case_closure_independence`. A prewired,
no-threading accessory also requires `accessory_insertion_removal`,
`accessory_retention_rattle`, and `cable_strain_clearance`, each covering the
affected installed part. These obligations cannot be removed merely by
omitting rows from the authored test census.

## Commands

```bash
/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-config "$PROJECT/03_src/mechanical/enclosure-v2.yaml" \
  --root "$PROJECT" \
  --output "$PROJECT/06_build/mechanical/v2-validation.json"

/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-evidence "$PROJECT/08_reviews/<physical-witness>.yaml" \
  --config "$PROJECT/03_src/mechanical/enclosure-v2.yaml" \
  --root "$PROJECT" \
  --output "$PROJECT/06_build/mechanical/physical-validation-v2.json"

/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  aggregate-config "$PROJECT/06_build/mechanical/scope-statuses.json" \
  --config "$PROJECT/03_src/mechanical/enclosure-v2.yaml" \
  --root "$PROJECT" \
  --output "$PROJECT/06_build/mechanical/scoped-verdict.json"
```

The Python helper `aggregate_status(scope_statuses, required_scopes,
ceilings=...)` returns `FAIL` if any required scope fails, `INCOMPLETE` if one
is missing/incomplete/authority-blocked, otherwise the lowest achieved
readiness. A ready shell can never hide an incomplete accessory scope.

Use `aggregate-config` for governing decisions: it derives required scopes and
authority/unknown ceilings from the validated config. The shorter `aggregate`
command accepts caller-supplied applicability and ceilings and is diagnostic
only; it must never govern verification, packaging, or publication.
