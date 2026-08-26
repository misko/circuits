# RX2 antenna adapter co-design evidence

This directory is a self-contained review snapshot for the bottom-loaded,
pre-wired RX2/reference antenna adapter candidate. It is bound to the ordered
`pluto-rx2-8way-v5` PCB release `v0.2.1-2026-08-14`; it is **not** a new PCB
or enclosure release and it is **not** an order/print package.

## Status

| Scope | Status | Meaning |
|---|---|---|
| Overall candidate | **INCOMPLETE** | Do not promote or order as a production antenna accessory. |
| Antenna-accessory verification run | COMPLETE | All declared selectors, source bindings, hostile probes, and exact STEP checks ran. |
| Candidate collision result | PASS | The conservative modeled antenna/cable envelope has no detected final-state, insertion-sweep, fastener, lid, or PCB STEP collision. |
| Existing split shell | CAD_READY | This is the subordinate shell-only result in `verification/shell-verification.json`; it does not qualify the antenna accessory. |
| Physical validation | INCOMPLETE | No real antenna fit, retention/rattle, board drop-in, all-interface mating, print, or thermal test was performed for this candidate. |

The supplied holder STL proves a flexible bottom-open U-channel clearance
concept. It does not prove the dimensions of the user's antenna. The D10.0
lower L envelope, D8.75 upper section, and D2.50 cable in this candidate are
explicitly conservative modeling assumptions.

Production still needs one authoritative antenna/cable profile (caliper
measurements or a dimensioned vendor drawing) and a physical adapter/gauge
fit test. Required dimensions are horizontal OD and shoulder length, lower
upright OD, taper/upper OD and usable length, elbow maximum envelope, attached
cable/ferrule OD and exit direction, plus any external strain-relief limit.

## Mechanical result

The complete already-wired L-shaped antenna loads vertically through one
58 x 31 mm rectangular underside relief. Its attached cable rises into a
bottom-open south U-notch; nothing is threaded through a closed bore and
nothing penetrates the PCB lid. The adapter then seats on the closed lid and
is retained by two M3 x 8 screws into reinforced bosses using the already
qualified E-Z LOK `260-M3-BR`/`260-M3-CR` family and the selected 4.25 mm
production pilot.

The transparent orange shape in `renders/bottom-load-proof.png` is the seated
target position. Gray/green axes mark the two M3 fastener stacks. The closed
assembly render leaves the screw wells visually open so the two-point pattern
is legible; the actual assembly requires both M3 x 8 screws.

## Evidence map

- `source/` contains the exact authored SCAD, enclosure config, hardened
  antenna verifier, and closed candidate-fact contract used by this run.
- `authorities/pcb-release/` carries the sealed PCB manifest, PCB source, and
  STEP subject copied byte-for-byte from PCB release `v0.2.1-2026-08-14`.
- `raw-evidence/` preserves the user-supplied holder STL and reference image
  byte-for-byte plus the machine-readable measurement/interpretation receipt.
- `meshes/printable/` contains all five candidate printable outputs: base,
  lid, 4.25 mm insert coupon, RX2 adapter, and antenna fit gauge.
- `meshes/reference-only/` contains the conservative antenna and cable witness
  meshes used for exact collision checks. They are not printable parts and
  are not measurements of the real antenna.
- `verification/antenna-clearance.json` is the overriding accessory receipt:
  overall `INCOMPLETE`, run `COMPLETE`, candidate collision `PASS`.
- `verification/` also includes every mesh/receipt subject named by the
  generation, STEP-inspection, and collision receipts; `tooling/` preserves
  the two shared Python modules snapshotted by the hardened verifier.
- `verification/shell-verification.json` is retained only as subordinate
  shell-scope evidence. Its `CAD_READY` status must never be read as an
  antenna-accessory or overall-bundle status.
- `MANIFEST.json` binds every payload by repository-relative path, byte size,
  and SHA-256 digest. It also binds the ordered PCB release manifest and STEP.

The main source README at `03_src/mechanical/README.md` documents the exact
assembly/removal sequence and reproducible commands. No generic enclosure ZIP
was minted because its schema cannot carry the accessory evidence or its
honest `INCOMPLETE` status.

The payload is self-contained as geometry and provenance evidence. Replaying
the CAD tools still requires a compatible external runtime: OpenSCAD 2021.01
(the verified `/usr/bin/openscad` was SHA-256
`ca63bba23a3186003603895e2aba8baaebfc56d4153351cdf08c06205a155865`,
8,387,456 bytes), Python, CadQuery 2.8.0, and OCP 7.9.3.1. No executable or
third-party runtime is embedded in this evidence directory.
