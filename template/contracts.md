# contract: board project root

**Purpose** — one fabricable board, standalone and transferable. A clone with
no network and no sibling repos must be enough to understand, regenerate, and
re-order it.

**The organizing axis** — who writes a file, and may it change:

| Folder | Written by | Mutability |
|---|---|---|
| `01_docs/` | humans | hand-edited |
| `03_src/` | humans | hand-edited — THE source of truth |
| `02_parts/` | humans (once per part) | append; edit only on datasheet revision |
| `04_kicad/` | generators | regenerated, committed for reviewable diffs |
| `05_firmware/` | humans | hand-edited |
| `06_build/` | tools | disposable, gitignored |
| `07_releases/` | release step | **IMMUTABLE once written** |

## Allowed at root

| Pattern | What |
|---|---|
| `README.md` | what the board is, status, current release, how to build |
| `contracts.md` | this file |
| `.gitignore` | must ignore `06_build/`; must NOT ignore `01_docs/decisions/` or `02_parts/` |
| `01_docs/ 03_src/ 02_parts/ 04_kicad/ 05_firmware/ 06_build/ 07_releases/` | see each folder's contract |

## Forbidden at root

- Loose design docs (`DESIGN.md`, `BOM.md` at root) — they go in `01_docs/`.
- Loose scripts — they go in `03_src/`.
- Any `*_v2`, `*_old`, `*_experiment`, `*_backup` file or folder. **Iterations
  live in git history, never in filenames.** A `board_v2.kicad_pcb` beside
  `board.kicad_pcb` is a defect: nothing says which one is real.
- Generated artifacts (PNG/PDF/netlist) — they go in `06_build/`.

## Iteration vs release — the distinction that matters

- **Revision**: any design state. Recorded as a git tag + one
  `01_docs/CHANGELOG.md` entry. Costs nothing, happens constantly.
- **Release**: a design state that was actually sent to a fab. Gets an
  immutable `07_releases/<ver>-<date>/`. Rare, permanent, checksummed.

Most revisions never become releases. A board can go v4.4 → v4.10 in a day
and ship exactly one of them.

## Validate

- no `*_old|*_v[0-9]|*_backup|*_experiment` paths anywhere in the repo
- `06_build/` is gitignored; `01_docs/decisions/` and `02_parts/` are NOT
- every folder present has a `contracts.md`
- `README.md` names the current release and it exists in `07_releases/`

## Repair

- Loose root docs → move to `01_docs/`, fix links.
- Versioned filenames → keep the newest as the canonical name, delete the
  rest (git history holds them), note it in `01_docs/CHANGELOG.md`.
- Missing `contracts.md` → copy from the template and adapt.
