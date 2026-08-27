# Enclosure release stream

This directory is the project's immutable enclosure-release stream.  It is
independent of `../07_releases/`, which remains the PCB hardware stream.

Each enclosure release:

- has an enclosure-specific semantic version and publication date;
- binds exactly one immutable PCB release manifest, PCB, and assembly STEP;
- may advance without changing or resealing its parent PCB release;
- records the least-ready installed scope as its overall status;
- carries every source, tool, mesh, receipt, and authority needed to reopen
  its claims;
- never implies firmware compatibility unless a separate product lock binds
  all three streams;
- is never edited after publication; corrections require a new enclosure
  version.

## Allowed

| Pattern | Content |
|---|---|
| `contracts.md` | this stream contract |
| `<version>-<date>/MANIFEST.json` | schema-v2 identity and complete regular-file census |
| `<version>-<date>/README.md` | achieved status, open work, printing and assembly notes |
| `<version>-<date>/authorities/pcb-release/**` | exact parent PCB manifest, PCB, and STEP |
| `<version>-<date>/authorities/enclosure-predecessor/MANIFEST.json` | optional exact predecessor identity |
| `<version>-<date>/cad/**` | exact CAD authority |
| `<version>-<date>/meshes/**` | printable meshes |
| `<version>-<date>/package/**` | optional transfer package |
| `<version>-<date>/renders/**` | visual-review evidence |
| `<version>-<date>/source/**` | release-root configuration and input contracts |
| `<version>-<date>/tooling/**` | exact release-local replay and verification tools |
| `<version>-<date>/verification/**` | governing generation, collision, and readiness evidence |

## Status and publication

Readiness is ordered:

```text
INCOMPLETE < CAD_READY < PRINT_VERIFIED < THERMALLY_VERIFIED
```

The overall status equals the least-ready declared scope. The deployed
publisher allows only an `immutable_candidate` where overall status and every
required schema-v2 scope are `INCOMPLETE`, with `order_ready=false`.
The current publisher rejects every ready status and `order_ready=true` until
it can reopen a governing schema-v2 scope receipt and independently regrade
the exact evidence. Renders, mesh topology, or coupon intent alone can never
satisfy that future state.

## Validate

Run the release-local verifier after publication:

```bash
/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure_release.py \
  projects/<project>/07_enclosure_releases/<version-date> \
  --project-root projects/<project>
```

The verifier must reopen every payload byte, PCB authority, optional
predecessor, status scope, and replay path.  Every ordinary file except
`MANIFEST.json` appears exactly once in the sorted manifest census.  Missing,
extra, symlinked, hard-linked, path-aliased, and special objects fail.

## Forbidden

- editing, merging into, or overwriting an existing enclosure release;
- writing enclosure artifacts under `07_releases/`;
- changing or resealing the PCB release because enclosure or firmware changes;
- resolving replay configuration or required tools through a live mutable
  project path (all config file bindings must resolve below the release root);
- claiming a status above the least-ready installed scope;
- publishing `INCOMPLETE` as order-ready;
- treating a render as fit, collision, assembly, or thermal proof.
