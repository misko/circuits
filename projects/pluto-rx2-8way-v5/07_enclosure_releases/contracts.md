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
