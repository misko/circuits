# PCB project structure

The `pcb-design` commissioner owns creation of this tree. This reference
explains the KiCad-side separation of human source, generated current state,
disposable evidence, and immutable release history.

```text
projects/<name>/
├── README.md                 navigation only
├── contracts.md              project membership and mutability
├── 01_docs/                  brief, decisions, status, journal, reviews
├── 02_parts/                 exact part dossiers and archived data
├── 03_src/                   human PCB config, rules, promoted route
├── 03_tscircuit/             human TSX plus pinned generated schematic input
├── 04_kicad/                 generated current KiCad snapshot
├── 05_firmware/              empty unless explicitly requested
├── 06_build/                 disposable caches, candidates, receipts
├── 07_releases/              immutable PCB release stream
├── 07_enclosure_releases/    optional independent enclosure stream
└── 08_reviews/               independent mutable-state reviews
```

Every present folder is governed by its nearest `contracts.md`. The
commissioner copies project-independent templates from `pcb-design`; never copy
a sibling board.

## Authority by folder

| Folder | Authority and mutability |
|---|---|
| `01_docs/` | Human commission/decision history. Prompt/directive log is append-only; STATUS is the mutable live beacon. |
| `02_parts/` | Human-maintained exact identities and authoritative facts; volatile stock belongs in build evidence. |
| `03_src/` | Human KiCad-side design source: placement, rule declarations, route config, promoted route chain. |
| `03_tscircuit/` | Human TSX source and pinned producer inputs. |
| `04_kicad/` | Generated, committed current snapshot. Never edit as source; regenerate for reviewable diffs. |
| `06_build/` | Disposable, ignored workspaces and receipts. Nothing uniquely authoritative may live only here. |
| `07_releases/` | Immutable reviewed PCB candidate archives. A release may remain not order-ready. |
| `07_enclosure_releases/` | Immutable mechanical versions binding an exact PCB release; no PCB reseal. |
| `08_reviews/` | Independent reviews bound to exact mutable subjects; adopted copies enter release evidence at seal. |

## Source and generated state

If `03_src`/`03_tscircuit` disagree with `04_kicad`, generated KiCad is stale.
Fix source and rerun. Routing experiments occur in transaction-local build
workspaces; only an independently accepted chain is promoted under
`03_src/route/` and replayed into `04_kicad`.

Do not keep `*_old`, `*_v2`, backup, or experiment siblings. Git preserves
iterations; one canonical current artifact prevents ambiguous writers and
release inputs.

## Build and release distinction

Generated current state and immutable release history solve different
problems:

- `04_kicad` makes generator changes visible in ordinary Git review.
- `06_build` isolates disposable candidates and expensive evidence.
- `07_releases/<version-date>` freezes one complete reviewed candidate with
  exact source, fabrication, verification, human documents, and manifest.

Sealing a release does not mean it was ordered or passed first article.
Ordering and physical acceptance add separate evidence; neither rewrites the
release.

## Validation

Use the project's own contracts and the repository audit:

```bash
python3 scripts/contracts_audit.py --walk --root projects/<name>
```

Then run the project conductor and owning gates. Directory shape alone proves
only governance coverage; it says nothing about electrical correctness,
freshness, review, orderability, or physical success.
