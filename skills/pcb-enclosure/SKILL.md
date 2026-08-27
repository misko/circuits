---
name: pcb-enclosure
description: Commission, design, generate, review, verify, package, and independently release 3D-printable PCB enclosures from KiCad boards or immutable PCB-release STEP assemblies. Use for cases, lids, trays, connector panels, standoffs, independent PCB and case fasteners, threaded inserts, support-free FDM geometry, fit coupons, assembly-motion and prewired-part clearance contracts, interference checks, scoped readiness, and enclosure revisions tied to exact board releases.
---

# PCB Enclosure

Commission the complete assembly before drawing it. Build reproducible geometry
from exact subjects, keep each claim within its evidence, and release enclosure
revisions without modifying their parent PCB release.

## Choose the mode

- Use `co_design` while PCB placement, outline, mounting, or connector choices
  may still change. Regenerate the interface after every accepted board change.
- Use `derived` for a sealed PCB release. Bind its exact manifest, PCB, STEP,
  and interface; revise only the enclosure or explicitly select a newer parent.

Never silently move connectors, holes, or board geometry. Record proposed PCB
changes in `co_design`; reject stale subject bindings in `derived`.

## Follow the workflow

1. Read [contracts.md](contracts.md) and
   [mechanical-commission.md](references/mechanical-commission.md). Copy
   [mechanical-intent.template.yaml](assets/mechanical-intent.template.yaml),
   enumerate installed/service states, installed parts, fastener roles,
   insertion/removal operations, cable constraints, required scopes, and open
   unknowns, then run `enclosure_v2.py validate-intent` before choosing CAD.
2. Read [interface-schema.md](references/interface-schema.md), extract the
   exact PCB interface, and pass every known connector, control, fuse,
   indicator, or service item with `--access-ref` when conservative extraction
   might miss it.
3. Author the strict schema-v1 CAD design (`enclosure.yaml`). Bind PCB, STEP,
   interface, and, for `derived`, the release manifest by relative path, byte
   size, and SHA-256. This remains the exact input to the existing generator.
4. Author the schema-v2 composition around that exact v1 file. Read
   [configuration-schema-v2.md](references/configuration-schema-v2.md), bind
   the intent and external authorities, declare installed parts, verification
   scopes, independent board/case/accessory fastener groups, clearance cases,
   and physical tests, then run `enclosure_v2.py validate-config`.
5. Inspect the STEP before trusting it. Missing modeled refs or unmodeled
   access items are `FAIL`; an unavailable exact-geometry backend is
   `INCOMPLETE`.
6. Select topology with
   [enclosure-topologies.md](references/enclosure-topologies.md), author every
   interface disposition with [connector-access.md](references/connector-access.md),
   and dimension hardware using exact datasheets and coupons with
   [fasteners-and-inserts.md](references/fasteners-and-inserts.md). Schema v2
   requires distinct board-retention and case-closure groups: removing the lid
   must not loosen the PCB. With the current built-in CAD adapter, select
   `fasteners.strategy: separate_perimeter` and confirm the generation
   assembly contract; the v2 validator does not infer CAD axes from declarations.
7. Apply [fdm-printability.md](references/fdm-printability.md). Use the built-in
   engine for its supported rectangular cases or bind one reviewed authored
   SCAD entrypoint. Keep authored source outside the build directory; never
   hand-edit generated copies or STL files.
8. Generate from the exact v1 `subject.cad_design`, then verify its bindings,
   interface coverage, generation assembly contract, fasteners, mesh topology,
   exact installed-position collision, and thermal intent. All enclosure tool
   subprocesses use the repository's shared bounded process authority and
   stage outputs atomically.
9. Read [assembly-and-motion.md](references/assembly-and-motion.md). Final-pose
   collision is not an insertion sweep. For a prewired/no-threading part,
   declare a straight operation and `full_part` clearance case. Until a
   reviewed project-specific verifier executes that sweep, keep the affected
   scope `INCOMPLETE`; the v2 validator checks the contract, not the geometry.
10. Print the insert coupon before the enclosure. Record v1 shell evidence
    with [physical-evidence.template.yaml](assets/physical-evidence.template.yaml)
    and v2 scoped evidence with
    [physical-evidence-v2.template.yaml](assets/physical-evidence-v2.template.yaml).
    Validate the exact v2 census with `validate-evidence`. For a first article
    or enclosure redesign, apply
    [first-article-iteration.md](references/first-article-iteration.md),
    including an explicit board-support/load-path check where case features
    can approach PCB components or edges.
11. Produce one evidence-backed status per required scope and run
    `aggregate-config`; it derives applicability and authority/unknown ceilings
    from the validated v2 config. Never use diagnostic `aggregate` for a
    governing decision. Package only the v1 status actually achieved.
12. Read [release-stream.md](references/release-stream.md). Publish a prepared,
    release-root-replayable **INCOMPLETE immutable candidate** beneath
    `07_enclosure_releases/`, then reopen it with
    `verify_enclosure_release.py`. The current publisher deliberately refuses
    `CAD_READY` and higher until it can consume and independently regrade a
    governing schema-v2 scope receipt. Never write enclosure artifacts to or
    reseal `07_releases/`.

The built-in v1 OpenSCAD engine supports one axis-aligned rectangular PCB
outline. It fails closed on cutouts, rounded/nonrectangular contours, or
multiple outline islands. Such boards require a reviewed, hash-bound authored
SCAD adapter.

## Run the core tools

Use `/usr/bin/python3` on a KiCad host and inspect each script's `--help` before
first use. Keep authored inputs outside the build directory and generated
artifacts inside it.

```bash
SKILL_DIR=skills/pcb-enclosure

/usr/bin/python3 "$SKILL_DIR/scripts/enclosure_v2.py" \
  validate-intent "$INTENT"

/usr/bin/python3 "$SKILL_DIR/scripts/extract_board_interface.py" \
  "$PCB" -o "$BUILD/board-interface.json" --access-ref J1 --access-ref SW1

/usr/bin/python3 "$SKILL_DIR/scripts/enclosure_v2.py" \
  validate-config "$V2_CONFIG" --root "$SUBJECT_ROOT" \
  --output "$BUILD/v2-validation.json"

/usr/bin/python3 "$SKILL_DIR/scripts/inspect_step.py" \
  "$STEP" --interface "$BUILD/board-interface.json" \
  --output "$BUILD/step-inspection.json" \
  --component-mesh "$BUILD/components.stl"

/usr/bin/python3 "$SKILL_DIR/scripts/generate_enclosure.py" \
  "$CAD_CONFIG" --root "$SUBJECT_ROOT" --build-dir "$BUILD"

# Use the CadQuery/OCP Python environment used for STEP inspection.
"$CADQUERY_PYTHON" "$SKILL_DIR/scripts/build_collision.py" \
  --step "$STEP" --step-inspection "$BUILD/step-inspection.json" \
  --component-mesh "$BUILD/components.stl" \
  --generation "$BUILD/generation.json" \
  --assembled-case-mesh "$BUILD/assembled-case.stl" \
  --board-bottom-z-mm "$BOARD_BOTTOM_Z_MM" \
  --output "$BUILD/clearance-intersection.stl" \
  --report "$BUILD/collision.json"

/usr/bin/python3 "$SKILL_DIR/scripts/render_enclosure.py" \
  "$BUILD/enclosure.scad" --output "$BUILD/assembly.png"

/usr/bin/python3 "$SKILL_DIR/scripts/verify_enclosure.py" \
  "$CAD_CONFIG" --root "$SUBJECT_ROOT" --build-dir "$BUILD" \
  --step-inspection "$BUILD/step-inspection.json" \
  --collision-mesh "$BUILD/clearance-intersection.stl" \
  --collision-report "$BUILD/collision.json" \
  --physical-evidence "$BUILD/physical-evidence.yaml" \
  --report "$BUILD/verification.json" --target cad

/usr/bin/python3 "$SKILL_DIR/scripts/enclosure_v2.py" \
  aggregate-config "$BUILD/scope-statuses.json" \
  --config "$V2_CONFIG" --root "$SUBJECT_ROOT" \
  --output "$BUILD/scoped-verdict.json"

/usr/bin/python3 "$SKILL_DIR/scripts/package_enclosure.py" \
  "$CAD_CONFIG" --root "$SUBJECT_ROOT" --build-dir "$BUILD" \
  --output "$BUILD/enclosure-candidate.zip"
```

`generate_enclosure.py` exports `assembled-case.stl` only through the fixed
`part="installed_case"` selector and binds the source, command, mesh, declared
part census, and assembly contract in `generation.json`. `build_collision.py`
reopens the exact STEP BReps and accepts only that receipted installed case.
Do not substitute a print-oriented lid, exploded view, component export,
arbitrary mesh, or unreceipted empty STL.

`package_enclosure.py` regrades the current build and creates a portable v1
replay config. It refuses `FAIL`, and requires `--allow-incomplete` for a
clearly labeled draft. Immutable publication is a separate operation governed
by `stage_enclosure_release.py` and the rules in `release-stream.md`. Its
current deployment boundary is INCOMPLETE immutable candidates only; a ready
or order-ready enclosure must remain unpublished until governing scoped
regrade is implemented.

## Interpret status without inflation

- `FAIL`: represented automated or physical evidence contradicts a requirement,
  is stale, or is invalid. Do not publish it.
- `INCOMPLETE`: a required automated result, authority, operation proof, or
  scope result is absent.
- `CAD_READY`: all automated evidence required by that scope passes.
- `PRINT_VERIFIED`: `CAD_READY` plus all configured nonthermal physical tests.
- `THERMALLY_VERIFIED`: `PRINT_VERIFIED` plus required thermal evidence, or no
  configured thermal requirement.

The schema-v1 verifier grades the CAD design as a whole. Schema v2 composes
separate required scopes and lowers each by bound authority and open-unknown
ceilings. `aggregate-config` consumes scope results produced by their actual
verifiers; it does not manufacture motion, fit, or thermal evidence.

## Load references selectively

- Read [mechanical-commission.md](references/mechanical-commission.md) before
  topology or CAD work.
- Read [interface-schema.md](references/interface-schema.md) for the v1 CAD
  adapter contract and [configuration-schema-v2.md](references/configuration-schema-v2.md)
  for the commissioned composition.
- Read [enclosure-topologies.md](references/enclosure-topologies.md),
  [connector-access.md](references/connector-access.md),
  [fasteners-and-inserts.md](references/fasteners-and-inserts.md), and
  [fdm-printability.md](references/fdm-printability.md) while designing.
- Read [assembly-and-motion.md](references/assembly-and-motion.md) for service
  states, whole-body sweeps, and prewired parts.
- Read [first-article-iteration.md](references/first-article-iteration.md) when
  incorporating physical fit feedback or revising a printed enclosure.
- Read [verification-and-release.md](references/verification-and-release.md)
  for evidence and status, then [release-stream.md](references/release-stream.md)
  for independent immutable publication.

Use the sanitized runnable canaries in repository-root
`examples/pcb-enclosure-split-shell-v1/` and
`examples/pcb-enclosure-edge-panel-v1/` to learn the v1 adapter. Their
dimensions are examples, never defaults for a real board.
