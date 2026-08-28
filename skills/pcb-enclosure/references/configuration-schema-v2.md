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
7. [Connector service envelopes](#connector-service-envelopes)
8. [Extensible physical tests](#extensible-physical-tests)
9. [Commands](#commands)

## Top level

The exact fields are:

- `schema`, `kind`, `name`, and `mode`;
- `subject` and `external_subjects`;
- `verification_scopes` and `installed_parts`;
- `fastener_policy` and `fastener_groups`;
- `clearance_cases`, optional additive `service_envelopes` or the go-forward
  `interface_assemblies`, and `physical_tests`.

Already-published v2 configs may omit both connector fields and validate as a
legacy compatibility case. When an `opening` or `service_opening` exists, that omission is
reported and caps every scope in the required closure at `INCOMPLETE`; it does
not preserve legacy readiness. New enclosure work binds `interface_assemblies`
to the exact shared PCB connector receipt. Inline `service_envelopes` remain a
compatibility/migration form and cannot be combined with the shared receipt.
Whichever form is present must cover every `opening` and `service_opening`
exactly once, including top-side service access.

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
| `first_article_observation` | hash-bound physical pass/fail or relational witness without dimensional authority | `exact_geometry`, `clearance`, `physical_fit`, `manufacturing_dimensions` |
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

## Connector service envelopes

The go-forward form is:

```yaml
interface_assemblies:
  receipt: {path: 06_build/verification/connector_assembly_contract.json,
            sha256: <sha256>, size: <bytes>}
  # Empty only when every receipt instance is mapped below.
  non_enclosure_refs: []
  group_state_bindings:
    - group_id: all-external-service
      enclosure_state_ids: [installed]
  mappings:
    - id: external_usb
      assembly_id: usb_c_service
      interface_ids: [usb]
      scope: connector_access
      mated_in_states: [installed]
      mated_during_operations: [install_lid, remove_lid]
```

The receipt is compiled by the PCB-design connector contract and freshly
regraded during enclosure validation. An `assembly_id` owns the receptacle,
mate, grip, fastening, tool, torque, reaction, cable, operations, tolerances,
and simultaneous groups. The enclosure mapping adds only case-interface IDs,
scope, and enclosure state/operation membership. Unknown assemblies, stale
receipts, partial opening/service-opening coverage, ref mismatches, omitted simultaneous-group
members, absent group-to-enclosure-state bindings, a mating axis that
contradicts the declared case side, optional-scope laundering, and any extra
dimension field are errors.

`interface_assemblies` is also the exact receipt-instance census. Every
connector ref is accounted for as either a mapped case interface or a
dimensionless non-enclosure disposition:

```yaml
non_enclosure_refs:
  - ref: J17
    disposition: no_enclosure_interface
    reason: Internal factory header is intentionally inaccessible in this case.
```

The literal is closed and the reason is required; dimension fields are not
accepted. Mapped refs plus `non_enclosure_refs` must equal the complete receipt
census. If any member of a simultaneous group is mapped, every member of that
group must be mapped with the same scope/state/operation signature so all
populated obstacles remain represented. Only a wholly irrelevant group may use
non-enclosure dispositions, and then every member needs its own row. Validation
reopens the exact contract, every evidence file, and compiler after shared
regrade; drift in any authority during regrade is a hard error.

The shared receipt closes connector authority and population-census gaps, and
prevents the v2 mapping from inventing another dimension set. The bound v1 CAD
config still carries legacy `plug_envelope_mm` and `clearance_mm` candidates;
schema v2 neither derives them from the shared receipt nor treats them as
connector-service authority. The current validator also does not instantiate
or sweep complete plug/tool/cable solids against generated enclosure geometry.
Mapped scopes therefore remain `INCOMPLETE` until both the legacy projection
and governing service verifier are composed. Physical qualification remains
required. A shared-receipt config is eligible only for the current
all-`INCOMPLETE` immutable-candidate boundary when the prepared release mirrors
the exact receipt-owned contract and evidence paths beneath the fixed
`source/connector-assembly/` virtual project root, copies the exact receipt
below `verification/`, and binds the exact compiler at
`tooling/connector_assembly_contract.py` with replay-tool role
`connector_assembly_contract`. The recorded paths inside the receipt remain
unchanged: the release virtualizes filesystem resolution, not source identity.
Publication and reopen validation reject a missing or extra closure file,
compiler role/path substitution, nested binding drift, and a receipt that does
not deterministically recompile from those release-local bytes.

### Inline migration form

`service_envelopes` prevents the PCB receptacle or footprint outline from
silently standing in for the complete installed service assembly. Each row
names an edge-opening `interface_id`, one verification scope whose
`required` flag is true, and a closed census of:

- `connector_body`: the board receptacle body;
- `mated_plug`: the complete plug or overmold;
- `strain_relief`: rear boot, soldered termination, heat-shrink, or equivalent;
- `cable`: received cable outside diameter;
- `bend`: minimum radius plus the swept bend envelope;
- `installation_sweep`: the exact intent operation and modeled/physical method;
- `allowances`: separate per-side print/process and assembly allowances.

Each row also names a `simultaneous_group`, every intent state in which the
interface is mated, and every operation during which it must remain mated. The
state list must be nonempty. Every member of one simultaneous group must share
one scope and identical mated-state and mated-during-operation censuses; a
group name alone cannot claim simultaneous installation. The validator also
requires both endpoints of each such operation to be in the mated state list.
The operation must declare `cable_condition: pre_attached`,
`threading_permitted: false`, and `disconnecting_permitted: false`, so a
lid-service claim cannot silently assume disconnected or newly threaded cables.
`observation_subject` is null unless any row uses `physical_observation`; then
it must name an exact external subject graded `first_article_observation`.

The three solid rows use `{basis, envelope_mm}`. Cable uses
`{basis, diameter_mm, straight_run_mm, exit_direction}`. Bend uses
`{basis, minimum_radius_mm, swept_envelope_mm}`. This first additive slice
accepts only `conservative_candidate` for dimension-bearing rows. Vendor,
measured, and derived authority belongs in the shared connector contract;
inline rows cannot promote readiness. `physical_observation` and `unknown`
require null values: a photograph that proves interference does not become a
fabricated measurement. A dimension-bearing cable row requires all three of
diameter, nonnegative straight run, and nonzero 3-D exit vector.

The installation row uses `{basis, method, operation}`. A conservative linear
sweep names a declared intent operation; `physical_test` binds an operation
but remains physical rather than CAD evidence; `not_modeled` uses a null
operation and preserves the gap. Allowances use `{basis,
process_per_side_mm, assembly_per_side_mm}` with nonnegative 3-D vectors only
for a conservative candidate basis.

The entire represented service scope remains capped at `INCOMPLETE`, even when
every conservative candidate dimension is populated: the checklist does not
bind external geometry or execute the named sweep. A config with either form
also requires `all_interfaces_mated` and `cable_strain_clearance` physical
tests in every affected scope.

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
