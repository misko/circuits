# contract: 03_src/lib/

**Purpose** — footprints, symbols and 3D models this project OWNS. Vendored
so a clone opens correctly on a machine that has never seen your global
libraries.

**Mutability** — hand-edited, rarely.

## Allowed

| Pattern | What |
|---|---|
| `<name>.pretty/**` | KiCad footprint library owned by this project (all .kicad_mod inside) |
| `*.kicad_mod` | inside a `.pretty/` only |
| `3dmodels/*.step|3dmodels/*.wrl` | flat source-owned or provenance-pinned 3D models |
| `3dmodels/**/*.step|3dmodels/**/*.wrl` | versioned or package-grouped source-owned/provenance-pinned 3D models |
| `3dmodels/**/*.md` | model provenance and retained upstream licensing |
| `3dmodels/**/SHA256SUMS` | machine-verifiable digests for a vendored model subset and its licence |
| `contracts.md` | this file |

## Rules

- Reference these with `${KIPRJMOD}` in `fp-lib-table`, never an absolute
  path — the project must clone-and-open anywhere.
- An unmodified vendored model records its upstream repository, immutable tag
  or commit, source URL, licence and SHA-256 digest beside the files.
- Vendor a stock KiCad footprint into here ONLY if you modify it. An
  unmodified copy is drift waiting to happen; reference the stock library.
- A footprint's polarity / pin-1 marker is a FACT other tooling depends on.
  If you author or modify one, record its pad-1 convention in the
  corresponding `02_parts/<MPN>/part.yaml` (`pins:`) — generators trust that
  file over the footprint.

## Validate

- `fp-lib-table` uses `${KIPRJMOD}`, no absolute paths
- every footprint referenced by `04_kicad/<board>.kicad_pcb` resolves from
  `03_src/lib/` or a stock KiCad library — no dangling refs
- no unmodified copies of stock footprints

## Repair

- Absolute path in `fp-lib-table` → rewrite with `${KIPRJMOD}`.
- Dangling footprint ref → restore the library or repoint the footprint;
  never let the board carry a ref that does not resolve.
