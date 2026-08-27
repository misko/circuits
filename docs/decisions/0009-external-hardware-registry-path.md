# ADR-0009 — Name the foreign-device fact registry `external_hardware`

status: accepted
date: 2026-08-26
supersedes: ADR-0005 path name only; its provenance grades and single-home
semantics remain authoritative
tags: external-facts, mechanical, mating, repository-structure

## Context

ADR-0005 established one shared, machine-checked home for facts about hardware
this repository did not design. It used the top-level name `spf/`, an acronym
whose meaning was not apparent to readers and which was easily mistaken for a
project, generated cache, or disposable migration folder.

The registry is neither disposable nor project-specific. The active Pluto
eight-way board consumes its measured SMA gender and port ordering plus the
cited AD936x RX absolute maximum through `03_src/rules/mates.yaml`. Removing
the registry would make those inputs unverifiable.

## Decision

Foreign-device fact records live at:

```text
external_hardware/<device>/
  README.md
  facts.yaml
  ...optional evidence...
```

`external_hardware/README.md` explains the boundary. The provenance checker
uses `<repo>/external_hardware` by default and exposes the explicit override
`--external-hardware-root`. It does not silently fall back to `spf/`.

Boards continue to name only the device and fact IDs. They do not embed the
registry path or restate values. This changes discoverability, not the
M-IMPORT/D-MATE evidence model.

## Consequences

- Repository navigation, forward templates, checker documentation, and tests
  use the descriptive name.
- ADR-0005 remains unchanged as the accepted historical record. This ADR
  supersedes only its directory-name examples.
- Commissioned project contracts, reviews, archived projects, and sealed
  releases may retain `spf/` wording as historical bytes. They do not create a
  second live authority; the current checker resolves their device IDs against
  `external_hardware/`.
- New device records require an explicit row in
  `external_hardware/contracts.md`.
