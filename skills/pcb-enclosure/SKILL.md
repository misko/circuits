---
name: pcb-enclosure
description: Design, generate, review, verify, and package 3D-printable PCB enclosures from KiCad boards or immutable PCB-release STEP assemblies. Use for cases, lids, trays, connector panels, standoffs, threaded inserts, support-free FDM geometry, fit coupons, interference checks, and enclosure revisions tied to exact board releases.
---

# PCB Enclosure

Build a reproducible mechanical design from an exact PCB/interface snapshot. Keep CAD readiness distinct from printed fit and thermal evidence.

## Choose the mode

- Use `co_design` while PCB placement, outline, mounting, or connector choices may still change. Feed mechanical findings back to the PCB workflow and regenerate the interface after every accepted board change.
- Use `derived` for a sealed PCB release. Treat PCB and assembly STEP files as immutable inputs; revise only the enclosure or select a newer release explicitly.

Do not silently move connectors, holes, or board geometry in either mode. Record proposed PCB changes in `co_design`; fail a stale subject binding in `derived`.

## Follow the workflow

1. Read [contracts.md](contracts.md). Locate the PCB, assembly STEP, output root, printer process, hardware datasheet, and intended cable/load cases.
2. Read [interface-schema.md](references/interface-schema.md), then extract the exact board interface. Pass every known connector, control, fuse, indicator, or service item with `--access-ref` if conservative extraction might miss it.
3. Bind the PCB, STEP, and generated interface by relative path, byte size, and SHA-256 in `enclosure.yaml`. For `derived` work from a sealed PCB release, also bind that release's manifest; the release label alone is not identity. Never copy hashes from another release.
4. Inspect the STEP before trusting it. Missing modeled refs or unmodeled access items are `FAIL`; an unavailable exact-geometry backend is `INCOMPLETE`.
5. Select a topology using [enclosure-topologies.md](references/enclosure-topologies.md). Author every interface disposition using [connector-access.md](references/connector-access.md).
6. Dimension inserts and screws from the exact part datasheet and printer coupon using [fasteners-and-inserts.md](references/fasteners-and-inserts.md). Treat all dimensional checks as validation dimensions, not formal design-policy gate IDs.
7. Apply the support and orientation rules in [fdm-printability.md](references/fdm-printability.md). Use the built-in engine for declarative cases, or bind one reviewed authored-SCAD entrypoint as described in [interface-schema.md](references/interface-schema.md). Authored entrypoints may declare safe project-specific printable selectors for accessories and fit coupons; unknown selectors must emit no mesh or reject evaluation, and generation probes that closed contract. Custom-part exports receive deterministic STL facet canonicalization plus the same generation, mesh, receipt, and package checks as the shell. Keep authored source outside the build directory and never hand-edit generated copies or STL files.
8. Verify subject bindings, interface coverage, fasteners, mesh topology, exact-solid clearance, and thermal intent. Render and visually inspect the assembly, but never use a render as fit evidence.
9. Print the insert coupon before the enclosure. Record required physical tests from [physical-evidence.template.yaml](assets/physical-evidence.template.yaml), following [verification-and-release.md](references/verification-and-release.md).
10. Package only the status actually achieved. Use `--allow-incomplete` only for an explicitly labeled draft, never to imply readiness.

The built-in v1 OpenSCAD engine intentionally supports one axis-aligned rectangular PCB outline. It fails closed on cutouts, rounded/nonrectangular contours, or multiple outline islands instead of silently replacing them with a bounding box. Such boards need a reviewed, hash-bound authored-SCAD adapter before this workflow can generate them.

## Run the tools

Use `/usr/bin/python3` on a KiCad host. Run each script with `--help` before first use. Keep authored inputs outside the build directory and generated artifacts inside it.

```bash
SKILL_DIR=skills/pcb-enclosure

/usr/bin/python3 "$SKILL_DIR/scripts/extract_board_interface.py" \
  "$PCB" -o "$BUILD/board-interface.json" \
  --access-ref J1 --access-ref SW1

/usr/bin/python3 "$SKILL_DIR/scripts/inspect_step.py" \
  "$STEP" --interface "$BUILD/board-interface.json" \
  --output "$BUILD/step-inspection.json" \
  --component-mesh "$BUILD/components.stl"

/usr/bin/python3 "$SKILL_DIR/scripts/generate_enclosure.py" \
  "$CONFIG" --root "$SUBJECT_ROOT" --build-dir "$BUILD"

# Run this with the CadQuery/OCP Python environment used for STEP inspection.
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
  "$CONFIG" --root "$SUBJECT_ROOT" --build-dir "$BUILD" \
  --step-inspection "$BUILD/step-inspection.json" \
  --collision-mesh "$BUILD/clearance-intersection.stl" \
  --collision-report "$BUILD/collision.json" \
  --physical-evidence "$BUILD/physical-evidence.yaml" \
  --report "$BUILD/verification.json" --target cad

/usr/bin/python3 "$SKILL_DIR/scripts/package_enclosure.py" \
  "$CONFIG" --root "$SUBJECT_ROOT" --build-dir "$BUILD" \
  --output "$BUILD/enclosure-candidate.zip"
```

`generate_enclosure.py` always invokes the fixed `part="installed_case"` selector and records the resulting `assembled-case.stl`, exact source, and command in `generation.json`. `components.stl` is a tessellated audit export derived from the exact STEP solids. `build_collision.py` refuses any assembled case not proven by that generation receipt, reopens the exact STEP BReps, applies the recorded registration plus `board_bottom_z_mm`, and binds its intersection mesh in `collision.json`; do not pass a print-oriented lid, exploded view, arbitrary case mesh, component export, or unreceipted empty mesh.

The package contains both the original authored config and
`replay/enclosure.yaml`, whose paths are rebased to included payloads. After
extraction, use the package root as `--root` with the replay config; it is the
portable regeneration entrypoint, while the original config preserves source
provenance.

## Interpret status without inflation

- `FAIL`: an automated design check or supplied physical evidence contradicts a requirement, is stale, or is invalid. Fix it before proceeding.
- `INCOMPLETE`: required automated evidence is unavailable or missing. State exactly what is absent.
- `CAD_READY`: all automated checks pass, including complete STEP inspection and empty exact-solid collision result.
- `PRINT_VERIFIED`: `CAD_READY` plus evidenced required coupon, board drop-in, and interface-mating tests.
- `THERMALLY_VERIFIED`: `PRINT_VERIFIED` plus an evidenced required thermal soak, or a configuration that does not require one.

Requesting `--target print` or `--target thermal` makes the verifier return nonzero until that evidence exists. Missing physical evidence may remain `INCOMPLETE` while the overall result is legitimately `CAD_READY`; supplied stale, invalid, or contradictory physical evidence forces `FAIL`.

## Load references selectively

- Read [interface-schema.md](references/interface-schema.md) when extracting or authoring `enclosure.yaml`.
- Read [enclosure-topologies.md](references/enclosure-topologies.md) when selecting shell construction or printable parts.
- Read [connector-access.md](references/connector-access.md) for openings, plugs, service access, and interface dispositions.
- Read [fasteners-and-inserts.md](references/fasteners-and-inserts.md) for insert pockets, bosses, screws, and coupons.
- Read [fdm-printability.md](references/fdm-printability.md) for support policy, orientation, walls, bridges, vents, and tolerances.
- Read [verification-and-release.md](references/verification-and-release.md) for collision evidence, physical testing, statuses, and packaging.

Use the sanitized, runnable canaries at repository-root `examples/pcb-enclosure-split-shell-v1/` and `examples/pcb-enclosure-edge-panel-v1/` when learning the schemas or forward-testing changes. Their dimensions are examples, not defaults for a real board.
