# ADR-0010 — Retire the unused shared tscircuit module registry

status: accepted
date: 2026-08-26
supersedes: ADR-0002 Phase C registry location and forward-adoption decision;
the TSX-to-native-KiCad authoring boundary remains authoritative
tags: tscircuit, modules, repository-structure, retirement

## Context

ADR-0002 Phase C created a top-level `tscircuit_modules/` experiment and one
parameterized `ShuntMonitor` module. Its local demo instantiated that module six
times and retained parity evidence against the ble-bus-bar design.

The experiment did not become shared infrastructure:

- no active or archived project TSX imported the module;
- no project package manifest depended on the registry;
- no project conductor, repository test, or CI job executed its demo or parity
  checker;
- the only code consumer was the demo inside the registry itself;
- its replay instructions predated the pinned project-local tscircuit toolchain
  and still named paths that later moved.

Keeping the directory at the repository root made it appear to be active
pipeline authority when it was actually an isolated historical proof.

## Decision

Remove `tscircuit_modules/` from the current repository tree. New PCB projects
author TSX inside their governed `03_tscircuit/` directory and use the pinned
project-local toolchain. Reusable modules may be proposed again only when a
real project adopts them and the shared package, dependency lock, replay, and
automated tests land together.

## Consequences

- ADR-0002 remains unchanged as the historical record of the experiment; this
  ADR supersedes only its Phase C shared-registry decision.
- Git history retains the exact module, generated demo, parity script, and
  evidence at parent commit `7a6c0978` under `tscircuit_modules/`.
- The normal TSX → `circuit.json` → native KiCad workflow is unchanged.
- Historical plans may continue to mention the removed experiment, but current
  skill documentation must not present it as a live library.
