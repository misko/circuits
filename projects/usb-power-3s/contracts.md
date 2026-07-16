# contract: board project root

**Purpose** — one fabricable board, standalone and transferable. A clone with
no network and no sibling repos must be enough to understand, regenerate, and
re-order it.

**The organizing axis** — who writes a file, and may it change:

| Folder | Written by | Mutability |
|---|---|---|
| `docs/` | humans | hand-edited |
| `src/` | humans | hand-edited — THE source of truth |
| `parts/` | humans (once per part) | append; edit only on datasheet revision |
| `kicad/` | generators | regenerated, committed for reviewable diffs |
| `firmware/` | humans | hand-edited |
| `build/` | tools | disposable, gitignored |
| `releases/` | release step | **IMMUTABLE once written** |

## Allowed at root

| Pattern | What |
|---|---|
| `README.md` | what the board is, status, current release, how to build |
| `contracts.md` | this file |
| `.gitignore` | must ignore `build/`; must NOT ignore `docs/decisions/` or `parts/` |
| `docs/ src/ parts/ kicad/ firmware/ build/ releases/` | see each folder's contract |

## Forbidden at root

- Loose design docs (`DESIGN.md`, `BOM.md` at root) — they go in `docs/`.
- Loose scripts — they go in `src/`.
- Any `*_v2`, `*_old`, `*_experiment`, `*_backup` file or folder. **Iterations
  live in git history, never in filenames.** A `board_v2.kicad_pcb` beside
  `board.kicad_pcb` is a defect: nothing says which one is real.
- Generated artifacts (PNG/PDF/netlist) — they go in `build/`.

## Iteration vs release — the distinction that matters

- **Revision**: any design state. Recorded as a git tag + one
  `docs/CHANGELOG.md` entry. Costs nothing, happens constantly.
- **Release**: a design state that was actually sent to a fab. Gets an
  immutable `releases/<ver>-<date>/`. Rare, permanent, checksummed.

Most revisions never become releases. A board can go v4.4 → v4.10 in a day
and ship exactly one of them.

## Validate

- no `*_old|*_v[0-9]|*_backup|*_experiment` paths anywhere in the repo
- `build/` is gitignored; `docs/decisions/` and `parts/` are NOT
- every folder present has a `contracts.md`
- `README.md` names the current release and it exists in `releases/`

## Repair

- Loose root docs → move to `docs/`, fix links.
- Versioned filenames → keep the newest as the canonical name, delete the
  rest (git history holds them), note it in `docs/CHANGELOG.md`.
- Missing `contracts.md` → copy from the template and adapt.
