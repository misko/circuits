# Enclosure release stream

This directory is the immutable enclosure-release stream for this project.
It is independent of `07_releases/`, which remains the PCB hardware stream.

Each enclosure release:

- has its own semantic version and date;
- binds exactly one PCB release manifest, PCB, and assembly STEP by SHA-256;
- may advance without resealing or changing its parent PCB release;
- carries printable meshes and the verification status actually achieved;
- never implies firmware compatibility unless a separate product lock says so;
- is never edited after publication; corrections require a new enclosure
  version.

`CAD_READY`, `PRINT_VERIFIED`, and `THERMALLY_VERIFIED` are distinct states.
An enclosure release at `CAD_READY` still requires physical printing and fit
evidence before it may be promoted to `PRINT_VERIFIED`.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this release-stream contract |
| `<version>-<date>/MANIFEST.json` | machine-readable complete payload census |
| `<version>-<date>/README.md` | status, parent PCB identity, print and validation notes |
| `<version>-<date>/authorities/**` | exact immutable PCB-release subjects bound by the enclosure release |
| `<version>-<date>/cad/**` | exact authored CAD authority |
| `<version>-<date>/meshes/**` | printable STL parts only |
| `<version>-<date>/package/**` | self-contained replay package |
| `<version>-<date>/renders/**` | regenerated visual-review evidence |
| `<version>-<date>/source/**` | exact enclosure configuration |
| `<version>-<date>/tooling/**` | exact verifier implementations required to reopen release evidence |
| `<version>-<date>/verification/**` | generation, STEP, collision, and verification receipts |

## Validate

- every file except `MANIFEST.json` appears exactly once in its release
  manifest with matching size and SHA-256;
- `cad_authority` matches both the manifest payload and bound source config;
- the package identity matches the release-local ZIP;
- the parent PCB manifest/PCB/STEP hashes match the named immutable PCB
  release;
- status never exceeds the verification receipt or supplied physical
  evidence.

## Forbidden

- editing any published release payload;
- putting PCB, firmware, or fabrication releases in this stream;
- claiming `PRINT_VERIFIED` from mesh checks, renders, or coupon intent alone;
- omitting an accessory declared printable by the bound configuration.
