# Verification, evidence, and publication

Verification is cumulative and scoped. Never promote status from intent,
appearance, a declaration without its geometry, or an unevidenced operator
claim.

## Contents

- [Keep the two schema layers distinct](#keep-the-two-schema-layers-distinct)
- [Schema-v1 automated boundary](#schema-v1-automated-boundary)
- [Exact STEP and final-position collision](#exact-step-and-final-position-collision)
- [Assembly motion and whole-body clearance](#assembly-motion-and-whole-body-clearance)
- [Independent fasteners](#independent-fasteners)
- [Physical evidence](#physical-evidence)
- [Scoped status](#scoped-status)
- [Candidate package and immutable release](#candidate-package-and-immutable-release)
- [Process and output safety](#process-and-output-safety)

## Keep the two schema layers distinct

The existing schema-v1 tools are the geometry adapter:

- `generate_enclosure.py` consumes the exact bound v1 CAD design;
- `verify_enclosure.py` grades its subjects, generated meshes, final installed
  collision result, and closed v1 physical-evidence census;
- `package_enclosure.py` freshly regrades that same build and creates a
  portable candidate ZIP.

Schema v2 is the commissioning and composition layer:

- `validate-intent` checks service states, linear operations, cable rules,
  unknowns, and desired release intent;
- `validate-config` reopens the exact bound v1 CAD design and requires the
  same release manifest, PCB, STEP, and interface identities. It checks
  installed parts, scopes, independent fastener declarations, clearance-case
  contracts, external authority, and physical-test obligations;
- `validate-evidence` checks the exact configured v2 physical-test census and
  semantic config hash;
- `aggregate-config` derives required scopes and authority/unknown ceilings
  from the validated config, then conservatively combines supplied scope
  results.

V2 currently does not generate CAD, infer v2 fastener axes from v1 geometry,
execute insertion sweeps, or derive individual scope results from v1 receipts.
Those results must come from the corresponding geometry, motion, and physical
verifiers. Report a scope as `INCOMPLETE` when that verifier is unavailable.

## Schema-v1 automated boundary

`verify_enclosure.py` checks:

- exact PCB, STEP, interface, and declared sealed-release-manifest bindings;
- agreement between PCB and interface hashes;
- disposition of every extracted access candidate and opening/plug clearance;
- selected mounting holes and insert/screw stack dimensions;
- generation receipt identity, declared printable-part census, closed selector
  probe, and the generated assembly contract;
- manifold topology, connectivity, nonzero volume, and degeneracy rate for
  every declared STL and the fixed installed-case mesh;
- STEP inspection, exact installed-position collision, and thermal-plan
  consistency.

The generated `verification.json` binds raw and semantic v1 config hashes and
reports a denominator for every check. `package_enclosure.py` requires the
closed seven-check census, reruns verification against current bytes, and
refuses changed generation or evidence receipts.

## Exact STEP and final-position collision

Run `inspect_step.py` on the bound STEP and interface. With CadQuery/OCP it
identifies the PCB solid, records exact solid bounds and registration, and can
export component solids for audit. Without that backend, geometry is
`INCOMPLETE`; text parsing or a guessed bounding box is not a substitute.

`generate_enclosure.py` creates `assembled-case.stl` only through the fixed
`part="installed_case"` selector and binds its source, command, artifact, part
census, and assembly contract in `generation.json`. `build_collision.py`
reopens the exact STEP BReps, excludes inspector-recorded PCB fabrication
solids, applies the recorded registration plus board-bottom Z, and binds its
intersection mesh in `collision.json`. Verification rejects a print-oriented
lid, exploded view, arbitrary case mesh, component export, stale receipt, or
unreceipted empty mesh.

The collision receipt proves only the represented final installed pose. It
does not prove cable mating, insertion/removal motion, compliant parts,
tolerance stack-up, tool access, or thermal safety.

## Assembly motion and whole-body clearance

Schema v2 requires one clearance case for each declared linear operation. A
prewired part for which threading is forbidden must use a `full_part` envelope;
`cable_only` and partial-body declarations are rejected. This proves that the
commissioned contract asks the right question, not that geometry has cleared
the opening.

To raise the affected scope to `CAD_READY`, use a reviewed project-specific
verifier to sweep the complete exact or conservative full-body solid over the
declared travel against every named obstacle, check the configured minimum
clearance, and bind the result to the config, subjects, transforms, operation,
and tool. If no such verifier exists, keep the scope `INCOMPLETE`. Record the
configured insertion/removal physical tests when performed, but they cannot
bypass a CAD prerequisite that the scope requires.

## Independent fasteners

Schema v2 requires board-retention and case-closure groups with disjoint axes.
Board retention must secure PCB plus base without the lid; closure must secure
base plus lid without retaining the PCB. It also requires print tests for
lid-off PCB retention and closure independence.

For the built-in v1 adapter, use `separate_perimeter`. Its generation receipt
records distinct board and closure roles, and v1 verification checks the
declared axis separation against boss/post radii. An authored adapter needs
equivalent geometry and evidence. Do not assign a ready board-retention scope
from v2 declarations alone.

## Physical evidence

For the v1 CAD build, copy `assets/physical-evidence.template.yaml`, replace
its semantic hash with the one in `verification.json`, retain all four rows,
and populate every test required by `physical_validation`:

- `insert_coupon` for exact insert/process retention without boss damage;
- `board_drop_in` for actual installation/removal without force or collision;
- `all_interfaces_mated` for the simultaneous real plug/control/service case;
- `thermal_soak` for the declared load and ambient limits.

For v2 composition, copy `assets/physical-evidence-v2.template.yaml` and make
its ID/type/scope census exactly match `physical_tests`. The schema adds
lid-off retention, closure independence, accessory insertion/removal,
retention/rattle, cable strain/clearance, and namespaced custom tests. Every
required test needs `PASS` plus nonempty inspectable evidence. Keep failures
and genuine `NOT_RUN` results; any semantic config edit makes old v2 evidence
stale.

## Scoped status

Use this order:

```text
INCOMPLETE < CAD_READY < PRINT_VERIFIED < THERMALLY_VERIFIED
```

`FAIL` dominates every represented result and must not publish. For each v2
required scope, produce an evidence-backed status, then write only that census:

```json
{"scope_statuses":{"shell":"CAD_READY","board_retention":"CAD_READY","antenna_accessory":"INCOMPLETE"}}
```

Run `aggregate-config` with the exact v2 config. It rejects missing or extra
required scopes, returns `FAIL` when a supplied scope fails, returns
`INCOMPLETE` when a scope is incomplete or authority/unknown-capped, and
otherwise returns the least readiness. Exit code 1 means `FAIL`, 2 means
`INCOMPLETE`, and 0 means a ready status. The diagnostic `aggregate` command
accepts caller-supplied applicability and ceilings and must not govern
packaging or publication.

## Candidate package and immutable release

`package_enclosure.py` creates a deterministic v1 candidate ZIP with bound
subjects, source, meshes, generation/collision/verification evidence, and a
release-root-portable replay config. It always refuses `FAIL` and accepts
`INCOMPLETE` only with `--allow-incomplete`; this is a draft transfer package,
not publication.

Publish independently under `07_enclosure_releases/` using
`stage_enclosure_release.py` only after preparing a stable, release-root
workspace. The stage command accepts the supplied overall and per-scope
statuses, requires the overall value to equal their least readiness, copies
the exact parent PCB authorities, writes a full census, reopens the staging
tree, and publishes with an atomic no-replace rename. Because it does not yet
consume and independently regrade a governing schema-v2 scope receipt, its
deployed policy accepts only overall `INCOMPLETE` with
`--immutable-candidate`, and every required schema-v2 scope must likewise be
declared `INCOMPLETE`. It refuses every ready status, component-ready scope,
partial scope census, and order-ready flag.

An `INCOMPLETE` publication requires `--immutable-candidate` and can never be
order-ready. Reopen every release with `verify_enclosure_release.py`;
optionally add `--project-root` to compare its local authority copies with the
current immutable PCB parent. Never write enclosure artifacts under
`07_releases/` or reseal a PCB because its enclosure changed. See
`release-stream.md` for the complete workspace and manifest contract.

## Process and output safety

Enclosure scripts delegate every external process to the repository's shared
`process_runner`/`pipeline_runtime` authority for deadlines, descendant cleanup,
and bounded output. Generated outputs are staged beside their destination and
atomically replaced after success. Symlink paths, path escapes, and output
aliases to protected inputs are rejected. Preserve this single process
authority; do not add direct `subprocess.run` or `Popen` launch paths to an
enclosure script.
