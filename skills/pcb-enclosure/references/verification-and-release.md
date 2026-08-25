# Verification and candidate release

Verification is cumulative. Never promote status from intent, appearance, or an unevidenced operator claim.

## Automated boundary

`verify_enclosure.py` checks:

- exact PCB, STEP, and interface path/size/hash bindings, plus the sealed PCB
  release manifest when one is declared;
- agreement between PCB and interface hashes;
- disposition of every extracted access candidate;
- opening versus plug-envelope clearance;
- selected mounting-hole existence and insert/screw stack dimensions;
- existence, manifold topology, connectivity, nonzero volume, and degeneracy rate for every declared STL;
- STEP inspection status and collision result;
- thermal plan consistency.

The generated `verification.json` binds raw and semantic config hashes and reports denominators for every check.

## Exact STEP and collision evidence

Run `inspect_step.py` on the bound STEP and interface. Occurrence coverage fails when a footprint declaring a model is absent from the STEP, or an access candidate declares no model.

With CadQuery/OCP available, inspection identifies the PCB solid, records exact solid bounds and registration, and can export component solids as a mesh. Without that backend, geometry status is `INCOMPLETE`; do not replace it with text parsing or a guessed bounding box.

The generator always creates `assembled-case.stl` through the fixed `part="installed_case"` selector and binds the source, selector command, and artifact in `generation.json`. A print-oriented lid, exploded render, or separately supplied mesh is not valid collision geometry. Run `build_collision.py` with that generation receipt and CadQuery/OCP. It reopens the exact STEP solids, excludes the inspector-recorded PCB fabrication solids, applies the recorded registration plus the configured board-bottom Z, and writes both `clearance-intersection.stl` and a hash-bound `collision.json`. Verification reopens the generation receipt and proves the config, CAD authority, source, fixed selector command, assembled-case artifact, and collision input agree. A component export, guessed transform, or unreceipted empty STL is not collision evidence. The verifier compares the receipt's exact BRep volume with `--collision-tolerance-mm3`; choose and justify any nondefault tolerance.

Exact collision clearance does not prove cable mating, assembly sequence, compliant-part motion, tolerance stack-up, or thermal safety.

## Physical evidence

Copy `assets/physical-evidence.template.yaml` into the build directory. Replace the placeholder with the semantic SHA-256 recorded in `verification.json`. Keep all four closed-schema test rows, populate those required by `physical_validation`, and leave genuinely inapplicable rows as evidenced `NOT_RUN`. The untouched template is not evidence.

Each required test needs `status: PASS` and a nonempty `evidence` value. Use repository-relative evidence paths, measurement records, or concise photo identifiers that another reviewer can inspect. Keep failures as failures; revise the design and repeat the test rather than editing history.

- `insert_coupon`: production process installs and retains the exact insert without boss damage.
- `board_drop_in`: actual assembled PCB installs/removes in the defined sequence without force or collisions.
- `all_interfaces_mated`: actual intended plugs, controls, and service tools fit in the required simultaneous use case.
- `thermal_soak`: declared load and ambient complete without exceeding recorded limits.

Any config edit changes the semantic hash and makes prior physical evidence stale.

## Status ladder

- `FAIL`: a represented automated check or supplied physical evidence contradicts a requirement, is stale, or is invalid.
- `INCOMPLETE`: an automated prerequisite such as exact STEP geometry or collision evidence is absent.
- `CAD_READY`: every automated check passes; physical evidence may be absent and its check may therefore remain `INCOMPLETE`.
- `PRINT_VERIFIED`: CAD is ready and all required nonthermal physical tests pass with evidence.
- `THERMALLY_VERIFIED`: print verification plus required thermal evidence, or no configured soak requirement.

Use `--target cad`, `print`, or `thermal` to make the command exit nonzero below the requested level. Read both exit status and report status.

## Render and package

Render `enclosure.scad` with `render_enclosure.py`; it uses a deterministic orthographic assembly view and a virtual display when available. Inspect the image, but treat it only as review evidence.

Package with `package_enclosure.py`. The deterministic ZIP includes config, interface, bound subjects, an optional exact PCB-release manifest, the exact generated or authored SCAD, STLs, generation and verification receipts, and optional render/inspection/physical evidence. For authored SCAD, the generation receipt and package manifest carry its original path/hash/size authority, and packaging proves the copied source is byte-identical. `source/enclosure.yaml` preserves the authored paths; `replay/enclosure.yaml` rebases only those paths to packaged payloads and can be reopened with the extracted ZIP root as `--root`. The package manifest records both its exact PCB dependency and replay config identity. It always refuses `FAIL`; it accepts `INCOMPLETE` only when `--allow-incomplete` explicitly marks a draft. It also rejects generated or verified files changed after their receipts were written.

Use draft packaging only to transfer unfinished work. Label the package with its actual status and open findings. A candidate suitable for manufacture should include the achieved verification report, reproducible inputs, and all evidence required for the claimed status.
